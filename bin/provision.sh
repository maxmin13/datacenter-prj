#!/bin/bash 
# shellcheck disable=SC1091

set -o errexit
set -o pipefail
set -o nounset
set +o xtrace

#########################################################################
## The script provisions an AWS datacenter using Ansible.
## Ansible connects to the instances with an SSH connection plugin.
## Ansible is configured to use the Dynamic inventory plugin aws_ec2 to create a dynamic 
## inventory of the AWS instances.
## see: ansible.cfg file
##
## run:
##
## AWS IAM user credentials
## export AWS_ACCESS_KEY_ID=xxxxxx
## export AWS_SECRET_ACCESS_KEY=yyyyyy
## export AWS_DEFAULT_REGION=zzzzzz
##
## ./provision.sh 
##
#########################################################################

# AWS IAM user credientials
if [[ ! -v AWS_ACCESS_KEY_ID ]]
then
  echo "ERROR: environment variable AWS_ACCESS_KEY_ID not set!"
  exit 1
fi

if [[ ! -v AWS_SECRET_ACCESS_KEY ]]
then
  echo "ERROR: environment variable AWS_SECRET_ACCESS_KEY not set!"
  exit 1
fi

if [[ ! -v AWS_DEFAULT_REGION ]]
then
  echo "ERROR: environment variable AWS_DEFAULT_REGION not set!"
  exit 1
fi

# directory where the datacenter project is downloaded from github
# see: name_dtc_box file
export DATACENTER_DIR
DATACENTER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && cd .. && pwd)"

echo "Creating local datacenter virtual environment ..."

{
    python -m venv "${DATACENTER_DIR}"/.venv
    source "${DATACENTER_DIR}"/.venv/bin/activate
    python3 -m pip install -r "${DATACENTER_DIR}"/requirements.txt
    deactivate
} > /dev/null

echo "Local datacenter virtual environment created."

ANSIBLE_PLAYBOOK_CMD="${DATACENTER_DIR}"/.venv/bin/ansible-playbook

cd "${DATACENTER_DIR}"/provision || exit

########################
##### UPDATE SYSTEM ####
########################

echo "Upgrading instances ..."
 
"${ANSIBLE_PLAYBOOK_CMD}" playbooks/upgrade.yml 

##################
##### OPENSSL ####
##################

echo "Openssl ..."

"${ANSIBLE_PLAYBOOK_CMD}" playbooks/openssl.yml 

##################
##### DOCKER #####
##################

echo "Docker ..."

"${ANSIBLE_PLAYBOOK_CMD}" playbooks/docker.yml 

##################
### PHPMYADMIN ###
##################

echo "phpMyadmin ..."

"${ANSIBLE_PLAYBOOK_CMD}" playbooks/phpmyadmin.yml 

#################
##### PYTHON ####
#################

echo "Python ..."

"${ANSIBLE_PLAYBOOK_CMD}" playbooks/python.yml 

#####################
##### POSTGRESQL ####
#####################

echo "Postgresql ..."

"${ANSIBLE_PLAYBOOK_CMD}" playbooks/postgresql.yml 

################
##### NGINX ####
################

echo "Nginx ..."

"${ANSIBLE_PLAYBOOK_CMD}" playbooks/nginx.yml 

#################
##### JAVA ######
#################

echo "Java ..."

"${ANSIBLE_PLAYBOOK_CMD}" playbooks/java.yml 

###################
##### TOMCAT ######
###################

echo "Tomcat ..."

"${ANSIBLE_PLAYBOOK_CMD}" playbooks/tomcat.yml 

###################
##### MARIADB ######
###################

echo "MariaDB ..."

"${ANSIBLE_PLAYBOOK_CMD}" playbooks/mariadb.yml 

