#!/usr/bin/env bash

SCRIPT_ROOT=$(dirname "${BASH_SOURCE}")
cd $SCRIPT_ROOT

. deploy.sh
. run_test.sh

echo "CONTROLLER LOGS:"
kubectl logs `kubectl get pods -n zorp-controller | grep zorp | cut -d " " -f 1` -n zorp-controller
