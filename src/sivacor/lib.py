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


def abbreviate_image(image_name: str | None, image_tag: str | None) -> str:
    """Shorten a stage's image reference to something a table column can hold.

    The full "repo:tag" is the authoritative record and is still printed by
    `submission get`; here it is only being scanned down a column, where
    "dataeditors/stata18_5-mp:2025-02-26" pushes every other column off the
    terminal. Families come from the allow-list in SIVACOR/sivacor-repo-choice.
    """
    name = (image_name or "").strip()
    tag = (image_tag or "").strip()
    if not name:
        return "N/A"
    repo = name.rsplit("/", 1)[-1]

    if repo.startswith("stata"):
        # dataeditors/stata19_5-mp-i-python -> "Stata 19.5 (py)". The tag is a
        # build date, so it separates rebuilds of the same Stata -- not the
        # distinction anyone is scanning this column for. "-mp" is dropped
        # because every multi-processor image carries it.
        version, _, variant = repo[len("stata") :].partition("-")
        label = f"Stata {version.replace('_', '.')}"
        if "python" in variant:
            label += " (py)"
        return label

    if repo == "dynare":
        # 6.1-R2024a: the suffix is the bundled MATLAB release, and the Dynare
        # version is what identifies the run.
        return f"Dynare {tag.split('-')[0]}" if tag else "Dynare"

    if name.startswith("rocker/"):
        # Every rocker repo is the same R, differing only in which packages
        # come preinstalled -- which the researcher's own install step usually
        # overrides anyway. So the version is the whole label; the tag *is*
        # the version here, unlike Stata's build date.
        return f"R {tag}" if tag else "R"

    # Outside the known families: keep it short but whole, so an unrecognised
    # image reads as unrecognised instead of being mislabelled as one of these.
    return f"{repo}:{tag}" if tag else repo


def image_summary(stages: list[dict]) -> str:
    """One cell naming the images a submission's stages ran on.

    Distinct labels in first-appearance order, each with a count. A multi-stage
    submission usually alternates between two images, and once the labels are
    abbreviated the repeats are literally the same string -- printing all
    seven of them makes the row six lines tall to say two things. The exact
    per-stage sequence is what `submission get` is for.
    """
    if not stages:
        return "N/A"
    counts: dict[str, int] = {}
    for stage in stages:
        label = abbreviate_image(stage.get("image_name"), stage.get("image_tag"))
        counts[label] = counts.get(label, 0) + 1
    return ", ".join(
        label if count == 1 else f"{label} x{count}" for label, count in counts.items()
    )
