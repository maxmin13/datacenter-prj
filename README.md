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

edit datacenter.json and hostedzone.json and set the Vpc and DNS values accourding to your AWS account: <br>
vpc cidr, region", availability zone, instance private IP, DNS registered domain.


**Create AWS datacenter and DNS record:**

```
cd bin
./make.sh

```

**Upgrade all the instances and istall some basic programs:**

```
cd provision
ansible-playbook -b -K playbooks/upgrade.yml
```

**Install OpenSSL 1.1.1:**

```
ansible-playbook -b -K playbooks/openssl.yml
```

**Install Python 3.11.4:**

```
ansible-playbook -b -K playbooks/python.yml
```

**Install nginx web server:**

```
ansible-playbook -b -K playbooks/nginx.yml
```

**Install Postgresql database:**

```
ansible-playbook -b -K playbooks/postgresql.yml
```

**Delete the datacenter:**

```
cd bin
./delete.sh
```

**Connect to the instance:**

```
cd access
rm -f ~/.ssh/known_hosts && ssh -v -i admin-key -p 22 awsadmin@<instance-public-ip>
```

<br>
