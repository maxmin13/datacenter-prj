# AWS datacenter project

The project creates a datacenter in the AWS cloud.</br>
The datacenter consists of a VPC, a subnet, one security group, one Linux 2 instance with a DNS record associated.

**Requirements:**

- Fedora 38
- Python 3.11.4
- ansible 2.14.5
- aws-cli/2.13.0

**Clone the project:**

git clone git@github.com:maxmin13/datacenter-prj.git

**Configure the AWS credentials and default region on the controller machine:**

```
aws configure
```

**Configure the project:**

edit **datacenter.json** and **hostedzone.json** and set the Vpc and DNS values accourding to your AWS account: <br>

* VPC CIDR (eg: "Cidr": "10.0.0.0/16")<br>
* VPC region (eg: "Region": "eu-west-1")<br>
* Availability zone (eg: "Az": "eu-west-1a")<br>
* Subnet CIDR (eg: "Cidr": "10.0.20.0/24")<br>
* admin instance private IP (eg: "PrivateIp": "10.0.20.35")<br>
* DNS registered domain (your domain registered with the AWS registrar, eg: "RegisteredDomain": "maxmin.it")<br>


**Create AWS datacenter and DNS record:**

```
cd bin
sudo chmod -R -x  *.sh 
./make.sh

```

**Upgrade Openssl, install Python, Postgresql, Nginx:**

```
export REMOTE_USER=<remote instance user, eg: awsadmin>
export REMOTE_USER_PASSWORD=<remote instance user pwd, eg: awsadmin>

cd bin

./provision.sh

```

**Delete the datacenter:**

```
cd bin
./delete.sh
```

**Log in the remote instance:**

```
cd access
rm -f ~/.ssh/known_hosts && ssh -v -i admin-key -p 22 awsadmin@<remote instance IP address>

```

<br>
