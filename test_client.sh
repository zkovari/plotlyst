#!/bin/bash

# exit when any command fails
set -e

# generate UI > Python code first
pyqt5ac --config .pyqt5ac.yml

python -m pytest src/main/python/plotlyst/test/core --cov-report term -v --color=yes
