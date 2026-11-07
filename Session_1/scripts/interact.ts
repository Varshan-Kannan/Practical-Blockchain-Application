import "dotenv/config";
import { ethers } from "ethers";

const abi = [
  {
    "inputs": [
      {
        "internalType": "uint256",
        "name": "num",
        "type": "uint256"
      }
    ],
    "name": "store",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "retrieve",
    "outputs": [
      {
        "internalType": "uint256",
        "name": "",
        "type": "uint256"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  }
]

async function main() {
    const provider = new ethers.JsonRpcProvider(process.env.SEPOLIA_RPC_URL);
    
    const wallet = new ethers.Wallet(process.env.DEPLOYER_PRIVATE_KEY || "",provider);

    console.log("Wallet", wallet.address);

    const storage = new ethers.Contract(
        process.env.CONTRACT_ADDRESS || "",
        abi,
        wallet
    )

    const amount = await storage.retrieve();
    console.log(amount)

    const tx = await storage.store("25");
    const receipt = await tx.wait()
    console.log("Receipt", receipt)

    const updatedAmount = await storage.retrieve();
    console.log(updatedAmount)
}

main()