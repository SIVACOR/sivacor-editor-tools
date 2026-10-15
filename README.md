# SIVACOR toolkit

## How to install

1. Install [`uv`](https://docs.astral.sh/uv/) if you don't have it already:

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

   or follow more detailed instructions at
   [https://docs.astral.sh/uv/getting-started/installation/](https://docs.astral.sh/uv/getting-started/installation/).

2. Install the SIVACOR toolkit as a `uv` tool:

   ```bash
   uv tool install git+https://github.com/SIVACOR/sivacor-editor-tools.git
   ```

   Add `uv tool update-shell` (once) if `~/.local/bin` isn't on your `PATH` yet.

   To also read configuration from a `.env` file, install with the `extras` extra:

   ```bash
   uv tool install "sivacor[extras] @ git+https://github.com/SIVACOR/sivacor-editor-tools.git"
   ```

3. Verify the installation by running:

   ```bash
   sivacor --help
   ```

   Later, upgrade with `uv tool upgrade sivacor`, or remove it with
   `uv tool uninstall sivacor`.

   You can also run it without installing anything:

   ```bash
   uvx --from git+https://github.com/SIVACOR/sivacor-editor-tools.git sivacor --help
   ```

## How to use

1. Ensure that you have Girder API Key set in your environment variables:

   ```bash
   export GIRDER_API_KEY="your_api_key_here"
   ```

2. You can use the SIVACOR toolkit by running the `sivacor` command in your terminal. For example

   ```bash
   sivacor submission list --user <login or name>
   ```

   ```bash
   sivacor submission get <id>
   ```

   ```bash
   sivacor user list
   ```

## Development

The project is managed with `uv`; `uv.lock` pins the full dependency set.

```bash
uv sync --extra extras   # create .venv from the lockfile
uv run sivacor --help    # run the CLI from the project environment
uv run ruff check src/   # lint
uv build                 # build sdist + wheel into dist/
uv lock --upgrade        # refresh pinned versions
```
