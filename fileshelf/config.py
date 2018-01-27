import os
import sys
import json

from pathlib import Path
from argparse import ArgumentParser


def default(appdir):
    return {
        # host and port to listen on:
        'host': '127.0.0.1',
        'port': 8021,

        # modes:
        'debug': False,

        # directories:
        'app_dir': appdir,
        'data_dir': os.path.join(appdir, 'data'),        # multiple-users storage
        'storage_dir': os.path.join(appdir, 'storage'),  # single-user storage
        'static_dir': os.path.join(appdir, 'static'),
        'template_dir': os.path.join(appdir, 'tmpl'),

        # users:
        'multiuser': False,
        'auth': None,           # null, 'basic'
        'auth_realm': None,     # basic auth realm, e.g. "fs.mydomain.tld"
        'auth_htpasswd': None,  # data/htpasswd.db by default
        'auth_https_only': False,

        # used to offload large static files to a static server (nginx):
        'offload_dir': None,
        'offload_path': None,
    }


def from_arguments(appdir=None):
    conf = default(appdir or os.getcwd())

    ap = ArgumentParser()
    ap.add_argument("-c", "--config",
        help="path to a configuration file")
    ap.add_argument("-p", "--port", type=int,
        help="port to listen on")
    ap.add_argument("-d", "--debug", action="store_true",
        help="debug output")
    ap.add_argument("directory", nargs='?',
        help="directory to serve")

    args = ap.parse_args()

    if args.config:
        with open(args.config) as f:
            uconf = json.load(f)
            conf.update(uconf)

    # override config if options are specified:
    if args.directory:
        if Path(args.directory).expanduser().absolute().exists():
            conf['storage_dir'] = args.directory
        else:
            print("Directory not found: %s" % args.directory, file=sys.stderr)
            sys.exit(1)

    if args.port and 0 < args.port and args.port < 65536:
            conf['port'] = args.port

    if args.debug:
        conf['debug'] = True

    return conf
