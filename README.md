# ![Zorp](https://github.com/Balasys/zorp-ingress-controller/raw/master/assets/images/balasys-logo.png "Balasys")

## Zorp Kubernetes Ingress Controller

### Description

An ingress controller is a Kubernetes resource that routes traffic from outside your cluster to services within the cluster. 

### Usage

Docker image is available on Docker Hub: [balasys/zorp-ingress](https://hub.docker.com/r/balasys/zorp-ingress)

If you prefer to build it from source use
```
docker build -t balasys/zorp-ingress -f build/Dockerfile .
```

Please see [controller.md](https://github.com/Balasys/zorp-ingress-controller/blob/master/documentation/controller.md) for all available arguments of controler image.

Available customisations are described in [doc](https://github.com/Balasys/zorp-ingress-controller/blob/master/documentation/README.md)

Basic setup to to run controller is described in [yaml](https://github.com/Balasys/zorp-ingress-controller/blob/master/deploy/zorp-ingress.yaml) file.
```
kubectl apply -f deploy/zorp-ingress.yaml
```

### Contributing

For commit messages and general style please follow the zorp project's [CONTRIBUTING guide](https://github.com/Balasys/zorp/blob/master/CONTRIBUTING) and use that where applicable.

Please use `golangci-lint run` from [github.com/golangci/golangci-lint](https://github.com/golangci/golangci-lint) for linting code.

## License

[Apache License 2.0](LICENSE)
