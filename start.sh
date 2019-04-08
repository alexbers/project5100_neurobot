#!/bin/sh

export PYTHONUNBUFFERED=1
exec gunicorn -w 2 neurobot_srv:app -b 0.0.0.0:10001 -u neurobot -g neurobot --capture-output --timeout=20
