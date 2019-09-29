#!/usr/bin/env bash
set -e

SCRIPT_ROOT=$(dirname "${BASH_SOURCE}")
cd $SCRIPT_ROOT

zorp_pods=$(kubectl get pods -l run=zorp-ingress -n zorp-controller | awk '/zorp/ {print $1}')
while read -r pod; do
    kubectl logs -f pod/$pod -n zorp-controller >> controller-$pod.log
done <<< "$zorp_pods"
