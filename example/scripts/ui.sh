#!/bin/bash
pip3 install -q -e /crawlers
gunicorn --reload -t 900 -w 4 -b 0.0.0.0:8000 --log-level info --log-file - memorious.ui.views:app