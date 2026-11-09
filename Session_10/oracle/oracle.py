import json
import os
import time
import requests
from dotenv import load_dotenv
from eth_account import Account
from web3 import  Web3

load_dotenv()
from contract import CONTRACT_ABI

w3 = Web3(Web3.HTTPProvider(os.environ["SEPOLIA_RPC_URL"]))
account = Account.from_key(os.environ["PRIVATE_KEY"])
contract = w3.eth.contract(address=os.environ["CONTRACT_ADDRESS"], abi= CONTRACT_ABI)

COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd"
COINBASE_URL = "https://api.coinbase.com/v2/prices/ETH-USD/spot"

MIN_USD = 100
MAX_USD = 100_00
DECIMALS = 8
INTERVAL = 20
CHANGE_PERCENT = 0.1
HEARTBEAT = 60

def get_json(url):
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    return response.json()

def fetch_price() -> int:
    coingecko = float(get_json(COINGECKO_URL)["ethereum"]["usd"])
    coinbase = float(get_json(COINBASE_URL)["data"]["amount"])

    print(f" CoinGecko ${coingecko:,.2f} | Coinbase ${coinbase:,.2f}")
    for price in (coingecko, coinbase):
        if not MIN_USD <= price <= MAX_USD:
            raise ValueError(f"Price outside allowed range: {price}")

    average = (coingecko + coinbase) / 2
    return round(average * 10**DECIMALS)

def submit_value(value: int) -> str:
    tx = contract.functions.update(value).build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address, "pending"),
    })
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    if receipt["status"] != 1:
        raise RuntimeError(f"Transaction failed: {tx_hash.to_0x_hex()}")
    return tx_hash.to_0x_hex()

def should_update(new_price: int) -> bool:
    stored = contract.functions.value().call()
    updated_at = contract.functions.updatedAt().call()
    age = w3.eth.get_block("latest")["timestamp"] - updated_at  # chain time, not the laptop's clock
    if age >= HEARTBEAT:
        return True
    return abs(new_price - stored) * 100 >= stored * CHANGE_PERCENT

while True:
    try:
        price = fetch_price()
        dollars = f"${price / 10**DECIMALS:,.2f}"
        if should_update(price):
            print(f"✅ {dollars} → submitted {submit_value(price)}")
        else:
            print(f"⏸  {dollars} → moved less than {CHANGE_PERCENT}%, skipped")
    except Exception as error:
        print(f"❌ nothing submitted: {type(error).__name__}: {error}")
    time.sleep(INTERVAL)