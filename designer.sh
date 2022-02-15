#!/bin/bash

# exit when any command fails
set -e
export QT_DEBUG_PLUGINS=0

pyqt5-tools designer -p plugins &