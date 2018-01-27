#!/bin/sh

set -e

cd "`dirname $0`"

if which virtualenv >/dev/null ; then
  if ! test -d ./v3nv ; then
    virtualenv -p python3 v3nv
    ./v3nv/bin/pip install -r requirements.txt
  fi
  . ./v3nv/bin/activate
else
  echo "WARN: virtualenv not found, trying to use system libraries..." >&2
fi

exec ./index.py "$@"
