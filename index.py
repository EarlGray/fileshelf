#!/usr/bin/env python3

import sys

from fileshelf import DohApp, config

if __name__ == '__main__':
    conf = config.from_arguments()

    app = DohApp(conf)
    app.run()
