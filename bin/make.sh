
# shellcheck disable=SC1091

## python 3.11

set -o errexit
set -o pipefail
set -o nounset
set +o xtrace
  
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && cd .. && pwd)"
export PYTHONPATH="${PROJECT_DIR}"/src
python -m venv ${PROJECT_DIR}/.venv
source "${PROJECT_DIR}"/.venv/bin/activate
python3 -m pip install -r "${PROJECT_DIR}"/requirements.txt

# create vpc, instance, security groups, ...
python "${PROJECT_DIR}/src/com/maxmin/aws/startup.py" "${PROJECT_DIR}/config/datacenter.json" "${PROJECT_DIR}/config/dns.json"

deactivate
