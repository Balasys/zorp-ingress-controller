#!/usr/bin/env bash
set -e

SCRIPT_ROOT=$(dirname "${BASH_SOURCE}")
cd $SCRIPT_ROOT

docker build -t python-http:1.0.1 ..
kind load docker-image python-http:1.0.1

kubectl apply -f deployments.yaml
kubectl apply -f services.yaml
kubectl apply -f ingress.yaml
kubectl get nodes -o wide
kubectl wait --for=condition=available --timeout=600s deployment/http-app-1
kubectl wait --for=condition=available --timeout=600s deployment/http-app-2
kubectl wait --for=condition=available --timeout=600s deployment/http-app-3

kubectl get deployments -A
kubectl get pods -o wide -A
kubectl get svc -A
