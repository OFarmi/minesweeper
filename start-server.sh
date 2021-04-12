#!/usr/bin/env bash

artifacts_dir="$(pwd)/artifacts/"

# Generate static files
pushd "$(pwd)/frontend"
    npx webpack --env minesweeper_static_folder="$artifacts_dir"
popd

MINESWEEPER_STATIC_FOLDER="$artifacts_dir" gunicorn --worker-class=eventlet --workers=1 server:app