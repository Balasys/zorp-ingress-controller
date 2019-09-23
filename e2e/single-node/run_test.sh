#!/usr/bin/env bash
set +e

SCRIPT_ROOT=$(dirname "${BASH_SOURCE}")
cd $SCRIPT_ROOT

# Function params: 1 - port number, 2 - path, optional
test_request () {
  curl -fisSL --insecure http://$(minikube ip):$1$2 > test.log 2>test-err.log

  if [ -s "test.log" ]; then
    echo -e "*** Request: http://$(minikube ip):$1$2" >> log
    cat test.log >> log
    echo -e '\n' >> log
  fi

  if [ -s "test-err.log" ]; then
    echo -e "*** Request: http://$(minikube ip):$1$2" >> err.log
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

# Testing port-based routing
echo -e '---Testing port-based routing---\n' >> log
test_request 5000
test_request 4000
test_request 3000

#------------------------------------------

if [ -s "log" ]; then
  echo -e "\nRESPONSES:\n"
  cat log
fi

if [ -s "err.log" ]; then
  echo -e "\nERRORS:\n"
  cat err.log
fi

echo -e '\n---Testing finished---'

[ -s err.log ] && exit 1 || exit 0 