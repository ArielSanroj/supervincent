#!/bin/bash
cd /Users/arielsanroj/supervincent
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
uvicorn src.api.app:app --host 0.0.0.0 --port 8010 --reload
