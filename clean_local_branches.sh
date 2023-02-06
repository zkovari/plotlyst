#!/bin/bash

DRY_RUN=0

function show_help {
  echo "Usage: $(basename "$0") [OPTIONS]"
  echo "Remove local branches that don't exist in the remote and are older than 3 months."
  echo ""
  echo "Options:"
  echo "  -d    Dry run mode. Show what would be deleted, but don't actually delete."
  echo "  -h    Show this help message and exit."
  exit 0
}

while getopts "dh" opt; do
  case $opt in
    d)
      DRY_RUN=1
      ;;
    h)
      show_help
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
  esac
done

current_branch=$(git rev-parse --abbrev-ref HEAD)
now=$(date +%s)
three_months_ago=$(date -d '3 months ago' +%s)

for branch in $(git branch | grep -v $current_branch); do
  if [ -z "$(git ls-remote --heads origin $branch)" ]; then
    branch_date=$(git log -1 --pretty=format:"%ct" $branch)
    if (( branch_date <= three_months_ago )); then
      if [ $DRY_RUN -eq 0 ]; then
        git branch -D $branch
      else
        echo "Dry run: Would have deleted branch $branch"
      fi
    fi
  fi
done
