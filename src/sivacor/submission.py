import json as jsonlib
from datetime import datetime
from enum import Enum
from typing import List

import dateutil.parser
import typer
from rich.columns import Columns
from rich.console import Console
from rich.padding import Padding
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from typing_extensions import Annotated
from tzlocal import get_localzone

from .lib import _get_submission_collection, _search_user, client

app = typer.Typer()
console = Console()


class SubmissionFile(str, Enum):
    REPLPACK = "ReplPack"
    STDOUT = "stdout"
    STDERR = "stderr"
    TRO = "tro"
    TSR = "tsr"
    SIG = "sig"


enum_to_file_map = {
    SubmissionFile.REPLPACK: "Replicated Package",
    SubmissionFile.STDOUT: "Run output log",
    SubmissionFile.STDERR: "Run error log",
    SubmissionFile.TRO: "TRO Declaration",
    SubmissionFile.TSR: "Trusted Timestamp",
    SubmissionFile.SIG: "TRS Signature",
}


def status_icon(status: str) -> str:
    status_map = {
        "submitted": "⏳",
        "processing": "🔄",
        "completed": "✅",
        "failed": "❌",
    }
    return status_map.get(status.lower(), "❓")


@app.command("list", help="List all submissions")
def list_submissions(
    user: Annotated[
        str | None, typer.Option(help="Only print submissions created by this user")
    ] = None,
    sort: Annotated[
        str,
        typer.Option(
            help="Field to sort submissions by, e.g. 'created' or 'name'",
            show_default=True,
        ),
    ] = "created",
    sortDir: Annotated[
        int,
        typer.Option(
            help="Direction to sort submissions (1: ascending, -1: descending)",
            show_default=True,
        ),
    ] = -1,
    json: Annotated[
        bool,
        typer.Option(help="Output submission list in JSON format", show_default=True),
    ] = False,
    since: Annotated[
        datetime | None,
        typer.Option(
            help="Filter submissions created since this date", show_default=True
        ),
    ] = None,
) -> None:
    # Dummy implementation for demonstration purposes
    gc = client()
    if user:
        user_info = _search_user(gc, user)
        console.print(f"[yellow]Filtering by user ID: {user_info['_id']}[/yellow]")
    if since:
        since = since.replace(tzinfo=get_localzone(), microsecond=0)

    if not json:
        console.print("[bold cyan]🚀 Listing Submissions[/bold cyan]")
    table = Table(
        title="Submission Folders", show_header=True, header_style="bold magenta"
    )
    table.add_column("Submission Name", style="bold green", min_width=20)
    table.add_column("Job ID", style="dim", min_width=24)
    table.add_column("Image Tag", justify="left")
    table.add_column("Creator", justify="left")
    table.add_column("Created Date", justify="right", style="cyan")
    table.add_column("Status", justify="center")

    users = {
        _["_id"]: f"{_['firstName']} {_['lastName']} ({_['login']})"
        for _ in gc.listResource("user")
    }

    root_collection = _get_submission_collection(gc)
    params = {
        "sort": sort,
        "sortdir": sortDir,
        "parentType": "collection",
        "parentId": root_collection["_id"],
    }
    folders = []
    for folder in gc.listResource("folder", params):
        created = dateutil.parser.parse(folder["created"])
        if since and created < since:
            continue
        if user:
            if folder["meta"].get("creator_id", "") != user_info["_id"]:
                continue
        folders.append(folder)
        stages = folder["meta"].get("stages", [])
        image = (
            ",".join(
                [
                    f"{stage.get('image_name', 'N/A')}:{stage.get('image_tag', 'N/A')}"
                    for stage in stages
                ]
            )
            if stages
            else "N/A"
        )
        created = folder["created"].split(".")[0].replace("T", " ")
        table.add_row(
            folder["name"],
            folder["meta"].get("job_id", "N/A"),
            image,
            users.get(folder["meta"].get("creator_id", ""), "Unknown"),
            created,
            status_icon(folder["meta"].get("status", "unknown")),
        )

    if json:
        console.print(jsonlib.dumps(folders, indent=2))
    else:
        console.print(table)


@app.command(
    "get", help="Get details about a specific submission and/or download its files"
)
def get_submission(
    submission: Annotated[
        str, typer.Argument(help="The Job ID or name of the submission to retrieve")
    ],
    download: Annotated[
        List[SubmissionFile] | None,
        typer.Option(
            help="Optionally download a specific file associated with the submission",
            show_default=False,
        ),
    ] = None,
    json: Annotated[
        bool,
        typer.Option(
            help="Output submission details in JSON format", show_default=True
        ),
    ] = False,
) -> None:
    # Dummy implementation for demonstration purposes
    if not json:
        typer.echo("Getting a specific submission...")
    gc = client()
    root_collection = _get_submission_collection(gc)
    params = {
        "parentType": "collection",
        "parentId": root_collection["_id"],
    }
    if "-" in submission:
        params["name"] = submission
    else:
        params["jobId"] = submission

    folders = gc.get("/folder", parameters=params)
    folder = folders[0] if folders else None

    if not folder:
        console.print(
            f"[bold red]❌ Error:[/bold red] Submission '{submission}' not found."
        )
        raise typer.Exit(code=1)

    if json:
        console.print(jsonlib.dumps(folder, indent=2))
        return

    # 2. Display Core Summary
    meta = folder.get("meta", {})

    summary_content = Text()
    summary_content.append("Status: ", style="bold")
    summary_content.append(f"{meta.get('status', 'N/A')}\n", style="yellow")
    stages = meta.get("stages", [])
    for i, stage in enumerate(stages):
        summary_content.append(f"Stage {i+1} Image Tag: ", style="bold")
        summary_content.append(
            f"{stage.get('image_name', 'N/A')}:{stage.get('image_tag')}\n",
            style="magenta",
        )
    summary_content.append("Created: ", style="bold")
    summary_content.append(
        f"{folder.get('created', 'N/A').split('.')[0].replace('T', ' ')}\n",
        style="cyan",
    )
    summary_content.append("Updated: ", style="bold")
    summary_content.append(
        f"{folder.get('updated', 'N/A').split('.')[0].replace('T', ' ')}", style="cyan"
    )
    if creator_id := meta.get("creator_id"):
        creator = gc.get(f"/user/{creator_id}")
        summary_content.append("\nSubmitted by: ", style="bold")
        summary_content.append(
            f"{creator.get('firstName')} {creator.get('lastName')}", style="green"
        )

    summary_panel = Panel(
        summary_content,
        title="[bold white]📝 Submission Summary[/bold white]",
        border_style="blue",
    )
    console.print(summary_panel)

    # 3. Display File Downloads
    console.print(Padding("\n[bold]📦 Available Files for Download:[/bold]", (1, 0)))

    FILE_MAP = {
        "Replicated Package": meta.get("replpack_file_id"),
        "Run output log": meta.get("stdout_file_id"),
        "Run error log": meta.get("stderr_file_id"),
        "TRO Declaration": meta.get("tro_file_id"),
        "Trusted Timestamp": meta.get("tsr_file_id"),
        "TRS Signature": meta.get("sig_file_id"),
    }

    # Create rich Text objects for the file list
    file_list = []

    for name, file_id in FILE_MAP.items():
        if file_id:
            # Use Typer.prompt (which uses Rich) to offer the download
            file_list.append(f"[bold white]{name}:[/bold white] [dim]{file_id}[/dim]")

    console.print(Columns(file_list, expand=True, equal=True))

    download = download or []
    for fetch in download:
        name = enum_to_file_map[fetch.value]
        file_id = FILE_MAP.get(name)
        if not file_id:
            console.print(
                f"[bold red]File '{name}' not available for download.[/bold red]"
            )
            continue
        console.print(f"Downloading [bold]{name}[/bold]...")
        fobj = gc.get(f"/file/{file_id}")
        gc.downloadFile(file_id, fobj["name"])
