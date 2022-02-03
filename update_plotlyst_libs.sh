#!/bin/bash

# exit when any command fails
set -e

pip uninstall -y qt-anim
pip uninstall -y qt-textedit
pip uninstall -y qt-handy

pip install git+https://github.com/plotlyst/qt-anim.git
pip install git+https://github.com/plotlyst/qt-textedit.git
pip install git+https://github.com/plotlyst/qt-handy.git