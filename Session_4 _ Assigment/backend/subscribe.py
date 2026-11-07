import os
import asyncio

from dotenv import load_dotenv
from web3 import AsyncWeb3, WebSocketProvider

from contract import CONTRACT_ABI

load_dotenv()

async def main():
    async with AsyncWeb3(WebSocketProvider(os.environ["SEPOLIA_WSS_URL"])) as w3:
        contract = w3.eth.contract(
            address= AsyncWeb3.to_checksum_address(os.environ["CONTRACT_ADDRESS"]),
            abi=CONTRACT_ABI                                         
        )
        event_topic = contract.events.MessageUpdated.topic

        subscription = await w3.eth.subscribe(
            "logs",
            {
                "address": contract.address,
                "topics": [event_topic]
            }
        )

        print("Listening... subscription id", subscription)

        async for payload in w3.socket.process_subscriptions():
            event = contract.events.MessageUpdated().process_log(payload["result"])
            print("new Message:", event["args"]["newMessage"], "from", event["args"]["editor"])

asyncio.run(main())
