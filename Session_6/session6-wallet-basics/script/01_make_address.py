from eth_account import Account
from eth_keys import keys

first = Account.create()
second = Account.create()

print("Private key", first.key.to_0x_hex())
print("Public key", keys.PrivateKey(first.key).public_key.to_hex())
print("Address", first.address)

print("Same key again", Account.from_key(first.key).address)

print("Another key", second.address)