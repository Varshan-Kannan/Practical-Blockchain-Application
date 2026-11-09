from eth_account import Account

Account.enable_unaudited_hdwallet_features()

_, phrase = Account.create_with_mnemonic()
print("Seed Phrase: ", phrase)

for i in range(3):
    path = f"m/44'/60'/0/0/{i}"
    account = Account.from_mnemonic(phrase, account_path = path)
    print(f"Account {i + 1} ({path}):", account.address)

rebuild_account = Account.from_mnemonic(phrase, account_path = "m/44'/60'/0/0/0")
print("Rebuild Account 1:", rebuild_account.address)