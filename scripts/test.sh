#!/bin/bash
# Run API tests
cd "$(dirname "$0")/../apps/api"
pip install -r reqs.txt
pytest test_api.py -v
