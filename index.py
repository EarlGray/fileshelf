#!/usr/bin/env python3

import sys

from fileshelf import DohApp, config

if __name__ == '__main__':
    from pathlib import Path
    p = Path(sys.argv[0]).expanduser().absolute()
    appdir = p.parent.as_posix()

    conf = config.from_arguments(appdir)

    if not conf.get('multiuser'):
        print("Serving:", conf['storage_dir'], file=sys.stderr)

    app = DohApp(conf)
    app.run()
