# kubernetes-essentials

An Ansible role to deploy the essentials of a highly available Kubernetes cluster. Includes in-cluster apiserver and ingress controller loadbalancing, dns and flannel.

It was originally loosely based on the [kelseyhightower/kubernetes-the-hard-way](https://github.com/kelseyhightower/kubernetes-the-hard-way) runbooks, but this version is completely Ansible-ised, and not GCP-specific.
+ In common, it downloads and runs the controller componenets (apiserver, controller-manager and scheduler) _outside_ the cluster as systemd services.  Similarly, for kubelets on the worker nodes.  
+ However:
  + _etcd_ runs in separate VMs
  + The apiserver nodes are load-balanced using cloud-specific tools:
    + **Libvirt** (bare-metal): [_keepalived_](https://www.keepalived.org/manpage.html) (using IPVS real-servers on the same hosts as the directors). The VIP floats between the apiservers and load-balances the request in the kernel for processing by one of the peer apiservers.
    + **AWS**: Network load balancers, configured for internal load-balancing.  One per-zone for resilience.
  + [haproxy-ingress](https://haproxy-ingress.github.io/) is used as an ingress controller (using the [Gateway API](https://haproxy-ingress.github.io/docs/configuration/gateway-api/)).  It runs as a daemonset on special _node-edge_ worker nodes with hostNetwork.
    + External DNS must be configured to point to the _node-edge_ woker nodes.  e.g.:
      + `*.k8s           IN      A    192.168.1.59`
      + `*.k8s           IN      A    192.168.1.60`
      + `*.k8s           IN      A    192.168.1.61`
  + [flannel](https://github.com/coreos/flannel) provides the layer 3 overlay network
  + [CoreDNS](https://coredns.io/) provides internal DNS
  + Some testapps (applied using -e testapps=true) can be deployed with gateway-api enabled:
    + **headlamp**: One of the replacements for the [dashboard](https://github.com/kubernetes/dashboard) project.
      + `headlamp.{{cluster_vars.dns_domain}}`
      + Get the token using `kubectl create token headlamp`
    + **nginx-test**: just a simple nginx webserver that echoes the host it is running on.
      + `curl nginx-test.{{cluster_vars.dns_domain}}`
    + **pyechoserver**:  A simple python web server that returns the ip address and host it is on (not really an echo server!).
      + `curl pyechoserver.{{cluster_vars.dns_domain}}`
    + **tcpecho**: A TCP echo server.  
      + `nc tcpecho.{{cluster_vars.dns_domain}} 3495` will echo back what you type.

It supports (at present) AWS, libvirt(KVM/Qemu) and ESXi infrastructure.  

This project is designed to operate using [**clusterverse**](https://github.com/clusterverse/clusterverse) to manage the base infrastructure.  Please see the [README.md](https://github.com/clusterverse/clusterverse/blob/master/README.md) there for detailed instructions on its usage.

## Requirements / Compatibility
+ Tested on Ubuntu 24,04 
+ ansible-core >= 2.17.4 (pypi >= 10.4.0)
+ See [docs/EXAMPLE/Dockerfile](https://github.com/clusterverse/clusterverse/blob/master/docs/EXAMPLE/Dockerfile) for a full list of dependencies.


## Example
Please see the [EXAMPLE](https://github.com/clusterverse/fluentd/tree/master/EXAMPLE) directory in this repository for some basic configuration.  This can be copied in the root directory, and used as a starting point for your own configuration.

### Configuration
Clusters are defined as code within Ansible yaml files that are imported at runtime.  Because clusters are built from scratch on the localhost, the automatic Ansible `group_vars` inclusion cannot work with anything except the special `all.yml` group (actual `groups` need to be in the inventory, which cannot exist until the cluster is built).  The `group_vars/all.yml` file is instead used to bootstrap _merge_vars_, and the definitions are hierarchically defined in [cluster_defs](https://github.com/clusterverse/kubernetes-essentials/tree/master/EXAMPLE/cluster_defs).  Please see the full documentation in the main [clusterverse/README.md](https://github.com/clusterverse/clusterverse/blob/master/README.md#cluster-definition-variables)
+ Cluster configuration is stored in `cluster_defs/**/cluster_vars[*].yml` files.
+ Application configuration is stored in `cluster_defs/**/app_vars[*].yml` files.


### Invocation

_**For full clusterverse invocation examples and command-line arguments, please see the [example README.md](https://github.com/clusterverse/clusterverse/blob/master/EXAMPLE/README.md)**_

The role is designed to run in two modes:
#### Deploy (also performs _up-scaling_ and _repairs_)
+ A playbook based on the [deploy.yml example](https://github.com/clusterverse/clusterverse/tree/master/EXAMPLE/deploy.yml) will be needed.
+ The `deploy.yml` sub-role idempotently deploys a cluster from the config defined above (if it is run again (with no changes to variables), it will do nothing).  If the cluster variables are changed (e.g. add a host), the cluster will reflect the new variables (e.g. a new host will be added to the cluster.  Note: it _will not remove_ nodes, nor, usually, will it reflect changes to disk volumes - these are limitations of the underlying cloud modules).
+ Example:
```
    ansible-playbook deploy.yml -e cloud_type=libvirt -e region=dougalab -e buildenv=dev -e testapps=true
```

#### Redeploy
+ A playbook based on the [redeploy.yml example](https://github.com/clusterverse/clusterverse/tree/master/EXAMPLE/redeploy.yml) will be needed.
+ The `redeploy.yml` sub-role will completely redeploy the cluster; this is useful for example to upgrade the underlying operating system version.
+ Please see the full [documentation](#https://github.com/clusterverse/clusterverse#redeploy)
+ Example:
```
    ansible-playbook redeploy.yml -e canary=none -e cloud_type=esxifree -e clusterid=dougakube -e region=dougalab -e buildenv=dev -e testapps=true
```
