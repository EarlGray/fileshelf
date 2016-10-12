from __future__ import print_function

import os
import stat
from base64 import decodestring as b64decode

import flask
from flask import Flask
from werkzeug.utils import secure_filename

import doh.url as url
from doh.rproxy import ReverseProxied


def default_conf(appdir):
    return {
        'host': '127.0.0.1',
        'port': 5000,
        'rooturl': '/',
        'debug': False,
        'application_dir': appdir,
        'storage_dir': os.path.join(appdir, 'storage'),
        'static_dir': os.path.join(appdir, 'static')
    }


class DohApp:
    def __init__(self, conf):
        template_dir = conf.get('template_dir', '../templates')

        app = Flask(__name__, template_folder=template_dir)

        app.debug = conf['debug']
        app.storage_dir = conf['storage_dir']
        app.static_folder = conf['static_dir']

        # monkey-patch the environment to handle 'X-Forwarder-For'
        # 'X-Forwarded-Proto', etc:
        app.wsgi_app = ReverseProxied(app.wsgi_app)

        self.conf = conf

        @app.route(url.my, defaults={'path': ''}, methods=['GET', 'POST'])
        @app.route(url.join(url.my, '<path:path>'), methods=['GET', 'POST'])
        def path_handler(path):
            req = flask.request

            dpath = os.path.join(app.storage_dir, path)
            auth = req.headers.get('Authorization')
            user = ''
            if auth and auth.startswith('Basic '):
                user = 'by user=%s' % b64decode(auth.split()[1]).split(':')[0]
            print('#### %s %s %s => <%s>' % (req.method, path, user, dpath))

            if req.method == 'POST':
                if 'file' not in req.files:
                    args = {'title': 'server error', 'e': 'no file'}
                    return flask.render_template('500.htm', **args), 400

                redir_url = flask.url_for('path_handler', path=path)

                f = req.files['file']
                fpath = os.path.join(app.storage_dir, path,
                                     secure_filename(f.filename))
                print('Saving file as %s' % fpath)
                try:
                    f.save(fpath)
                except OSError as e:
                    args = {'title': 'saving error', 'e': e}
                    return flask.render_template('500.htm', **args), 500
                print('Success, redirecting back to %s' % redir_url)
                return flask.redirect(redir_url)

            if not os.path.exists(dpath):
                return flask.render_template('404.htm', title='not found'), 404

            if not os.path.isdir(dpath):
                # TODO: for large files, redirect to nginx-served address
                return flask.send_file(dpath)

            lsdir = []
            try:
                for fname in os.listdir(dpath):
                    st = os.lstat(os.path.join(dpath, fname))
                    href = flask.url_for('path_handler',
                                         path=url.join(path, fname))
                    lsdir.append({
                        'name': fname,
                        'href': href,
                        'size': st.st_size,
                        'isdir': stat.S_ISDIR(st.st_mode)
                    })
                templvars = {
                    'path': path,
                    'lsdir': sorted(lsdir,
                                    key=lambda d: (not d['isdir'], d['name'])),
                    'path_prefixes': url.prefixes(path),
                    'title': path
                }
                return flask.render_template('dir.htm', **templvars)
            except OSError:
                args = {'path': path, 'title': 'no ' + path}
                return flask.render_template('404.htm', **args), 404

        @app.route('/res/<path:path>')
        def static_handler(path):
            fname = secure_filename(path)
            fname = os.path.join(app.static_dir, fname)
            if not os.path.exists(fname):
                args = {'path': path, 'title': 'no ' + path}
                return flask.render_template('404.htm', **args), 404

            # print('Serving %s' % fname)
            return flask.send_file(fname)

        @app.route('/')
        def home_handler():
            return flask.redirect(flask.url_for('path_handler')), 302

        @app.errorhandler(404)
        def not_found(e):
            return flask.render_template('404.htm', title='not found'), 404

        @app.errorhandler(500)
        def internal_error(e):
            args = {'title': 'server error', 'e': e}
            return flask.render_template('500.htm', **args), 500

        self.app = app

    def run(self):
        self.app.run(host=self.conf['host'], port=self.conf['port'])
