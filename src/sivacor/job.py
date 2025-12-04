import json as jsonlib
import typer
from typing import List
from rich.console import Console
from rich.table import Table
from typing_extensions import Annotated
from .lib import client

console = Console()
app = typer.Typer()

{
    "created": "2025-11-14T01:44:16.919000+00:00",
    "status": 3,
    "title": "SIVACOR Run for astroML.tgz by Kacper Kowalik",
    "type": "sivacor_submission",
    "updated": "2025-11-14T01:44:23.952000+00:00",
    "when": "2025-11-14T01:44:16.919000+00:00",
}


@app.command("list", help="List all submission jobs")
def list_jobs(
    status: Annotated[
        List[int] | None,
        typer.Option(help="Filter jobs by status codes, e.g. [4] for 'failed'", show_default=True),
    ] = None,
    types: Annotated[
        List[str] | None,
        typer.Option(help="Filter jobs by types", show_default=True),
    ] = ["sivacor_submission"],
    json: Annotated[
        bool,
        typer.Option(help="Output user list in JSON format", show_default=True),
    ] = False,
) -> None:
    gc = client()
    params = {}
    if status:
        params["statuses"] = jsonlib.dumps(status)
    if types:
        params["types"] = jsonlib.dumps(types)

    jobs = gc.listResource("job/all", params=params)
    jobs = list(jobs)
    table = Table(title="SIVACOR Jobs", show_header=True, header_style="bold magenta")
    table.add_column("Job ID", style="bold green", min_width=20)
    table.add_column("Title", style="dim", min_width=40)
    table.add_column("Status", justify="left")
    table.add_column("Created", justify="left")

    for job in jobs:
        table.add_row(
            job['_id'],
            job["title"],
            status_code_to_str(job["status"]),
            job["created"][:16].replace("T", " "),
        )

    if json:
        console.print(jsonlib.dumps(jobs, indent=2))
    else:
        console.print(table)

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
