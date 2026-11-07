import os
from dotenv import load_dotenv
from web3 import Web3
from contract import CONTRACT_ABI
load_dotenv()

w3 = Web3(Web3.HTTPProvider(os.environ["SEPOLIA_RPC_URL"]))
contract = w3.eth.contract(
    address=Web3.to_checksum_address(os.environ["CONTRACT_ADDRESS"]),
    abi = CONTRACT_ABI
)

start_block = int(os.environ["START_BLOCK"])
latest_block = w3.eth.block_number
CHUNK=10

for from_block in range(start_block, latest_block + 1, CHUNK):
    to_block = min(from_block + CHUNK -1, latest_block)
    events = contract.events.MessageUpdated().get_logs(
        from_block=from_block,
        to_block=to_block
    )
    for event in events:
        print(
            "block", event["blockNumber"],
            "|", event["args"]["editor"],
            "|", event["args"]["newMessage"],
            "| tx", event["transactionHash"].to_0x_hex()
        )