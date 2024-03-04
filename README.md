# AWS datacenter project

The project creates a datacenter in the AWS cloud.</br>
The datacenter consists of a VPC, a subnet, one security group, one Linux 2 instance with a DNS record associated.</br>
The creation of the VPC is done with Python boto3 AWS development kit.</br>
Ansible scripts update OpenSSL to version 1.1.1u, install Python 3.11.4, Postgresql server, Nginx with a demo page.</br>

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

edit **config/datacenter.json** and **config/hostedzone.json** and set the Vpc and DNS values accourding to your AWS account: <br>

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
export REMOTE_USER=<remote AWS instance user, eg: awsadmin>
export REMOTE_USER_PASSWORD=<remote AWS instance user pwd, eg: awsadmin>

cd bin

./provision.sh

```

**Delete the datacenter:**

```
cd bin
./delete.sh
```

**Log in the remote AWS instance:**

```
cd datacenter-prj/access
rm -f ~/.ssh/known_hosts && ssh -v -i admin-box -p 22 awsadmin@<remote AWS instance IP address>
rm -f ~/.ssh/known_hosts && ssh -v -i admin-box -p 22 admin.maxmin.it

```

**Access the test web site:**
<br><br>
*http://admin.maxmin.it:8080/index.html*
<br>
*https://admin.maxmin.it:8443/index.html*

**Connect to the database server:**

```
// Install postgreSQL version 4 or above

psql -h admin.maxmin.it -p 5432 -U postgres postgresdb

#### check all currently active users:

\du

#### exit:	

\q
```

<br>
