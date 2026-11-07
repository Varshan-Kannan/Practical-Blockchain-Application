"use client"
import { contractABI } from "@/lib/contract";
import { BrowserProvider, Contract } from "ethers";
import { useEffect, useState } from "react";

// the 4 states a transaction can be in
type TxStatus = "idle" | "pending" | "confirmed" | "failed";

// these must match the response models in python-backend/main.py
type StatusResponse = {
  chain_id: number;
  latest_block: number;
};

type MessageResponse = {
  message: string;
};

type BalanceResponse = {
  address: string;
  balance: string;
};

const API_URL = "http://localhost:8000";

const SEPOLIA_CHAIN_ID = "11155111";

export default function Home() {
  const [address, setAddress] = useState("");
  const [chainId, setChainId] = useState("");
  const [error, setError] = useState("");

  const [message, setMessage] = useState("");
  const [newMessage, setNewMessage] = useState("");

  const [txStatus, setTxStatus] = useState<TxStatus>("idle");
  const [txHash, setTxHash] = useState("");
  const [txError, setTxError] = useState("");

  // data from the python backend
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [backendMessage, setBackendMessage] = useState<MessageResponse | null>(null);
  const [balance, setBalance] = useState<BalanceResponse | null>(null);
  const [backendError, setBackendError] = useState("");

  const contractAddress = process.env.NEXT_PUBLIC_CONTRACT_ADDRESS || "";

  function getEthereum() {
    return (window as any).ethereum;
  }

  async function connectWallet() {
    setError("");

    try {
      const ethereum = getEthereum();
      if (!ethereum) {
        throw new Error("No wallet found. Please install MetaMask to use this page.");
      }

      // this opens the MetaMask popup and asks the user to approve
      const accounts = await ethereum.request({
        method: "eth_requestAccounts"
      });

      setAddress(accounts[0] ?? "");

      const provider = new BrowserProvider(ethereum);
      const network = await provider.getNetwork();
      setChainId(network.chainId.toString());

      // read the message as soon as we are connected
      if (network.chainId.toString() === SEPOLIA_CHAIN_ID) {
        await getMessage();
      }
    } catch (err: any) {
      if (err.code === 4001) {
        setError("You rejected the connection request in MetaMask.");
      } else {
        setError(err.message || "Connection failed");
      }
    }
  }

  // read call - no gas, no popup
  async function getMessage() {
    setError("");

    try {
      const provider = new BrowserProvider(getEthereum());
      const contract = new Contract(
        contractAddress,
        contractABI,
        provider
      );

      const currentMessage = await contract.getMessage();
      setMessage(currentMessage);
    } catch (err: any) {
      console.log(err);
      setError("Could not read the message. Make sure MetaMask is on Sepolia.");
    }
  }

  // write transaction - needs a signer and the user has to approve it
  async function updateMessage() {
    setTxStatus("pending");
    setTxHash("");
    setTxError("");

    try {
      const provider = new BrowserProvider(getEthereum());
      const signer = await provider.getSigner();

      const contract = new Contract(
        contractAddress,
        contractABI,
        signer
      );

      const tx = await contract.setMessage(newMessage);
      console.log("Tx submitted", tx.hash);
      setTxHash(tx.hash);

      // don't show success until the transaction is actually in a block
      const receipt = await tx.wait();
      console.log("Receipt", receipt);

      setTxStatus("confirmed");
      setNewMessage("");
      await getMessage();
    } catch (err: any) {
      console.log(err);
      setTxStatus("failed");

      if (err.code === "ACTION_REJECTED") {
        setTxError("You rejected the transaction in MetaMask. You can try again.");
      } else {
        setTxError(err.shortMessage || err.message || "Transaction failed");
      }
    }
  }

  // call our python API instead of the blockchain directly
  async function loadFromBackend() {
    setBackendError("");

    try {
      const statusRes = await fetch(API_URL + "/status");
      if (!statusRes.ok) {
        throw new Error((await statusRes.json()).detail);
      }
      setStatus(await statusRes.json());

      const messageRes = await fetch(API_URL + "/message");
      if (!messageRes.ok) {
        throw new Error((await messageRes.json()).detail);
      }
      setBackendMessage(await messageRes.json());

      if (address) {
        const balanceRes = await fetch(API_URL + "/balance/" + address);
        if (!balanceRes.ok) {
          throw new Error((await balanceRes.json()).detail);
        }
        setBalance(await balanceRes.json());
      }
    } catch (err: any) {
      // fetch itself fails when the backend is not running
      if (err.message === "Failed to fetch") {
        setBackendError("Backend is not running");
      } else {
        setBackendError(err.message || "Backend request failed");
      }
    }
  }

  // listen for account and network changes from MetaMask
  useEffect(() => {
    const ethereum = getEthereum();
    if (!ethereum) {
      return;
    }

    // if the user already connected before, show it without asking again
    ethereum.request({ method: "eth_accounts" }).then((accounts: string[]) => {
      if (accounts.length > 0) {
        setAddress(accounts[0] ?? "");
      }
    });
    ethereum.request({ method: "eth_chainId" }).then((id: string) => {
      setChainId(parseInt(id, 16).toString());
    });

    function handleAccountsChanged(accounts: string[]) {
      setAddress(accounts[0] ?? "");
      setTxStatus("idle");
      setTxHash("");
      setTxError("");
    }

    function handleChainChanged(newChainId: string) {
      // MetaMask gives the chain id in hex, e.g. 0xaa36a7
      setChainId(parseInt(newChainId, 16).toString());
      setMessage("");
      setTxStatus("idle");
      setTxHash("");
      setTxError("");
    }

    ethereum.on("accountsChanged", handleAccountsChanged);
    ethereum.on("chainChanged", handleChainChanged);

    // clean up the listeners when the page is closed
    return () => {
      ethereum.removeListener("accountsChanged", handleAccountsChanged);
      ethereum.removeListener("chainChanged", handleChainChanged);
    };
  }, []);

  // read the message again whenever the network changes back to Sepolia
  useEffect(() => {
    if (address && chainId === SEPOLIA_CHAIN_ID) {
      getMessage();
    }
  }, [address, chainId]);

  const wrongNetwork = chainId !== "" && chainId !== SEPOLIA_CHAIN_ID;

  return (
    <main style={{ padding: 24, display: "flex", flexDirection: "column", gap: 10, maxWidth: 600 }}>
      <h1 style={{ fontSize: 24, fontWeight: "bold" }}>Message Board</h1>

      <button onClick={connectWallet} style={buttonStyle}>
        {address ? "Connected" : "Connect Wallet"}
      </button>
      <p>Address: {address || "Wallet not connected"}</p>
      <p>Chain Id: {chainId || "Unknown"}</p>

      {wrongNetwork && (
        <p style={{ color: "orange" }}>
          Wrong network. Please switch MetaMask to Sepolia.
        </p>
      )}

      {error && <p style={{ color: "red" }}>{error}</p>}

      <hr />

      <button onClick={getMessage} disabled={!address || wrongNetwork} style={buttonStyle}>
        Get Message from Contract
      </button>
      <p>Contract message: {message || "-"}</p>

      <hr />

      <input
        type="text"
        placeholder="Type a new message"
        value={newMessage}
        onChange={(e) => setNewMessage(e.target.value)}
        style={{ padding: 8, border: "1px solid gray", borderRadius: 4 }}
      />

      <button
        onClick={updateMessage}
        disabled={!address || wrongNetwork || !newMessage || txStatus === "pending"}
        style={buttonStyle}
      >
        {txStatus === "pending" ? "Updating..." : "Update Message"}
      </button>

      {/* show which state the transaction is in */}
      <p>Status: {txStatus}</p>

      {txStatus === "pending" && !txHash && <p>Please confirm the transaction in MetaMask...</p>}
      {txStatus === "pending" && txHash && <p>Waiting for the transaction to be confirmed...</p>}
      {txStatus === "confirmed" && <p style={{ color: "green" }}>Message updated!</p>}
      {txStatus === "failed" && <p style={{ color: "red" }}>{txError}</p>}

      {txHash && <p style={{ wordBreak: "break-all" }}>Tx hash: {txHash}</p>}

      <hr />

      <h2 style={{ fontSize: 20, fontWeight: "bold" }}>Data from Python Backend</h2>

      <button onClick={loadFromBackend} style={buttonStyle}>
        Load from Backend
      </button>

      {backendError && <p style={{ color: "red" }}>{backendError}</p>}
      {status && <p>Chain Id: {status.chain_id} | Latest block: {status.latest_block}</p>}
      {backendMessage && <p>Message: {backendMessage.message}</p>}
      {balance && <p>Balance (wei): {balance.balance}</p>}
    </main>
  );
}

const buttonStyle = {
  padding: "8px 16px",
  border: "1px solid gray",
  borderRadius: 4,
  cursor: "pointer",
  width: "fit-content"
};
