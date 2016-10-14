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
        'static_dir': os.path.join(appdir, 'static'),
        'share_dir': os.path.join(appdir, 'share')
    }


class DohApp:
    def __init__(self, conf):
        template_dir = conf.get('template_dir', '../templates')

        app = Flask(__name__, template_folder=template_dir)

        app.debug = conf['debug']
        app.storage_dir = conf['storage_dir']
        app.static_dir = conf['static_dir']
        app.share_dir = conf['share_dir']
        self.shared = self._scan_share(app.share_dir)

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
                print(req.form)
                action = req.form['action']
                if action == 'upload':
                    if 'file' not in req.files:
                        args = {'title': 'server error', 'e': 'no file'}
                        return flask.render_template('500.htm', **args), 400

                    return self._upload(req, path)
                if action == 'share':
                    return self._share(dpath, path)

                return flask.Response('unknown action %s' % action), 400

            if not os.path.exists(dpath):
                return flask.render_template('404.htm', title='not found'), 404

            if not os.path.isdir(dpath):
                # TODO: for large files, redirect to nginx-served address
                return flask.send_file(dpath)

            return self._render_dir(dpath, path)

        @app.route(url.join(url.res, '<path:path>'))
        def static_handler(path):
            fname = secure_filename(path)
            fname = os.path.join(app.static_dir, fname)
            if not os.path.exists(fname):
                args = {'path': path, 'title': 'no ' + path}
                return flask.render_template('404.htm', **args), 404

            # print('Serving %s' % fname)
            return flask.send_file(fname)

        @app.route(url.join(url.pub, '<path:path>'))
        def pub_handler(path):
            fname = secure_filename(path)
            fname = os.path.join(app.share_dir, fname)
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


    def _scan_share(self, share_dir):
        share = {}
        for link in os.listdir(share_dir):
            lpath = os.path.join(share_dir, link)
            if not os.path.islink(lpath): continue

            source = os.readlink(lpath)
            print('share: %s => %s' % (link, source))
            share[source] = link
        return share

    def _render_dir(self, dpath, path):
        lsdir = []
        try:
            for fname in os.listdir(dpath):
                fpath = os.path.join(dpath, fname)
                st = os.lstat(fpath)
                href = flask.url_for('path_handler',
                                     path=url.join(path, fname))
                shared = self.shared.get(fpath)
                if shared:
                    shared = flask.url_for('pub_handler', path=shared)
                # print('dpath=%s, shared=%s' % (fpath, shared))
                lsdir.append({
                    'name': fname,
                    'href': href,
                    'size': st.st_size,
                    'shared': shared,
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

    def _upload(self, req, path):
        redir_url = flask.url_for('path_handler', path=path)

        f = req.files['file']
        fpath = os.path.join(self.app.storage_dir, path,
                             secure_filename(f.filename))
        print('Saving file as %s' % fpath)
        try:
            f.save(fpath)
        except OSError as e:
            args = {'title': 'saving error', 'e': e}
            return flask.render_template('500.htm', **args), 500
        print('Success, redirecting back to %s' % redir_url)
        return flask.redirect(redir_url)

    def _share(self, dpath, path):
        req = flask.request
        try:
            fname = req.form.get('file')
            if not fname:
                return flask.render_template('400.htm'), 400
            fname = secure_filename(fname)
            fpath = os.path.join(dpath, fname)
            link = os.path.join(self.app.share_dir, fname)
            # TODO: check if already shared
            # TODO: check for existing links
            os.symlink(fpath, link)
            self.shared[fname] = fpath
            print('shared:', fname, ' => ', fpath)
            return flask.redirect(flask.url_for('path_handler', path=path))
        except OSError as e:
            return flask.render_template('500.htm', e=e), 500
