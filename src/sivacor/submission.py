import math
import json as jsonlib
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Dict

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


def duration(start: datetime, end: datetime) -> str:
    delta = end - start
    days, seconds = delta.days, delta.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if seconds > 0 or not parts:
        parts.append(f"{seconds}s")
    return " ".join(parts)


def convert_size(size_bytes, binary=True):
    if size_bytes <= 0:
        return "0B"
    if binary:
        suffix = "i"
        base = 1024
    else:
        suffix = ""
        base = 1000
    size_name = (
        "B",
        f"K{suffix}B",
        f"M{suffix}B",
        f"G{suffix}B",
        f"T{suffix}B",
        f"P{suffix}B",
    )
    i = int(math.floor(math.log(size_bytes, base)))
    p = math.pow(base, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


@dataclass(frozen=True)
class FileSpec:
    """Specification for a submission file type, consolidating all naming variants."""

    cli_name: str  # Used in CLI enum (e.g., "ReplPack")
    display_name: str  # Human-readable name (e.g., "Replicated Package")
    field_name: str  # Database field name (e.g., "replpack_file_id")
    api_type: str  # API metadata type (e.g., "replicated_package")

    @property
    def enum_value(self) -> str:
        """Return the CLI enum value."""
        return self.cli_name


# Define all submission file specifications
class SubmissionFiles:
    """Registry of all submission file types."""

    REPLPACK = FileSpec(
        cli_name="ReplPack",
        display_name="Replicated Package",
        field_name="replpack_file_id",
        api_type="replicated_package",
    )
    STDOUT = FileSpec(
        cli_name="stdout",
        display_name="Run output log",
        field_name="stdout_file_id",
        api_type="stdout",
    )
    STDERR = FileSpec(
        cli_name="stderr",
        display_name="Run error log",
        field_name="stderr_file_id",
        api_type="stderr",
    )
    TRO = FileSpec(
        cli_name="tro",
        display_name="TRO Declaration",
        field_name="tro_file_id",
        api_type="tro_declaration",
    )
    TSR = FileSpec(
        cli_name="tsr",
        display_name="Trusted Timestamp",
        field_name="tsr_file_id",
        api_type="tro_timestamp",
    )
    SIG = FileSpec(
        cli_name="sig",
        display_name="TRS Signature",
        field_name="sig_file_id",
        api_type="tro_signature",
    )

    @classmethod
    def all(cls) -> List[FileSpec]:
        """Return all file specifications."""
        return [
            cls.REPLPACK,
            cls.STDOUT,
            cls.STDERR,
            cls.TRO,
            cls.TSR,
            cls.SIG,
        ]

    @classmethod
    def by_cli_name(cls) -> Dict[str, FileSpec]:
        """Return mapping from CLI name to FileSpec."""
        return {spec.cli_name: spec for spec in cls.all()}

    @classmethod
    def by_api_type(cls) -> Dict[str, FileSpec]:
        """Return mapping from API type to FileSpec."""
        return {spec.api_type: spec for spec in cls.all()}

    @classmethod
    def by_display_name(cls) -> Dict[str, FileSpec]:
        """Return mapping from display name to FileSpec."""
        return {spec.display_name: spec for spec in cls.all()}


class SubmissionFile(str, Enum):
    """CLI Enum for submission file types."""

    ALL = "all"
    REPLPACK = "ReplPack"
    STDOUT = "stdout"
    STDERR = "stderr"
    TRO = "tro"
    TSR = "tsr"
    SIG = "sig"


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
    head: Annotated[
        int | None,
        typer.Option(help="Only show the first N submissions", show_default=False),
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
    table.add_column("Duration", justify="right", style="cyan")
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
    for folder in gc.listResource("folder", params, limit=head):
        created = dateutil.parser.parse(folder["created"]).astimezone(get_localzone())
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
        table.add_row(
            folder["name"],
            folder["meta"].get("job_id", "N/A"),
            image,
            users.get(folder["meta"].get("creator_id", ""), "Unknown"),
            created.strftime("%Y-%m-%d %H:%M:%S %Z"),
            duration(
                created,
                dateutil.parser.parse(folder["updated"]).astimezone(get_localzone()),
            ),
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
    job = gc.get(f"/job/{folder['meta']['job_id']}") if folder else None

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
    summary_content.append("Stages:\n", style="bold")
    stages = meta.get("stages", [])
    for i, stage in enumerate(stages):
        summary_content.append(f" {i+1}. ", style="bold")
        summary_content.append("Image: ", style="dim")
        summary_content.append(
            f"{stage.get('image_name', 'N/A')}:{stage.get('image_tag')}\n",
            style="magenta",
        )
        summary_content.append("    Main File: ", style="dim")
        summary_content.append(f"{stage.get('main_file', 'N/A')}\n", style="magenta")
    summary_content.append("Created: ", style="bold")
    created = dateutil.parser.parse(folder["created"]).astimezone(get_localzone())
    summary_content.append(
        f"{created.strftime('%Y-%m-%d %H:%M:%S %Z')}\n",
        style="cyan",
    )
    summary_content.append("Updated: ", style="bold")
    updated = dateutil.parser.parse(folder["updated"]).astimezone(get_localzone())
    summary_content.append(
        f"{updated.strftime('%Y-%m-%d %H:%M:%S %Z')}\n", style="cyan"
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

    if job:
        console.print("\n[bold]🔍 Main workflow job logs:[/bold]")
        for line in job.get("log", []):
            console.print(f"[dim]{line.strip()}[/dim]")

    # 3. Display File Downloads
    console.print(Padding("\n[bold]📦 Files Available for Download:[/bold]", (1, 0)))

    # Build mapping from display name to file ID from submission metadata
    file_id_map = {}
    for spec in SubmissionFiles.all():
        file_id = meta.get(spec.field_name)
        if file_id:
            file_id_map[spec.display_name] = file_id

    # Build mapping from API type to FileSpec for easy lookup
    api_type_to_spec = SubmissionFiles.by_api_type()

    # Create rich Text objects for the file list
    file_list = []
    items = {}
    for item in gc.get("/item", parameters={"folderId": folder["_id"]}):
        api_type = item.get("meta", {}).get("type")
        spec = api_type_to_spec.get(api_type)

        if not spec:
            continue

        display_name = spec.display_name
        items[display_name] = {
            "itemId": item["_id"],
            "name": item["name"],
            "size": item["size"],
        }

        line = (
            f"[bold white] - {display_name}:[/bold white] [dim]{item['name']}[/dim] "
            f"(size: [dim]{convert_size(item['size'])}[/dim]) "
            f"(Girder Item ID: [dim]{item['_id']}[/dim])"
        )
        file_list.append(Text.from_markup(line))

    console.print(Columns(file_list, expand=True, equal=True))

    download = download or []
    cli_name_to_spec = SubmissionFiles.by_cli_name()

    # If 'all' is specified, download all available files
    if any(fetch.value == "all" for fetch in download):
        download_specs = [
            cli_name_to_spec[spec.cli_name] for spec in SubmissionFiles.all()
        ]
    else:
        download_specs = []
        for fetch in download:
            spec = cli_name_to_spec.get(fetch.value)
            if not spec:
                console.print(
                    f"[bold red]Unknown file type: '{fetch.value}'[/bold red]"
                )
                continue
            download_specs.append(spec)

    for spec in download_specs:
        file_id = file_id_map.get(spec.display_name)
        if not file_id:
            console.print(
                f"[bold red]File '{spec.display_name}' not available for download.[/bold red]"
            )
            continue

        console.print(f"Downloading [bold]{spec.display_name}[/bold]...")
        fobj = gc.get(f"/file/{file_id}")
        gc.downloadFile(file_id, fobj["name"])
