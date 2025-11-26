import typer

from .sivacor import submission


app = typer.Typer(help="SIVACOR Command Line Interface")
app.command()(submission)


if __name__ == "__main__":
    app()
