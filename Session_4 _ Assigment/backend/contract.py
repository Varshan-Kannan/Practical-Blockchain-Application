CONTRACT_ABI = [
    {
        "name": "getMessage",
        "type": "function",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "string"}],
    },
    {
        "name": "setMessage",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [{"name": "newMessage", "type": "string"}],
        "outputs": [],
    },
    {
        "name": "MessageUpdated",
        "type": "event",
        "anonymous": False,
        "inputs": [
            {"name": "editor", "type": "address", "indexed": True},
            {"name": "newMessage", "type": "string", "indexed": False},
        ],
    },
]