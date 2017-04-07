from __future__ import print_function

import os.path
import flask

import fileshelf.url as url


class Handler:
    # content priority
    DOESNT = 0
    CAN = 1
    SHOULD = 2
    MUST = 3

    def __init__(self, name, conf):
        """
        `name` is the name of this plugin and its directory
        `extensions` is
            - `None`;
            - a map from extensions to priority (0-3):
                e.g. `Handler('epub', extensions={'epub': 3})`
        """
        self.name = name
        self.conf = conf

    def can_handle(self, storage, path):
        """
        should return one of:
        Handler.DOESNT, Handler.CAN, Handler.SHOULD, Handler.MUST
        """
        _, ext = os.path.splitext(path)
        ext = ext.strip('.')
        # self._log('Handler.can_handle .' + ext)

        extensions = self.conf.get('extensions')
        if extensions and ext in extensions:
            return extensions[ext]
        return Handler.DOESNT

    def render(self, req, storage, path):
        """ handles GET requests """
        self._log('Handler.render(%s)' % path)

        tmpl = url.join(self.name, 'index.htm')
        self._log('rendering ' + tmpl)
        args = {
            'file_url': url.my(path),
            'user': getattr(flask.request, 'user'),
            'path_prefixes': url.prefixes(path, storage.exists)
        }
        return flask.render_template(tmpl, **args)

    def action(self, req, storage, path):
        """ handles POST requests, to override """
        raise NotImplementedError('Handler.action')

    def _log(self, *msgs):
        print('## Plugin[%s]: ' % self.name, end='')
        print(*msgs)
