#!/bin/sh

set -e

APPDIR="$(dirname "$0")"
export APPDIR

if python3 -c "import virtualenv" >/dev/null ; then
  if ! test -d "$APPDIR/venv" ; then
    python3 -m virtualenv -p python3 "$APPDIR/venv"
    "$APPDIR/venv/bin/pip" install -r "$APPDIR/requirements.txt"
  fi
  . "$APPDIR/venv/bin/activate"
else
  echo "WARN: virtualenv not found, trying to use system libraries..." >&2
fi

exec "$APPDIR/index.py" "$@"
