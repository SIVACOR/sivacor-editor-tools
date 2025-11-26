import os
import typer
from typing_extensions import Annotated
from girder_client import GirderClient


def client() -> GirderClient:
    api_url = os.environ.get("GIRDER_API_URL", "https://girder.sivacor.org/api/v1")
    gc = GirderClient(apiUrl=api_url)
    gc.authenticate(apiKey=os.environ["GIRDER_API_KEY"])
    return gc


def get_user(text: Annotated[str, typer.Argument(help="The name to search for")]):
    # Dummy implementation for demonstration purposes
    gc = client()
    return gc.get(f"/user?text={text}")
