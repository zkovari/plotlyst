#!/bin/bash

# exit when any command fails
set -e

# generates Python code from Qt UI files. See .pyqt5ac.yml for reference
pyqt5ac --config .pyqt5ac.yml
