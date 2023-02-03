#!/bin/bash

# exit when any command fails
set -e

git checkout release/beta
merge_output=$(git merge main 2>&1)
if echo "$merge_output" | grep -q "CONFLICT"; then
  echo "$merge_output"
  exit 1
fi

git push origin release/beta
git checkout main