#!/bin/bash

# exit when any command fails
set -e

# generate UI > Python code first
./gen.sh
export PLOTLYST_TEST_ENV=1
export PYTHONPATH=src/main/python
python -X faulthandler -m pytest src/main/python/plotlyst  --cov=src.main.python.plotlyst --junitxml=report.xml --cov-report html:coverage --cov-report term -v --color=yes
