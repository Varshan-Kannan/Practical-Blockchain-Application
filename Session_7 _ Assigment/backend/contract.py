"""ABI of the MessageBoard contract (same as Remix > Compile > ABI)."""
import json

CONTRACT_ABI = json.loads('''
[
  {
    "anonymous": false,
    "inputs": [
      {
        "indexed": true,
        "internalType": "address",
        "name": "editor",
        "type": "address"
      },
      {
        "indexed": false,
        "internalType": "string",
        "name": "newMessage",
        "type": "string"
      }
    ],
    "name": "MessageUpdated",
    "type": "event"
  },
  {
    "inputs": [],
    "name": "getMessage",
    "outputs": [
      {
        "internalType": "string",
        "name": "",
        "type": "string"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "string",
        "name": "newMessage",
        "type": "string"
      }
    ],
    "name": "setMessage",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  }
]
''')
