#!/bin/bash

# DeepDrone launcher wrapper (runs root entrypoint)

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR/.."

python3 run.py
