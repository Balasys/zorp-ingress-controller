#!/usr/bin/env bash

SCRIPT_ROOT=$(dirname "${BASH_SOURCE}")
cd $SCRIPT_ROOT

. test_deploy.sh
. test_logging.sh
. test_deploy_app.sh
. test_wait.sh
. test_run.sh
. test_cleanup.sh

. test_deploy_ingress.sh
. test_logging.sh
. test_deploy_app_ingress.sh
. test_wait.sh
. test_run_ingress.sh
. test_cleanup.sh
