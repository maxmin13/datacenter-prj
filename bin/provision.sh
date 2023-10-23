#!/bin/bash 
# shellcheck disable=SC1091

set -o errexit
set -o pipefail
set -o nounset
set +o xtrace

#########################################################################
## Provisions an AWS datacenter.
##
## run:
##
## export REMOTE_USER=<remote instance user, eg: awsadmin>
## export REMOTE_USER_PASSWORD=<remote instance user pwd, eg: awsadmin>
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

WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && cd ../.. && pwd)"
export DATACENTER_PROJECT_DIR="${WORKSPACE_DIR}"/datacenter-prj

ANSIBLE_PLAYBOOK_CMD="${DATACENTER_PROJECT_DIR}"/.venv/bin/ansible-playbook

########################
##### UPDATE SYSTEM ####
########################

echo "Upgrading instance ..."

cd "${DATACENTER_PROJECT_DIR}"/provision || exit

"${ANSIBLE_PLAYBOOK_CMD}" playbooks/upgrade.yml \
    --extra-vars "ansible_user=${REMOTE_USER} ansible_password=${REMOTE_USER_PASSWORD} ansible_sudo_pass=${REMOTE_USER_PASSWORD}"

echo "Instance upgraded."

##################
##### OPENSSL ####
##################

echo "Upgrading Openssl ..."

"${ANSIBLE_PLAYBOOK_CMD}" playbooks/openssl.yml --extra-vars "ansible_user=${REMOTE_USER} \
    ansible_password=${REMOTE_USER_PASSWORD} ansible_sudo_pass=${REMOTE_USER_PASSWORD}"

echo "Openssl upgraded."

#################
##### PYTHON ####
#################

echo "Installing new Python version ..."

"${ANSIBLE_PLAYBOOK_CMD}" playbooks/python.yml \
    --extra-vars "ansible_user=${REMOTE_USER} ansible_password=${REMOTE_USER_PASSWORD} ansible_sudo_pass=${REMOTE_USER_PASSWORD}"

echo "Python installed."

#####################
##### POSTGRESQL ####
#####################

echo "Installing Postgresql ..."

"${ANSIBLE_PLAYBOOK_CMD}" playbooks/postgresql.yml \
    --extra-vars "ansible_user=${REMOTE_USER} ansible_password=${REMOTE_USER_PASSWORD} ansible_sudo_pass=${REMOTE_USER_PASSWORD}"

echo "Postgresql installed."

################
##### NGINX ####
################

echo "Installing Nginx ..."

"${ANSIBLE_PLAYBOOK_CMD}" playbooks/nginx.yml \
    --extra-vars "ansible_user=${REMOTE_USER} ansible_password=${REMOTE_USER_PASSWORD} ansible_sudo_pass=${REMOTE_USER_PASSWORD}"

echo "Nginx installed."
echo "Datacenter provisioned."
