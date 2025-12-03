#!/usr/bin/env bash
set -euo pipefail

# Start gateway and trainer in separate terminals in practice. This script shows the sequence you should record.

echo "Killing trainer (if running)"
pkill -f training_server.py || true
sleep 1

echo "Start trainer"
python backend/training/training_server.py &
TPID=$!
sleep 2

# Simulate latency
curl -s -X POST http://localhost:8000/rpc -H 'Content-Type: application/json' -d '{"type":"delay","ms":400}' || true
sleep 2

# Pause and resume
curl -s -X POST http://localhost:8000/rpc -H 'Content-Type: application/json' -d '{"type":"pause"}' || true
sleep 2
curl -s -X POST http://localhost:8000/rpc -H 'Content-Type: application/json' -d '{"type":"resume"}' || true
sleep 2

# Crash trainer and show auto-reconnect on the dashboard
kill $TPID
sleep 3
python backend/training/training_server.py &