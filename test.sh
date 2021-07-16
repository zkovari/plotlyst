#!/bin/bash

# exit when any command fails
set -e

# generate UI > Python code first
./gen.sh
python -m pytest src/main/python/plotlyst  --cov=plotlyst --junitxml=report.xml --cov-report html:coverage --cov-report term -v --color=yes