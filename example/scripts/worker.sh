#!/bin/bash
pip3 install -q -e /crawlers

# For debugging inside a container, attach a terming and try:
# python3 /tmp/debugpy --wait-for-client --listen 0.0.0.0:5678 memorious/cli.py --debug run book_scraper
pip3 install debugpy -t /tmp
/bin/bash