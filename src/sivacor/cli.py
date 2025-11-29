import typer

from .submission import list_submissions, get_submission


app = typer.Typer(help="SIVACOR Command Line Interface")
app.command("list")(list_submissions)
app.command("get")(get_submission)


if __name__ == "__main__":
    from sivacor.cli import app
    app()
