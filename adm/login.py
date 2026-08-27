
import json
import os

ARCHIVE = "database@2.json"

# Carrega os dados
if os.path.exists(ARCHIVE):
    with open(ARCHIVE, "r", encoding="utf-8") as archive:
        users = json.load(archive)
else:
    users = {}
    
changes = 2

while changes > 0:

    user = input("Usuário: ")
    password = input("Senha: ")

    if user in users and users[user] == password:
        print("Bem vindo!")
        break

    else:
        changes -= 1

        print("Usuário ou senha incorretos")
        print(f"Tentativas restantes: {changes}")

if changes == 0:
    print("Acesso bloqueado")