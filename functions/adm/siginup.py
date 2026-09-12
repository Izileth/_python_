
import json
import os

# Dataset

ARCHIVE = "database_adm.json"

if os.path.exists(ARCHIVE):
    with open(ARCHIVE, "r", encoding="utf-8") as archive:
        users = json.load(archive)
else:
    users = {}    


# Criação do dicionário

user = input("Create a user:")
password = input("Create a password:")

users[user] = password

# Datase Insert

with open(ARCHIVE, "w", encoding="utf-8") as archive:
    json.dump(users, archive, indent=4)

print("User created!")

