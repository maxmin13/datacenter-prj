#!/bin/bash

# shellcheck disable=SC1091

## python 3.11

set -o errexit
set -o pipefail
set -o nounset
set +o xtrace
  
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && cd ../.. && pwd)"

echo $PROJECT_DIR

export PYTHONPATH="${PROJECT_DIR}/project/src"
source "${PROJECT_DIR}"/.venv/bin/activate

cd "${PROJECT_DIR}"/project/tests
pytest -s
