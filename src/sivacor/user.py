import json as jsonlib
import typer
from rich.console import Console
from rich.table import Table
from typing_extensions import Annotated
from .lib import client

console = Console()
app = typer.Typer()


@app.command("list", help="List all users in the SIVACOR system")
def list_users(
    json: Annotated[
        bool,
        typer.Option(help="Output user list in JSON format", show_default=True),
    ] = False,
) -> None:
    gc = client()
    users = gc.listResource("user")
    if json:
        console.print(jsonlib.dumps(list(users), indent=2))
        return

    table = Table(
        title="SIVACOR Users", show_header=True, header_style="bold magenta"
    )
    table.add_column("Name", style="bold green", min_width=20)
    table.add_column("Email", style="dim", min_width=24)
    table.add_column("Last Job ID", justify="left")
    table.add_column("OAuth IDs", justify="left")

    for user in users:
        oauth = {}
        if "oauth" in user:
            for _ in user["oauth"]:
                oauth[_['provider']] = _["id"]
        table.add_row(
            f"{user['firstName']} {user['lastName']}",
            user.get("email", "N/A"),
            user.get("lastJobId", "N/A"),
            ",".join(list(oauth.keys()))
        )
    if json:
        console.print(jsonlib.dumps(user, indent=2))
    else:
        console.print(table)
