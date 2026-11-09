import os

from dotenv import load_dotenv
from eth_account import Account
from web3 import Web3

load_dotenv()

w3 = Web3(
    Web3.HTTPProvider(
        os.environ["SEPOLIA_RPC_URL"]
    )
)

account = Account.from_key(
    os.environ["PRIVATE_KEY"]
)

recipient = Web3.to_checksum_address(
    os.environ["RECIPIENT_ADDRESS"]
)

chain_id = w3.eth.chain_id

nonce = w3.eth.get_transaction_count(
    account.address,
    "pending"
)

priority_fee = w3.eth.max_priority_fee

base_fee = w3.eth.get_block(
    "latest"
)["baseFeePerGas"]

tx = {
    "to": recipient,
    "value": Web3.to_wei(0.001, "ether"),
    "nonce": nonce,
    "chainId": chain_id,
    "gas": 21000,
    "maxFeePerGas": 2 * base_fee + priority_fee,
    "maxPriorityFeePerGas": priority_fee
}

signed = account.sign_transaction(tx)

print(
    "\nSigned raw transaction:\n",
    signed.raw_transaction.to_0x_hex()
)

tx_hash = w3.eth.send_raw_transaction(
    signed.raw_transaction
)

print("Transaction Broadcasted")


receipt = w3.eth.wait_for_transaction_receipt(
    tx_hash
)

print("Receipt:", receipt)