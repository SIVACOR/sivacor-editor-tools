import typer

from .submission import app as submission_app
from .user import app as user_app


app = typer.Typer(help="SIVACOR Command Line Interface")
app.add_typer(user_app, name="user", help="'User' collection related commands")
app.add_typer(submission_app, name="submission", help="'Submission' collection related commands")


if __name__ == "__main__":
    from sivacor.cli import app
    app()
