import json

import sys
import os.path

import doh
from doh import DohApp

if __name__ == '__main__':
    conf = doh.default_conf(os.getcwd())
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            uconf = json.load(f)
            conf.update(uconf)

    app = DohApp(conf)
    app.run()
