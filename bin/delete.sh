#!/bin/bash 
# shellcheck disable=SC1091

set -o errexit
set -o pipefail
set -o nounset
set +o xtrace

############################################################################
# The script deletes a datacenter on AWS.
# The script uses AWS boto3 library to make AWS requests.
# You must have both AWS IAM user credentials and an AWS Region set in order to make requests.
#
# run:
#
# export AWS_ACCESS_KEY_ID=xxxxxx
# export AWS_SECRET_ACCESS_KEY=yyyyyy
# export AWS_DEFAULT_REGION=zzzzzz
#
# ./delete.sh
#
############################################################################

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
export DATACENTER_DIR
DATACENTER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && cd .. && pwd)"
export PYTHONPATH="${DATACENTER_DIR}"/project/src

{
    python -m venv "${DATACENTER_DIR}"/.venv
    source "${DATACENTER_DIR}"/.venv/bin/activate
    python3 -m pip install -r "${DATACENTER_DIR}"/requirements.txt
} > /dev/null

# delete vpc, instance, security groups, ...
python "${DATACENTER_DIR}/project/src/com/maxmin/aws/shutdown.py" "${DATACENTER_DIR}/config/datacenter.json" "${DATACENTER_DIR}/config/hostedzone.json" 
