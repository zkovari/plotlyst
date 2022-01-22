#!/bin/bash

# exit when any command fails
set -e

ps aux | grep languagetool
pkill -f languagetool-server