
# shellcheck disable=SC1091

## python 3.11

set -o errexit
set -o pipefail
set -o nounset
set +o xtrace
  
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && cd .. && pwd)"
export PYTHONPATH="${PROJECT_DIR}/src"
source "${PROJECT_DIR}"/.venv/bin/activate

python "${PROJECT_DIR}/src/com/maxmin/aws/startup.py" "${PROJECT_DIR}/config/cms_datacenter.json" 
