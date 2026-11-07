
import json
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from eth_account import Account
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from web3 import Web3
from web3.exceptions import TimeExhausted, TransactionNotFound

from contract import CONTRACT_ABI

# --- Requirement: key loaded from environment configuration only ----------
load_dotenv()
missing = [v for v in ("SEPOLIA_RPC_URL", "PRIVATE_KEY", "CONTRACT_ADDRESS") if not os.environ.get(v)]
if missing:
    raise RuntimeError(f"Missing in backend/.env: {', '.join(missing)}")

w3 = Web3(Web3.HTTPProvider(os.environ["SEPOLIA_RPC_URL"]))
account = Account.from_key(os.environ["PRIVATE_KEY"])  # never printed or logged
contract = w3.eth.contract(
    address=Web3.to_checksum_address(os.environ["CONTRACT_ADDRESS"]),
    abi=CONTRACT_ABI,
)
CHAIN_ID = w3.eth.chain_id
RECEIPT_TIMEOUT = int(os.environ.get("RECEIPT_TIMEOUT", "120"))
AUDIT_FILE = Path(__file__).with_name("audit_log.jsonl")

print("Service account:", account.address)  # public address only
print("Contract:", contract.address, "| chain ID:", CHAIN_ID)

app = FastAPI(title="Custodial Transaction Service")


class MessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=280)


# --- Requirement: audit record includes request, nonce, hash, outcome ------
audit_lock = threading.Lock()


def write_audit(record: dict) -> None:
    record["logged_at"] = datetime.now(timezone.utc).isoformat()
    with audit_lock, AUDIT_FILE.open("a") as f:
        f.write(json.dumps(record) + "\n")


def clean_error(error: Exception) -> str:
    """Short error text; never contains key material (we never put the key in it)."""
    return f"{type(error).__name__}: {error}"[:300]


# --- Requirement: nonce handling accounts for concurrent requests ----------
nonce_lock = threading.Lock()
next_nonce: int | None = None


def reserve_nonce() -> int:
    """Called while holding nonce_lock. Uses the higher of our counter and the node's pending count."""
    global next_nonce
    chain_pending = w3.eth.get_transaction_count(account.address, "pending")
    nonce = chain_pending if next_nonce is None else max(next_nonce, chain_pending)
    next_nonce = nonce + 1
    return nonce


def release_nonce(nonce: int) -> None:
    """If a send failed before reaching the mempool, let the next request reuse that nonce."""
    global next_nonce
    if next_nonce == nonce + 1:
        next_nonce = nonce


# --- 1/2. Read and encode --------------------------------------------------
@app.get("/status")
def get_status():
    return {
        "service_account": account.address,
        "balance_eth": str(Web3.from_wei(w3.eth.get_balance(account.address), "ether")),
        "chain_id": CHAIN_ID,
        "contract_address": contract.address,
        "current_message": contract.functions.getMessage().call(),
    }


@app.post("/encode")
def encode_call(request: MessageRequest):
    call_data = contract.encode_abi("setMessage", args=[request.message])
    return {
        "to": contract.address,
        "data": call_data,
        "selector": call_data[:10],
        "selector_from_signature": Web3.keccak(text="setMessage(string)")[:4].to_0x_hex(),
    }


def build_transaction(message: str, nonce: int) -> dict:
    tx = {
        "from": account.address,
        "to": contract.address,
        "data": contract.encode_abi("setMessage", args=[message]),
        "value": 0,
        "chainId": CHAIN_ID,
        "nonce": nonce,
    }
    try:
        tx["gas"] = int(w3.eth.estimate_gas(tx) * 1.2)
    except Exception as error:
        raise HTTPException(400, {"outcome": "simulation_failed", "error": clean_error(error)})
    priority_fee = w3.eth.max_priority_fee
    base_fee = w3.eth.get_block("latest")["baseFeePerGas"]
    tx["maxPriorityFeePerGas"] = priority_fee
    tx["maxFeePerGas"] = 2 * base_fee + priority_fee
    return tx


@app.post("/prepare")
def prepare_transaction(request: MessageRequest):
    """Preview only: shows the unsigned tx; does not reserve a nonce."""
    nonce = w3.eth.get_transaction_count(account.address, "pending")
    return build_transaction(request.message, nonce)


# --- 3. Sign and submit ----------------------------------------------------
@app.post("/send")
def send_transaction(request: MessageRequest):
    request_id = str(uuid.uuid4())
    audit = {"request_id": request_id, "action": "setMessage", "request": {"message": request.message},
             "from": account.address, "to": contract.address, "chain_id": CHAIN_ID,
             "nonce": None, "tx_hash": None}

    # Reserve nonce, build, sign and broadcast under one lock so two requests never share a nonce.
    with nonce_lock:
        nonce = reserve_nonce()
        audit["nonce"] = nonce
        try:
            tx = build_transaction(request.message, nonce)
            signed = account.sign_transaction(tx)
            tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction).to_0x_hex()
        except HTTPException as error:
            release_nonce(nonce)
            write_audit({**audit, "outcome": "simulation_failed", "error": error.detail["error"]})
            raise HTTPException(400, {**error.detail, "request_id": request_id, "nonce": nonce})
        except Exception as error:
            release_nonce(nonce)
            write_audit({**audit, "outcome": "rejected_by_node", "error": clean_error(error)})
            raise HTTPException(502, {"outcome": "rejected_by_node", "request_id": request_id,
                                      "nonce": nonce, "error": clean_error(error)})
    audit["tx_hash"] = tx_hash
    print(f"Submitted nonce={nonce} hash={tx_hash}")

    # --- 4. Confirmation tracking (outside the lock so other requests can proceed)
    try:
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=RECEIPT_TIMEOUT)
    except TimeExhausted:
        result = {**audit, "outcome": "timeout",
                  "error": f"No receipt after {RECEIPT_TIMEOUT}s; tx may still confirm. Check GET /tx/{tx_hash}"}
        write_audit(result)
        raise HTTPException(504, result)

    outcome = "confirmed" if receipt["status"] == 1 else "reverted"
    result = {**audit, "outcome": outcome, "block_number": receipt["blockNumber"],
              "gas_used": receipt["gasUsed"],
              "explorer": f"https://sepolia.etherscan.io/tx/{tx_hash}"}
    write_audit(result)
    if outcome == "reverted":
        raise HTTPException(422, result)
    return result


@app.get("/tx/{tx_hash}")
def track_transaction(tx_hash: str):
    """Confirmation tracking: pending / confirmed / reverted, with confirmation count."""
    try:
        receipt = w3.eth.get_transaction_receipt(tx_hash)
    except TransactionNotFound:
        try:
            w3.eth.get_transaction(tx_hash)
            return {"tx_hash": tx_hash, "outcome": "pending", "confirmations": 0}
        except TransactionNotFound:
            raise HTTPException(404, {"tx_hash": tx_hash, "outcome": "not_found"})
    confirmations = w3.eth.block_number - receipt["blockNumber"] + 1
    return {"tx_hash": tx_hash, "outcome": "confirmed" if receipt["status"] == 1 else "reverted",
            "block_number": receipt["blockNumber"], "confirmations": confirmations,
            "gas_used": receipt["gasUsed"]}


@app.get("/audit")
def read_audit(limit: int = 20):
    if not AUDIT_FILE.exists():
        return []
    lines = AUDIT_FILE.read_text().splitlines()[-limit:]
    return [json.loads(line) for line in lines]
