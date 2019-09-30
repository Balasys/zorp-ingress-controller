#!/usr/bin/env bash
set -e

SCRIPT_ROOT=$(dirname "${BASH_SOURCE}")
cd $SCRIPT_ROOT

zorp_pods=$(kubectl get pods -l run=zorp-ingress -n zorp-controller | awk '/zorp/ {print $1}')

kubectl delete daemonset/zorp-ingress -n zorp-controller
kubectl delete ingress/example-ingress

while [ -n "$zorp_pods" ]; do  
    sleep 1
    echo $zorp_pods
    zorp_pods=$(kubectl get pods -l run=zorp-ingress -n zorp-controller | awk '/zorp/ {print $1}')    
done 

kubectl apply -f replace-zorp-ingress.yaml

zorp_pods=$(kubectl get pods -l run=zorp-ingress -n zorp-controller | awk '/zorp/ {print $1}')

while read -r pod; do
    kubectl wait --for=condition=Ready --timeout=600s pod/$pod -n zorp-controller
done <<< "$zorp_pods"
