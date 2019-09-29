#!/usr/bin/env bash
set +e

SCRIPT_ROOT=$(dirname "${BASH_SOURCE}")
cd $SCRIPT_ROOT

if [ -s "log" ]; then
  echo -e "\nRESPONSES:\n"
  cat log
fi

if [ -s "err.log" ]; then
  echo -e "\nERRORS:\n"
  cat err.log

  echo -e "\nCONTROLLER LOGS:\n"
  cat controller*.log

  echo -e "\nCONTROLLER CONFIG:\n"
  zorp_pods=$(kubectl get pods -l run=zorp-ingress -n zorp-controller | awk '/zorp/ {print $1}')
  while read -r pod; do
      echo -e '\n*****************************************************************************************************\n'
      kubectl exec pod/$pod -n zorp-controller cat /etc/zorp/policy.py
  done <<< "$zorp_pods"
  exit 1
fi

killall -9 kubectl
rm -f log err.log controller*.log
