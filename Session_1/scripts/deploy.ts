import "dotenv/config";
import { ethers } from "ethers";
import solc from "solc";
import fs from "fs";

// compile Storage.sol using solc and get the abi + bytecode
function compileContract() {
    const source = fs.readFileSync("../contracts/Storage.sol", "utf8");

    const input = {
        language: "Solidity",
        sources: {
            "Storage.sol": { content: source }
        },
        settings: {
            outputSelection: {
                "*": {
                    "*": ["abi", "evm.bytecode"]
                }
            }
        }
    };

    const output = JSON.parse(solc.compile(JSON.stringify(input)));

    // if there are any compile errors, show them and stop
    if (output.errors) {
        for (const err of output.errors) {
            console.log(err.formattedMessage);
        }
        const hasError = output.errors.some((e: any) => e.severity === "error");
        if (hasError) {
            throw new Error("Compilation failed");
        }
    }

    const contract = output.contracts["Storage.sol"]["Storage"];

    return {
        abi: contract.abi,
        bytecode: contract.evm.bytecode.object
    };
}

async function main() {
    // 1. connect using values from .env
    const provider = new ethers.JsonRpcProvider(process.env.SEPOLIA_RPC_URL);

    const wallet = new ethers.Wallet(process.env.DEPLOYER_PRIVATE_KEY || "", provider);

    const network = await provider.getNetwork();
    console.log("Network", network.name, network.chainId);
    console.log("Wallet", wallet.address);

    const balance = await provider.getBalance(wallet.address);
    console.log("Balance", ethers.formatEther(balance), "ETH");

    // 2. compile and deploy the contract
    const { abi, bytecode } = compileContract();
    console.log("Contract compiled");

    const factory = new ethers.ContractFactory(abi, bytecode, wallet);
    const deployed = await factory.deploy();

    console.log("Deploying... tx hash", deployed.deploymentTransaction()?.hash);
    await deployed.waitForDeployment();

    const contractAddress = await deployed.getAddress();
    console.log("Contract deployed at", contractAddress);

    const storage = new ethers.Contract(contractAddress, abi, wallet);

    // 3. read the initial value (call - no gas)
    const initialValue = await storage.retrieve();
    console.log("Initial value", initialValue);

    // 4. send a transaction to change the value and wait for it
    const tx = await storage.store(25);
    console.log("Transaction sent, hash", tx.hash);

    const receipt = await tx.wait();
    console.log("Transaction confirmed in block", receipt.blockNumber);

    // 5. read the value again to check it changed
    const updatedValue = await storage.retrieve();
    console.log("Updated value", updatedValue);

    console.log("\nAdd this to your .env to use with interact.ts:");
    console.log("CONTRACT_ADDRESS=" + contractAddress);
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
