#!/bin/sh

set -e

export APPDIR="`dirname $0`"

if which virtualenv >/dev/null ; then
  if ! test -d $APPDIR/v3nv ; then
    virtualenv -p python3 $APPDIR/v3nv
    $APPDIR/v3nv/bin/pip install -r $APPDIR/requirements.txt
  fi
  . $APPDIR/v3nv/bin/activate
else
  echo "WARN: virtualenv not found, trying to use system libraries..." >&2
fi

exec $APPDIR/index.py "$@"
