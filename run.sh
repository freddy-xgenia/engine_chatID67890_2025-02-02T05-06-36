#!/bin/bash

### Check if poetry is installed, if not install it
if ! command -v poetry &> /dev/null; then
    echo "Poetry not found, installing..."
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="/root/.local/bin:$PATH"
else
    echo "Poetry is already installed."
fi

### Set the current directory to the project directory
cd "$(dirname "${BASH_SOURCE[0]}")"

### Install poetry dependencies and run the apps
poetry lock
poetry install
poetry run python3 main.py