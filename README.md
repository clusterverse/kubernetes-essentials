# kubernetes-essentials

An Ansible role to deploy the essentials of a highly available Kubernetes cluster. Includes in-cluster apiserver and ingress controller loadbalancing, dns and flannel.

It was originally loosely based on the [kelseyhightower/kubernetes-the-hard-way](https://github.com/kelseyhightower/kubernetes-the-hard-way) runbooks, but this version is completely Ansible-ised, and not GCP-specific.
+ In common, it downloads and runs the controller componenets (apiserver, controller-manager and scheduler) _outside_ the cluster as systemd services.  Similarly, for kubelets on the worker nodes.  
+ However:
  + etcd runs in separate VMs
  + The apiserver nodes are load-balanced using cloud-specific tools:
    + **Libvirt** / **ESXi**: keepalived (with IPVS real-servers on the same hosts as the directors).  This means the host that is owner of the VIP receives the request, but hands it off in the kernel for processing by one of the apiservers.
    + **AWS**: Network load balancers, configured for internal load-balancing.  One per-zone for resilience.
  + [haproxy-ingress](https://haproxy-ingress.github.io/) is used as an ingress controller (using the [Gateway API](https://haproxy-ingress.github.io/docs/configuration/gateway-api/)).  It runs as a daemonset on special _node-edge_ worker nodes with hostNetwork.

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

### AWS
+ VPC and subnets configured
+ IAM role with access/secret key.
+ Route53 private Hosted zone (it probably could be run publicly, by setting `cluster_vars.assign_public_ip: true` and `cluster_vars.assign_public_ip: public`, but this would be highly insecure.
  + DNS is mandatory, because the NLBs do not provide a globally unique IP, and the APIservers need a load-balancer with either a single IP or a DNS name.

### libvirt (Qemu)
+ It is non-trivial to set up username/password access to a remote libvirt host, so we use an ssh key instead.
+ Your ssh user should be a member of the `libvirt` and `kvm` groups.
+ Store the config in `cluster_vars.libvirt`

### ESXi
+ Username & password for a privileged user on an ESXi host
+ SSH must be enabled on the host
+ Set the `Config.HostAgent.vmacore.soap.maxSessionCount` variable to 0 to allow many concurrent tests to run.   
+ Set the `Security.SshSessionLimit` variable to max (100) to allow as many ssh sessions as possible.   
+ You need a template VM.  [gold-img-build-esxi](https://github.com/dseeley/gold-img-build-esxi) can be used if needed.
+ DNS is optional.  If set, you will need a DNS server of either nsupdate (bind9), AWS route53 or GCP CloudDNS.
+ Store the config in `cluster_vars.esxi` 


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
