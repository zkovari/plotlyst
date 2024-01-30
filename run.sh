#!/bin/bash

# exit when any command fails
set -e

while [[ $# -gt 0 ]]
do
    arg="$1"
    case $arg in
        -p|--profile)
        profile="true"
        shift
        ;;
        *)
        shift
        ;;
    esac
done

# generate UI > Python code first
./gen.sh

py_cmd="python -X faulthandler"
if [ "$profile" == "true" ]
then
    if [ ! -f profile.stats ]
    then
        touch profile.stats
    fi
    py_cmd="$py_cmd -m cProfile -o profile.stats"
fi
export PYTHONPATH=src/main/python
py_cmd="$py_cmd src/main/python/plotlyst/__main__.py --mode DEV $@ &"

eval "$py_cmd"

wait

if [ "$profile" == "true" ]
then
    echo "Profiling results:"
    python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative').print_stats(50)"
fi

