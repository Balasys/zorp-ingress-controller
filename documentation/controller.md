# ![Zorp](../assets/images/balasys-logo.png "Zorp")

## Zorp kubernetes ingress controller

you can run image with arguments:

- `--ingress.class`
  - default: "zorp"
  - class of ingress object to monitor in multiple controllers environment
- `--namespace`
  - default: "default"
  - the namespace to watch for ingresses
- `--behaviour`
  - default: "basic"
  - choice: ["basic", "tosca"]
  - chooses if the controller should generate Zorp configuration based on k8s objects or TOSCA syntax annotation
