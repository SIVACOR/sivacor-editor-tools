# SIVACOR toolkit

## How to install

1. Install `pipx` if you don't have it already:

   ```bash
   python3 -m pip install --user pipx
   python3 -m pipx ensurepath
   ```

   or follow more detailed instructions at [https://pipx.pypa.io/stable/](https://pipx.pypa.io/stable/).
2. Install the SIVACOR toolkit using `pipx`:

   ```bash
   pipx install git+https://github.com/SIVACOR/sivacor-editor-tools.git
   ```

   follow the instructions to ensure your PATH is set up correctly.

3. Verify the installation by running:

   ```bash

   sivacor --help
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
