#!/bin/sh

cd "$(dirname "$0")"
exec env/bin/python3 main.py "$@"
