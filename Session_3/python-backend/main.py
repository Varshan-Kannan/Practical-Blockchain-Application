import os
from dotenv import load_dotenv
from web3 import Web3
from fastapi import  FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time

from contract import CONTRACT_ABI

load_dotenv()

w3 = Web3(Web3.HTTPProvider(os.environ["SEPOLIA_RPC_URL"]))

contract = w3.eth.contract(
    address=Web3.to_checksum_address(os.environ["CONTRACT_ADDRESS"]),
    abi=CONTRACT_ABI
)

app = FastAPI(title="Message Board API")

# allow the Next.js page (localhost:3000) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class StatusResponse(BaseModel):
    chain_id: int
    latest_block: int

class MessageResponse(BaseModel):
    message: str

class BalanceResponse(BaseModel):
    address: str
    balance: str

@app.get("/status", response_model=StatusResponse)
def get_status():
    try:
        return {"chain_id": w3.eth.chain_id, "latest_block": w3.eth.block_number}
    except Exception as error:
        print("Node error:", error)
        raise HTTPException(status_code=503, detail="Could not reach the blockchain node")

CACHE_SECOND=15
cache = {"message": None, "saved_at": 0.0}

def read_message() -> str:
    age = time.time() - cache["saved_at"]
    if cache["message"] is not None and age < CACHE_SECOND:
        print(f"cache hit ({age:.0f}s old)")
        return cache["message"]

    print("Calling the node")
    message = contract.functions.getMessage().call()
    cache["message"] = message
    cache["saved_at"] = time.time()
    return message

@app.get("/message", response_model=MessageResponse)
def get_message():
    try:
        return {"message": read_message()}
    except Exception as error:
        print("Node error:", error)
        raise HTTPException(status_code=503, detail="Could not reach the blockchain node")

@app.get("/balance/{address}", response_model=BalanceResponse)
def get_balance(address: str):
    if not Web3.is_address(address):
        raise HTTPException(status_code=400, detail="Not a valid address")
    checksum = w3.to_checksum_address(address)
    try:
        wei = w3.eth.get_balance(checksum)
    except Exception as error:
        print("Node error:", error)
        raise HTTPException(status_code=503, detail="Could not reach the blockchain node")
    return {"address": checksum, "balance": str(wei)}
