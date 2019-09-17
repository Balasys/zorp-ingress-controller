# ![Zorp](../assets/images/balasys-logo.png "Zorp")

## Zorp kubernetes ingress controller

Options for starting controller can be found in [controller.md](controller.md)

### Ingress Class

- Annotation: `ingress.class`
  - default: ""
  - used to monitor specific ingress objects in multiple controllers environment
  - any ingress object which have class specified and its different from one defined in [image arguments](controller.md) will be ignored

### Secrets

#### tls-secret

- single certificate secret can contain two items:
  - tls.key
  - tls.crt
