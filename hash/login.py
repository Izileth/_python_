import json
import os
import hashlib

from pyfiglet import figlet_format
from rich.console import Console
from rich.panel import Panel


console = Console()

# Autenticação

console.print(
    figlet_format("AUTH", font="slant"),
    style="bold cyan"
)

console.print(
    "[dim]Authentication System[/dim]\n"
)


# Carregar Dataset

ARCHIVE = "database.json"

# Carrega os dados
if os.path.exists(ARCHIVE):

    with open(ARCHIVE, "r", encoding="utf-8") as archive:
        users = json.load(archive)

else:

    users = {}


# Verificação de senha

def verify_password(password, stored_data):

    salt = bytes.fromhex(stored_data["salt"])

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        100_000
    )

    return password_hash == bytes.fromhex(
        stored_data["hash"]
    )


# Login

changes = 2

while changes > 0:

    user = console.input("[cyan]Usuário:[/cyan] ")
    password = console.input("[cyan]Senha:[/cyan] ")

    if user in users and verify_password(
        password,
        users[user]
    ):

        console.print(
            Panel(
                f"[bold green]✓ Bem-vindo, {user}![/bold green]",
                title="AUTH",
                border_style="green"
            )
        )

        break

    else:

        changes -= 1

        console.print(
            "[bold red]✗ Usuário ou senha incorretos[/bold red]"
        )

        console.print(
            f"[dim]Tentativas restantes: {changes}[/dim]"
        )


# Bloqueia acesso

if changes == 0:

    console.print(
        Panel(
            "[bold red]ACESSO BLOQUEADO[/bold red]",
            title="AUTH",
            border_style="red"
        )
    )