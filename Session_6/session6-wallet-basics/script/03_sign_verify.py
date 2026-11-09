from eth_account import Account
from eth_account.messages import encode_defunct

account = Account.create()
message = "I approve this request"

signed = account.sign_message(encode_defunct(text=message))
print("Signer address: ", account.address)
print("Signature: ", signed.signature.to_0x_hex())

recovered = Account.recover_message(encode_defunct(text=message), signature=signed.signature)
print("Recoverd: ", recovered)