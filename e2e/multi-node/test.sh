#!/usr/bin/env bash

SCRIPT_ROOT=$(dirname "${BASH_SOURCE}")
cd $SCRIPT_ROOT

. deploy.sh

echo -e "\n WAITING for controller to pick up configuration\n"
sleep 15

. run_test.sh
