from __future__ import print_function

import os
import stat
import shutil
import mimetypes
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

        @app.errorhandler(404)
        def not_found(e):
            return self.r404()

        @app.errorhandler(500)
        def internal_error(e):
            return self.r500(e)

        @app.route('/')
        def home_handler():
            return flask.redirect(flask.url_for('path_handler')), 302

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
                        return self.r500('no file in POST')

                    return self._upload(req, path)
                if action == 'share':
                    return self._share(dpath, path)
                if action == 'rename':
                    oldname = req.form.get('oldname')
                    newname = req.form.get('newname')
                    return self._rename(path, oldname, newname)
                if action == 'delete':
                    fname = req.form.get('filename')
                    return self._delete(path, fname)

                return flask.Response('unknown action %s' % action), 400

            if not os.path.exists(dpath):
                return self.r404(path)

            if not os.path.isdir(dpath):
                # TODO: for large files, redirect to nginx-served address
                return flask.send_file(dpath)

            return self._render_dir(dpath, path)

        @app.route(url.join(url.res, '<path:path>'))
        def static_handler(path):
            fname = secure_filename(path)
            fname = os.path.join(app.static_dir, fname)
            if not os.path.exists(fname):
                return self.r404(path)

            # print('Serving %s' % fname)
            return flask.send_file(fname)

        @app.route(url.join(url.pub, '<path:path>'))
        def pub_handler(path):
            fname = secure_filename(path)
            fname = os.path.join(app.share_dir, fname)
            if not os.path.exists(fname):
                return self.r404(path)

            # print('Serving %s' % fname)
            return flask.send_file(fname)

        self.app = app

    def run(self):
        self.app.run(host=self.conf['host'], port=self.conf['port'])

    def r400(self, why):
        args = {'title': 'not accepted', 'e': why}
        return flask.render_template('500.htm', **args), 400

    def r404(self, path=None):
        args = {'path': path, 'title': 'no ' + path if path else 'not found'}
        return flask.render_template('404.htm', **args), 404

    def r500(self, e=None):
        args = {'title': 'server error', 'e': e}
        return flask.render_template('500.htm', **args), 500

    def _scan_share(self, share_dir):
        share = {}
        for link in os.listdir(share_dir):
            lpath = os.path.join(share_dir, link)
            if not os.path.islink(lpath):
                continue

            source = os.readlink(lpath)
            print('share: %s => %s' % (link, source))
            share[source] = link
        return share

    def _render_dir(self, dpath, path):
        rename_fname = flask.request.args.get('rename')
        lsdir = []
        try:
            for fname in os.listdir(dpath):
                fpath = os.path.join(dpath, fname)
                st = os.lstat(fpath)
                href = flask.url_for('path_handler',
                                     path=url.join(path, fname))
                shared = self.shared.get(fpath)
                mimetype = mimetypes.guess_type(fpath)
                # print('fpath=%s, shared=%s' % (fpath, shared))
                if shared:
                    shared = flask.url_for('pub_handler', path=shared)

                lsdir.append({
                    'name': fname,
                    'href': href,
                    'mime': mimetype[0] or '',
                    'size': st.st_size,
                    'shared': shared,
                    'isdir': stat.S_ISDIR(st.st_mode),
                    'rename_url': path + '?rename=' + fname
                })

            lsdir = sorted(lsdir, key=lambda d: (not d['isdir'], d['name']))
            templvars = {
                'path': path,
                'lsdir': lsdir,
                'path_prefixes': url.prefixes(path),
                'title': path,
                'rename': rename_fname
            }
            return flask.render_template('dir.htm', **templvars)
        except OSError:
            args = {'path': path, 'title': 'no ' + path}
            return flask.render_template('404.htm', **args), 404

    def _upload(self, req, path):
        redir_url = flask.url_for('path_handler', path=path)

        f = req.files['file']
        if not f.filename:
            return flask.redirect(redir_url)
        fpath = os.path.join(self.app.storage_dir, path,
                             secure_filename(f.filename))
        print('Saving file as %s' % fpath)
        try:
            f.save(fpath)
        except OSError as e:
            return self.r500(e)

        print('Success, redirecting back to %s' % redir_url)
        return flask.redirect(redir_url)

    def _share(self, dpath, path):
        req = flask.request
        try:
            fname = req.form.get('file')
            if not fname:
                return self.r400('no `file` in POST')

            fname = secure_filename(fname)
            fpath = os.path.join(dpath, fname)
            link = os.path.join(self.app.share_dir, fname)
            # TODO: check if already shared
            # TODO: check for existing links

            os.symlink(fpath, link)
            self.shared[fpath] = fname
            print('shared:', fpath, ' => ', fname)
            return flask.redirect(flask.url_for('path_handler', path=path))
        except OSError as e:
            return self.r500(e)

    def _rename(self, path, oldname, newname):
        old = os.path.join(self.app.storage_dir, path, oldname)
        new = os.path.join(self.app.storage_dir, path, newname)
        print("mv %s %s" % (old, new))
        try:
            shutil.move(old, new)
            return flask.redirect(flask.url_for('path_handler', path=path))
        except IOError as e:
            return self.r500(e)

    def _delete(self, path, fname):
        fname = os.path.join(self.app.storage_dir, path, fname)
        print("rm %s" % fname)
        try:
            os.remove(fname)
            return flask.redirect(flask.url_for('path_handler', path=path))
        except OSError as e:
            return self.r500(e)
