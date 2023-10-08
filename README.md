# AWS Ansible project

The project creates a datacenter in the AWS cloud.</br>
Python is used to create the the AWS objects (VPC, subnets, security groups, instances and DNS records, see src/ folder),</br>
Ansible scripts to provision the instances.

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

edit: constants.py
set PROJECT_DIR=<path to the datacenter-prj directory>

**Create the AWS datacenter with instances, subnets, security groups and DNS records:**

```
cd bin
./make.sh

```

**Create a virtual environment with python version 3.11:**

```
cd datacenter-prj
python3 -m venv ".venv"
source .venv/bin/activate
pip install -r requirements.txt
```


**Upgrade all the instances and install some basic programs:**

```
cd provision
ansible-playbook -b -K playbooks/upgrade.yml
```

**Install OpenSSL 1.1.1:**

```
cd provision
ansible-playbook -b -K playbooks/openssl.yml
```

**Install Python 3.11.4:** 

```
cd provision
ansible-playbook -b -K playbooks/python.yml
```

**Install nginx web server:**

```
cd provision
ansible-playbook -b -K playbooks/nginx.yml
```

**Postgresql database instance:**

```
cd provision
ansible-playbook -b -K playbooks/postgresql.yml
```


**Delete the AWS datacenter:**

```
cd bin
./delete.sh
```

<br>
