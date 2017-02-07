import json

import sys

from doh import DohApp

if __name__ == '__main__':
    conf = {}
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            uconf = json.load(f)
            conf.update(uconf)

    app = DohApp(conf)
    app.run()
