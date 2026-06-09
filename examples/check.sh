#!/usr/bin/env bash
# Check an output against the donkeys. Same text -> same verdict, every time.
curl -s https://api.doloop.io/v1/check \
  -H 'content-type: application/json' \
  -d '{"text": "It is worth noting that, in many ways, this is slop."}'
