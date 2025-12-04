import os

import typer
from girder_client import GirderClient


def client() -> GirderClient:
    api_url = os.environ.get("GIRDER_API_URL", "https://girder.sivacor.org/api/v1")
    gc = GirderClient(apiUrl=api_url)
    gc.authenticate(apiKey=os.environ["GIRDER_API_KEY"])
    return gc


def _get_submission_collection(gc: GirderClient) -> dict:
    root_collection = gc.get("/collection", parameters={"name": "Submissions"})
    if not root_collection:
        typer.echo("No 'Submissions' collection found!", err=True)
        raise typer.Abort()
    return root_collection[0]


def _search_user(gc: GirderClient, user: str) -> dict:
    typer.echo(f"Searching for user with text: {user}")
    users = gc.get(f"/user?text={user}")
    if not users:
        typer.echo(f"No user found with (search: {user})", err=True)
        raise typer.Abort()
    elif len(users) > 1:
        u = next((_ for _ in users if _.get("login") == user), None)
        if not u:
            typer.echo("Found multiple users:")
            for u in users:
                typer.echo(
                    f" - \"{u['firstName']} {u['lastName']}\" <{u['email']}> ({u['login']})"
                )
            typer.echo(
                "Trying to search for user by their specific login name.", err=True
            )
            raise typer.Abort()
    else:
        u = users[0]
    print(
        f"Found user: \"{u['firstName']} {u['lastName']}\" <{u['email']}> ({u['login']})"
    )
    return u
