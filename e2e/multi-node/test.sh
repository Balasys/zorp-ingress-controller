#!/usr/bin/env bash

SCRIPT_ROOT=$(dirname "${BASH_SOURCE}")
cd $SCRIPT_ROOT

. deploy.sh

echo -e "\n WAITING for controller to pick up configuration...\n"
sleep 15

echo -n "\n ACTIVE sockets:\n"
netstat -antup

. run_test.sh
