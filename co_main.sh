#!/bin/bash

# exit when any command fails
set -e

if git checkout main; then
    git pull
fi