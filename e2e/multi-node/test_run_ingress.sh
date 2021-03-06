#!/usr/bin/env bash
set +e

SCRIPT_ROOT=$(dirname "${BASH_SOURCE}")
cd $SCRIPT_ROOT

# Function params: 1 - port number, 2 - path, optional
test_request () {
  curl -fisSL --insecure http://localhost:$1$2 > test.log 2>test-err.log

  if [ -s "test.log" ]; then
    echo -e "*** Request: http://localhost:$1$2" >> log
    cat test.log >> log
    echo -e '\n' >> log
  fi

  if [ -s "test-err.log" ]; then
    echo -e "*** Request: http://localhost:$1$2" >> err.log
    cat test-err.log >> err.log
    echo -e '\n' >> err.log
  fi

  rm -f test.log
  rm -f test-err.log
}

rm -f log err.log 

echo -e '\n---Testing started---\n'

#------------------------------------------
# Testing apps listening on different ports
echo -e '---Testing apps listening on different ports---\n' >> log

test_request 30500
test_request 30400
test_request 30300

# Testing ingress routing
echo -e '---Testing ingress routing---\n' >> log
test_request 80 /http-app-1
test_request 80 /http-app-2
test_request 80 /http-app-3

#------------------------------------------

echo -e '\n---Testing finished---'


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

rm -f log err.log controller*.log