# AWS datacenter project

The project creates a datacenter in the AWS cloud.</br>
The datacenter consists of a VPC, a subnet, one security group, one Linux 2 instance with a DNS record associated.

**Requirements:**

- Fedora 38
- Python 3.11
- ansible 2.14.5

**Configure the AWS credentials and default region on the controller machine:**

```
aws configure
```

**Clone the project:**

git clone git@github.com:maxmin13/datacenter-prj.git

**Configure the project:**

edit datacenter.json and dns.json and set the Vpc and DNS values accourding to your AWS account: <br>
vpc cidr, region", availability zone, instance private IP, DNS registered domain.


**Create the AWS datacenter with instances, subnets, security groups and DNS records:**

```
cd bin
./make.sh

```

**Delete the datacenter:**

```
cd bin
./delete.sh
```

<br>
