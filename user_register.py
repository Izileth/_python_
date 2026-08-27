import hashlib
import os
import json

from pyfiglet import figlet_format
from rich.console import Console
from rich.panel import Panel


console = Console()


# ==========================================
#                REGISTER
# ==========================================

console.print(
    figlet_format("REGISTER", font="slant"),
    style="bold cyan"
)

console.print(
    "[dim]Create a new account[/dim]\n"
)


# ==========================================
#                DATABASE
# ==========================================

ARCHIVE = "database.json"

if os.path.exists(ARCHIVE):

    with open(ARCHIVE, "r", encoding="utf-8") as archive:
        users = json.load(archive)

else:

    users = {}


# ==========================================
#            PASSWORD HASHING
# ==========================================

def hash_password(password):

    salt = os.urandom(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        100_000
    )

    return {
        "salt": salt.hex(),
        "hash": password_hash.hex()
    }


# ==========================================
#              CREATE USER
# ==========================================

user = console.input(
    "[cyan]Create a user:[/cyan] "
)

password = console.input(
    "[cyan]Create a password:[/cyan] "
)

confirm_password = console.input(
    "[cyan]Confirm password:[/cyan] "
)


# ==========================================
#          PASSWORD VALIDATION
# ==========================================

if password != confirm_password:

    console.print(
        Panel(
            "[bold red]✗ Passwords do not match.[/bold red]",
            title="REGISTER",
            border_style="red"
        )
    )

    exit()


# ==========================================
#          USER VALIDATION
# ==========================================

if user in users:

    console.print(
        Panel(
            "[bold red]✗ User already exists.[/bold red]",
            title="REGISTER",
            border_style="red"
        )
    )

    exit()


# ==========================================
#              SAVE USER
# ==========================================

users[user] = hash_password(password)


with open(ARCHIVE, "w", encoding="utf-8") as archive:

    json.dump(
        users,
        archive,
        indent=4
    )


# ==========================================
#               SUCCESS
# ==========================================

console.print(
    Panel(
        f"[bold green]✓ User '{user}' created successfully![/bold green]",
        title="REGISTER",
        border_style="green"
    )
)