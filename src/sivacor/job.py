import asyncio
import json as jsonlib
import os
import sys
from datetime import datetime
from typing import List

import dateutil.parser
import typer
import websockets
from rich.console import Console
from rich.table import Table
from typing_extensions import Annotated
from tzlocal import get_localzone

from .lib import client

console = Console()
app = typer.Typer()


async def connect_to_job_stream(token):
    """
    Connects to the WebSocket server and listens for incoming log messages.
    """

    api_url = os.environ.get("GIRDER_API_URL", "https://girder.sivacor.org/api/v1")
    ws_url = api_url.replace("http", "ws").replace("/api/v1", "/logs/docker?token=")
    print(f"Attempting to connect to WebSocket at: {ws_url}...")

    try:
        async with websockets.connect(ws_url + token) as websocket:
            print("Connection successful! 🟢 Subscribed to log stream.")
            print("=" * 60)

            # This loop waits indefinitely for incoming messages
            while True:
                try:
                    # Receive a text message (your log line)
                    log_message = await websocket.recv()
                    if hasattr(log_message, "decode"):
                        log_message = log_message.decode("utf-8")
                    print(f"| {log_message}")

                except websockets.exceptions.ConnectionClosedOK:
                    print("\nConnection closed gracefully by the server.")
                    break
                except websockets.exceptions.ConnectionClosedError as e:
                    print(
                        f"\nConnection closed unexpectedly (Code: {e.code}, Reason: {e.reason})."
                    )
                    break

    except ConnectionRefusedError:
        print(
            "\nConnection Refused: Ensure the Starlette server (uvicorn) is "
            "running and accessible at {ws_url}."
        )
        sys.exit(1)
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        sys.exit(1)

    finally:
        print("=" * 60)
        print("WebSocket client debugger stopped.")


@app.command("list", help="List all submission jobs")
def list_jobs(
    status: Annotated[
        List[int] | None,
        typer.Option(
            help="Filter jobs by status codes, e.g. [4] for 'failed'", show_default=True
        ),
    ] = None,
    types: Annotated[
        List[str] | None,
        typer.Option(help="Filter jobs by types", show_default=True),
    ] = ["sivacor_submission"],
    json: Annotated[
        bool,
        typer.Option(help="Output user list in JSON format", show_default=True),
    ] = False,
    since: Annotated[
        datetime | None,
        typer.Option(help="Filter jobs created since this date", show_default=True),
    ] = None,
) -> None:
    gc = client()
    local_tz = get_localzone()
    params = {}
    if status:
        params["statuses"] = jsonlib.dumps(status)
    if types:
        params["types"] = jsonlib.dumps(types)
    if since:
        since = since.replace(tzinfo=local_tz, microsecond=0)

    jobs = gc.listResource("job/all", params=params)
    jobs = list(jobs)
    table = Table(title="SIVACOR Jobs", show_header=True, header_style="bold magenta")
    table.add_column("Job ID", style="bold green", min_width=20)
    table.add_column("Title", style="dim", min_width=40)
    table.add_column("Status", justify="left")
    table.add_column("Created", justify="left")

    for job in jobs:
        created = dateutil.parser.parse(job["created"]).astimezone(local_tz)
        if since and created < since:
            continue
        table.add_row(
            job["_id"],
            job["title"],
            status_code_to_str(job["status"]),
            job["created"][:16].replace("T", " "),
        )

    if json:
        console.print(jsonlib.dumps(jobs, indent=2))
    else:
        console.print(table)


@app.command("stream", help="Show stdout/stderr of the current submission job")
def stream_current_job() -> None:
    gc = client()
    try:
        asyncio.run(connect_to_job_stream(gc.token))
    except KeyboardInterrupt:
        print("\n\nClient stopped by user (Ctrl+C)")


@app.command("get", help="Get details of a specific job by ID")
def get_job(job_id: str) -> None:
    gc = client()
    job = gc.getResource("job", job_id)
    console.print_json(jsonlib.dumps(job, indent=2))


def status_code_to_str(code: int) -> str:
    status_map = {
        0: "Inactive",
        1: "Queued",
        2: "Running",
        3: "Completed",
        4: "Failed",
        5: "Canceled",
    }
    return status_map.get(code, "Unknown")
