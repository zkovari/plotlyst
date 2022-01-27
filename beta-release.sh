#!/bin/bash

# exit when any command fails
set -e

git checkout release/beta
git merge main
git push origin release/beta
git checkout main