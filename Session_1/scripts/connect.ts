import "dotenv/config";
import { JsonRpcProvider } from "ethers";

const provider = new JsonRpcProvider(process.env.SEPOLIA_RPC_URL);

console.log(await provider.getBlockNumber());
console.log(await provider.getNetwork());