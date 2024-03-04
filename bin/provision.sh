#!/bin/bash 
# shellcheck disable=SC1091

set -o errexit
set -o pipefail
set -o nounset
set +o xtrace

#########################################################################
## The script creates and provisions a new AWS datacenter using Ansible.
## Ansible connects to the instances with SSH connection plugin.
## Ansible uses Dynamic inventory plugin aws_ec2 to create a dynamic 
## inventory of the AWS instances.
## see: ansible.cfg file, ransport=ssh, enable_plugins = aws_ec2
##
## run:
##
## export REMOTE_USER=<remote AWS instance user, eg: awsadmin>
## export REMOTE_USER_PASSWORD=<remote AWS instance user pwd, eg: awsadmin>
##
## ./provision.sh 
##
#########################################################################

if [[ ! -v REMOTE_USER ]]
then
  echo "ERROR: environment variable REMOTE_USER not set!"
  exit 1
fi

if [[ ! -v REMOTE_USER_PASSWORD ]]
then
  echo "ERROR: environment variable REMOTE_USER_PASSWORD not set!"
  exit 1
fi

export DATACENTER_PROJECT_DIR
DATACENTER_PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && cd .. && pwd)"

{
    python -m venv "${DATACENTER_PROJECT_DIR}"/.venv
    source "${DATACENTER_PROJECT_DIR}"/.venv/bin/activate
    python3 -m pip install -r "${DATACENTER_PROJECT_DIR}"/requirements.txt
} > /dev/null

ANSIBLE_PLAYBOOK_CMD="${DATACENTER_PROJECT_DIR}"/.venv/bin/ansible-playbook

cd "${DATACENTER_PROJECT_DIR}"/provision || exit

########################
##### UPDATE SYSTEM ####
########################

echo "Upgrading instances ..."

"${ANSIBLE_PLAYBOOK_CMD}" playbooks/upgrade.yml 

echo "Instances upgraded."

##################
##### OPENSSL ####
##################

echo "Upgrading Openssl ..."

"${ANSIBLE_PLAYBOOK_CMD}" playbooks/openssl.yml 

echo "Openssl upgraded."

#################
##### PYTHON ####
#################

echo "Installing new Python version ..."

"${ANSIBLE_PLAYBOOK_CMD}" playbooks/python.yml 

echo "Python installed."

#####################
##### POSTGRESQL ####
#####################

echo "Installing Postgresql ..."

"${ANSIBLE_PLAYBOOK_CMD}" playbooks/postgresql.yml 

echo "Postgresql installed."

################
##### NGINX ####
################

echo "Installing Nginx ..."

"${ANSIBLE_PLAYBOOK_CMD}" playbooks/nginx.yml 

echo "Nginx installed."

echo "Datacenter provisioned."
