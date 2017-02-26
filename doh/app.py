from __future__ import print_function

import os
import time
import uuid
from base64 import decodestring as b64decode
from collections import namedtuple

import flask
from flask import Flask
from werkzeug.utils import secure_filename

import doh.url as url
import doh.content as content
from doh.rproxy import ReverseProxied
from doh.storage import LocalStorage


def default_conf(appdir):
    return {
        # host and port to listen on:
        'host': '127.0.0.1',
        'port': 5000,

        # url prefix:
        'rooturl': '/',

        # modes:
        'debug': False,

        # directories:
        'app_dir': appdir,
        'storage_dir': os.path.join(appdir, 'storage'),
        'static_dir': os.path.join(appdir, 'static'),
        'data_dir': os.path.join(appdir, 'data'),

        # used to offload large static files to a static server (nginx):
        'offload_dir': None,
        'offload_path': None,

        'template_dir': '../templates'
    }


class DohApp:
    def __init__(self, config):
        self.app_dir = config.get('app_dir', os.getcwd())

        conf = default_conf(self.app_dir)
        conf.update(config)

        template_dir = conf['template_dir']

        app = Flask(__name__, template_folder=template_dir)

        app.debug = conf['debug']
        app.storage_dir = conf['storage_dir']
        app.static_dir = conf['static_dir']
        app.data_dir = conf['data_dir']
        # app.share_dir = conf['share_dir']

        app.offload = None
        offload_dir = conf.get('offload_dir')
        offload_path = conf.get('offload_path')
        if offload_dir and offload_path:
            Offload = namedtuple('Offload', ['dir', 'path', 'minsize'])
            app.offload = Offload(offload_dir, offload_path, 1024 * 1024)

        # monkey-patch the environment to handle 'X-Forwarded-For'
        # 'X-Forwarded-Proto', etc:
        app.wsgi_app = ReverseProxied(app.wsgi_app)

        # self.shared = self._scan_share(app.share_dir)

        self.storage = LocalStorage(app.storage_dir, app.data_dir)

        plugin_dir = os.path.join(self.app_dir, 'doh/content')
        self.plugins = content.Plugins(plugin_dir)

        self.conf = conf

        @app.errorhandler(404)
        def not_found(e):
            return self.r404()

        @app.errorhandler(500)
        def internal_error(e):
            return self.r500(e)

        @app.route(url.join(url._res, '<path:path>'))
        def static_handler(path):
            fname = os.path.join(app.static_dir, path)
            if not os.path.exists(fname):
                return self.r404(path)

            # print('Serving %s' % fname)
            return flask.send_file(fname)

        @app.route(url._my, defaults={'path': ''}, methods=['GET', 'POST'])
        @app.route(url.join(url._my, '<path:path>'), methods=['GET', 'POST'])
        def path_handler(path):
            req = flask.request

            auth = req.headers.get('Authorization')
            user = ''
            if auth and auth.startswith('Basic '):
                user = b64decode(auth.split()[1]).split(':')[0]
            print('### method=%s path=%s user=%s' % (req.method, path, user))

            if req.method == 'GET':
                return self._path_get(req, path)
            if req.method == 'POST':
                return self._path_post(req, path)
            return self.r400('Unknown method ' + req.method)

        # @app.route(url.join(url._pub, '<path:path>'))
        # def pub_handler(path):
        #     fname = secure_filename(path)
        #     fname = os.path.join(app.share_dir, fname)
        #     if not os.path.exists(fname):
        #         return self.r404(path)

        #     # print('Serving %s' % fname)
        #     return flask.send_file(fname)

        self.app = app

    def _path_get(self, req, path):
        if not self.storage.exists(path):
            return self.r404(path)

        entry = self.storage.file_info(path)
        if entry.is_dir:
            play = req.args.get('play')
            return self._render_dir(path, play=play)

        if 'edit' in req.args:
            text, e = self.storage.read_text(path)
            if e:
                return self.r400(e)
            args = {
                'js_links': [
                    url.codemirror('codemirror.min.js'),
                    url.codemirror('addon/dialog/dialog.min.js')
                ],
                'css_links': [
                    url.codemirror('codemirror.min.css'),
                    url.codemirror('addon/dialog/dialog.min.css')
                ],
                'codemirror_root': url.codemirror(),
                'text': text,
                'mimetype': content.guess_mime(path),
                'path_prefixes': self._gen_prefixes(path),
                'read_only': not entry.can_write
            }
            return flask.render_template('edit.htm', **args)
        if 'see' in req.args:
            mimetype = content.guess_mime(path)
            args = {
                'frame_url': url.my(path),
                'path_prefixes': self._gen_prefixes(path)
            }
            tmpl = 'frame.htm'
            if mimetype.startswith('video/'):
                tmpl = 'media.htm'
            return flask.render_template(tmpl, **args)

        return self._download(path, octetstream=('dl' in req.args))

    def _path_post(self, req, path):
        if 'update' in req.args:
            print('update request for %s:' % path)
            print(req.data)
            print('------------------------------')
            e = self.storage.write_text(path, req.data)
            if e:
                return flask.Response(str(e)), 400
            return flask.Response("saved"), 200

        print(req.form)
        action = req.form['action']
        if action == 'upload':
            if 'file' not in req.files:
                return self.r400('no file in POST')

            return self._upload(req, path)
        # if action == 'share':
        #     return self._share(path)
        if action == 'rename':
            oldname = req.form.get('oldname')
            newname = req.form.get('newname')
            return self._rename(path, oldname, newname)
        if action == 'delete':
            fname = req.form.get('filename')
            return self._delete(path, fname)
        if action == 'create':
            mime = req.form.get('mime')
            name = req.form.get('name')
            if mime == 'fs/dir':
                return self._mkdir(name)
            elif mime.startswith('text/'):
                e = self.storage.write_text(path, '')
                if e:
                    return self.r400(e)
                return flask.redirect(url.my(name) + '?edit')
            return self.r400('cannot create file with type ' + mime)
        if action == 'cut':
            name = req.form.get('name').strip()
            name = os.path.join(path, name)
            e = self.storage.clipboard_cut(name)
            if e:
                return self.r400(e)
            return flask.redirect(url.my(path))
        if action == 'copy':
            name = req.form.get('name')
            name = os.path.join(path, name)
            e = self.storage.clipboard_copy(name)
            if e:
                return self.r400(e)
            return flask.redirect(url.my(path))
        if action in ['paste', 'cb_clear']:
            into = path if action == 'paste' else None
            e = self.storage.clipboard_paste(into, dryrun=False)
            if e:
                return self.r400(e)
            return flask.redirect(url.my(path))
        if action == 'cb_clear':
            e = self.storage.clipboard_clear()
            if e:
                return self.r400(e)
            return flask.redirect(url.my(path))

        return self.r400('unknown action %s' % action)

    def run(self):
        self.app.run(host=self.conf['host'], port=self.conf['port'])

    def _gen_prefixes(self, path):
        return url.prefixes(self.storage.exists, path)

    def file_info(self, path):
        entry = self.storage.file_info(path)
        entry.href = url.my(path)

        # shared = self.shared.get(path)
        # if shared:
        #     shared = flask.url_for('pub_handler', path=shared)
        # entry.shared = shared

        entry.see_url = None
        if entry.is_text():
            entry.see_url = entry.href + '?edit'
        elif entry.is_audio():
            dirpath = os.path.dirname(path)
            filename = os.path.basename(path)
            entry.see_url = url.my(dirpath) + '?play=' + filename
        elif entry.is_viewable():
            entry.see_url = entry.href + '?see'

        return entry

    def r400(self, why):
        args = {'title': 'not accepted', 'e': why}
        return flask.render_template('500.htm', **args), 400

    def r404(self, path=None):
        if path is None:
            return flask.redirect(url.my())
        args = {
            'path': path,
            'path_prefixes': self._gen_prefixes(path),
            'title': 'no ' + path if path else 'not found'
        }
        mimetype = content.guess_mime(path)
        if mimetype is None:
            args['maybe_new'] = {
                'path': path,
                'mime': 'fs/dir',
                'desc': 'directory'
            }
        elif mimetype.startswith('text/'):
            args['maybe_new'] = {
                'path': path,
                'mime': mimetype,
                'desc': 'text file'
            }
        return flask.render_template('404.htm', **args), 404

    def r500(self, e=None):
        args = {
            'title': 'server error',
            'e': e
        }
        return flask.render_template('500.htm', **args), 500

    def _render_dir(self, path, play=None):
        lsdir = []
        try:
            for fname in self.storage.list_dir(path):
                entry = self.file_info(url.join(path, fname))

                lsfile = {
                    'name': fname,
                    'mime': content.guess_mime(fname),
                    'href': entry.href,
                    'size': entry.size,
                    'isdir': entry.is_dir,
                    'is_hidden': fname.startswith('.'),
                    'see_url': entry.see_url,
                    'ctime': entry.ctime,
                    'full_ctime': time.ctime(entry.ctime)+' '+time.tzname[0],
                    'created_at': content.smart_time(entry.ctime),
                    # 'shared': entry.shared,
                }

                if entry.is_dir:
                    lsfile['icon_src'] = 'dir-icon'
                    lsfile['icon_alt'] = 'd'
                else:
                    lsfile['icon_src'] = 'file-icon'
                    lsfile['icon_alt'] = '-'
                if fname == play:
                    lsfile['play'] = True

                if entry.can_rename:
                    lsfile['rename_url'] = url.my(path) + '?rename=' + fname

                lsdir.append(lsfile)

            clipboard = []
            for entry in self.storage.clipboard_list():
                loc = entry['tmp'] if entry['cut'] else entry['path']
                isdir = self.storage.is_dir(loc)

                e = {}
                e['do'] = 'cut' if entry['cut'] else 'copy'
                e['path'] = entry['path']
                e['icon_src'] = 'dir-icon' if isdir else 'file-icon'
                clipboard.append(e)

            lsdir = sorted(lsdir, key=lambda d: (not d['isdir'], d['name']))

            templvars = {
                'path': path,
                'lsdir': lsdir,
                'title': path,
                'path_prefixes': self._gen_prefixes(path),
                'rename': flask.request.args.get('rename'),
                'clipboard': clipboard
            }
            return flask.render_template('dir.htm', **templvars)
        except OSError as e:
            return flask.render_template('500.htm', e=e), 500

    def _mktemp(self, fname=None):
        tmp_dir = os.path.join(self.app.data_dir, 'tmp')
        if not os.path.exists(tmp_dir):
            os.mkdir(tmp_dir)
        _id = str(uuid.uuid1())
        if fname:
            fname = _id + '.' + secure_filename(fname)
        else:
            fname = _id
        return os.path.join(tmp_dir, fname)

    def _upload(self, req, path):
        redir_url = url.my(path)

        f = req.files['file']
        if not f.filename:
            return flask.redirect(redir_url)

        tmppath = self._mktemp(f.filename)
        exc = None
        try:
            print('Saving file as %s ...' % tmppath)
            f.save(tmppath)
            exc = self.storage.move_from_fpath(tmppath, path, f.filename)
        except (OSError, IOError, ValueError) as e:
            exc = e

        if exc:
            return self.r500(exc)
        return flask.redirect(redir_url)

    def _download(self, path, octetstream=False):
        if self.app.offload:
            u, e = self.storage.static_download(path, self.app.offload)
            if e:
                return self.r500(e)
            print('Redirecting to static: %s' % u)
            return flask.redirect(u)

        # TODO: hide _fullpath(), figure out a generic way of serving
        dlpath = self.storage._fullpath(path)

        headers = None
        if octetstream:
            headers = {'Content-Type': 'application/octet-stream'}
        if headers:
            return flask.send_file(dlpath), 200, headers
        else:
            return flask.send_file(dlpath), 200

    def _rename(self, path, oldname, newname):
        print("mv %s/%s %s/%s" % (path, oldname, path, newname))
        if os.path.dirname(oldname):
            return self.r400('Expected bare filename: ' + oldname)
        if os.path.dirname(newname):
            return self.r400('Expected bare filename: ' + newname)

        old = os.path.join(path, oldname)
        new = os.path.join(path, newname)
        try:
            self.storage.rename(old, new)
            return flask.redirect(url.my(path))
        except IOError as e:
            return self.r500(e)

    def _delete(self, path, fname):
        if os.path.dirname(fname):
            return self.r400('Expected bare filename: ' + fname)

        fpath = os.path.join(path, fname)
        print("rm %s" % fpath)
        e = self.storage.delete(fpath)
        if e:
            return self.r500(e)
        return flask.redirect(url.my(path))

    def _mkdir(self, dirname):
        e = self.storage.make_dir(dirname)
        if e:
            return self.r500(e)
        return flask.redirect(url.my(dirname))

    # def _scan_share(self, share_dir):
    #     share = {}
    #     for link in os.listdir(share_dir):
    #         lpath = os.path.join(share_dir, link)
    #         if not os.path.islink(lpath):
    #             continue

    #         source = os.readlink(lpath)
    #         print('share: %s => %s' % (link, source))
    #         share[source] = link
    #     return share

    # def _share(self, path):
    #     req = flask.request
    #     try:
    #         fname = req.form.get('file')
    #         if not fname:
    #             return self.r400('no `file` in POST')

    #         fname = secure_filename(fname)
    #         fpath = os.path.join(dpath, fname)
    #         link = os.path.join(self.app.share_dir, fname)
    #         # TODO: check if already shared
    #         # TODO: check for existing links

    #         os.symlink(fpath, link)
    #         self.shared[fpath] = fname
    #         print('shared:', fpath, ' => ', fname)
    #         return flask.redirect(url.my(path))
    #     except OSError as e:
    #         return self.r500(e)
