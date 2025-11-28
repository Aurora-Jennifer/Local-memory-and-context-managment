#!/bin/bash
PROJECT="$1"
shift
python3 ~/.contextai/src/context_engine.py "$PROJECT" "$@" 
