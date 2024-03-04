#!/bin/bash 
# shellcheck disable=SC1091

set -o errexit
set -o pipefail
set -o nounset
set +o xtrace

############################################################################
# The script makes a datacenter on AWS.
# Python Boto3 SDK is used to create the AWS datacener.
# Boto3 SDK uses the locally installed AWS cli to get AWS credentials. 
#
# run:
#    ./make.sh
#
############################################################################
  
export DATACENTER_PROJECT_DIR
DATACENTER_PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && cd .. && pwd)"
export PYTHONPATH="${DATACENTER_PROJECT_DIR}"/project/src

{
    python -m venv "${DATACENTER_PROJECT_DIR}"/.venv
    source "${DATACENTER_PROJECT_DIR}"/.venv/bin/activate
    python3 -m pip install -r "${DATACENTER_PROJECT_DIR}"/requirements.txt
} > /dev/null

# make vpc, instance, security groups, ...
python "${DATACENTER_PROJECT_DIR}/project/src/com/maxmin/aws/startup.py" "${DATACENTER_PROJECT_DIR}/config/datacenter.json" "${DATACENTER_PROJECT_DIR}/config/hostedzone.json" 
