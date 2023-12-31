#!/bin/bash 

# shellcheck disable=SC1091

############################################################################
# The script creates a datacenter on AWS.
#
# run:
#    ./make.sh
#
############################################################################

set -o errexit
set -o pipefail
set -o nounset
set +o xtrace
  
export DATACENTER_PROJECT_DIR
DATACENTER_PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && cd .. && pwd)"
export PYTHONPATH="${DATACENTER_PROJECT_DIR}"/src

{
    python -m venv "${DATACENTER_PROJECT_DIR}"/.venv
    source "${DATACENTER_PROJECT_DIR}"/.venv/bin/activate
    python3 -m pip install -r "${DATACENTER_PROJECT_DIR}"/requirements.txt
} > /dev/null

echo "Datacenter virtual environment created."

# create vpc, instance, security groups, ...
python "${DATACENTER_PROJECT_DIR}/src/com/maxmin/aws/startup.py" "${DATACENTER_PROJECT_DIR}/config/datacenter.json" "${DATACENTER_PROJECT_DIR}/config/hostedzone.json"

echo "Datacenter created."
