import os
from collections import namedtuple

from traceback import print_tb

import flask
from flask import Flask

import fileshelf.url as url
import fileshelf.content as content
import fileshelf.response as resp
from fileshelf.access import AuthChecker, UserDb
from fileshelf.rproxy import ReverseProxied


class FileShelf:
    def __init__(self, conf):
        self.app_dir = conf['app_dir']
        template_dir = conf['template_dir']

        app = Flask(__name__, template_folder=template_dir)
        app.debug = conf['debug']
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

        plugin_dir = os.path.join(self.app_dir, 'fileshelf/content')
        self.plugins = content.Plugins(conf, plugin_dir)

        self.users = UserDb(conf)
        self.auth = AuthChecker(conf)

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

            return flask.send_file(fname)

        @app.route(url._my, defaults={'path': ''}, methods=['GET', 'POST'])
        @app.route(url.join(url._my, '<path:path>'), methods=['GET', 'POST'])
        @self.auth.check_access
        def path_handler(path):
            req = flask.request
            # don't store it permanently:
            self.storage = self.users.get_storage(req.user)

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

    def run(self):
        self.app.run(host=self.conf['host'], port=self.conf['port'])

    def _log(self, msg):
        print('## App: ', msg)

    def _is_plugin_request(self, req):
        args = list(req.args.keys())
        if len(args) == 1:
            param = args[0]
            plugin = self.plugins.get(param)
            return plugin

    def _path_get(self, req, path):
        # self._log('args = ' + str(req.args))
        if not self.storage.exists(path):
            return self.r404(path)

        is_dl = 'dl' in req.args.values()
        if is_dl:
            return self._download(path, octetstream=True)

        plugin = self._is_plugin_request(req)
        if not plugin:
            plugin = self.plugins.dispatch(self.storage, path)
            plugin = self.plugins.get(plugin)

        if not plugin:
            return self._download(path)

        try:
            self._log('%s.render("%s")' % (plugin.name, path))
            r = plugin.render(req, self.storage, path)
            return r()
        except resp.RequestError as e:
            return self.r400(e)
        except Exception as e:
            return self.r500(e, path)

    def _path_post(self, req, path):
        self._log(req.form)

        plugin = self._is_plugin_request(req)
        if plugin:
            self._log('%s.action("%s", %s)' % (plugin.name, path, str(req.form)))
            r = plugin.action(req, self.storage, path)
            return r()

        plugin = self.plugins.dispatch(self.storage, path)
        plugin = self.plugins.get(plugin)
        if not plugin:
            return self.r400('unknown POST: %s' % str(req.form))

        try:
            self._log('"%s" opens "%s"' % (plugin.name, path))
            r = plugin.action(req, self.storage, path)
            return r()
        except resp.RequestError as e:
            return self.r400(e)
        except Exception as e:
            return self.r500(e, path)

    def _prefixes(self, path, tabindex=1):
        return url.prefixes(path, self.storage.exists, tabindex)

    def r400(self, why):
        args = {'title': 'not accepted', 'e': why}
        return flask.render_template('500.htm', **args), 400

    def r404(self, path=None):
        if path is None:
            return flask.redirect(url.my())
        args = {
            'path': path,
            'path_prefixes': self._prefixes(path),
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

    def r500(self, e=None, path=None):
        if self.conf.get('debug'):
            raise e
        self._log('r500: e=%s' % str(e))
        if hasattr(e, '__traceback__'):
            print_tb(e.__traceback__)

        args = {
            'title': 'server error',
            'e': e,
        }
        if path:
            args['path_prefixes'] = self._prefixes(path)
        return flask.render_template('500.htm', **args), 500

    def _download(self, path, octetstream=False):
        if self.app.offload:
            u, e = self.storage.static_download(path, self.app.offload)
            if e:
                return self.r500(e)
            if u:
                self._log('Redirecting to static: %s' % u)
                return flask.redirect(u)

        # TODO: hide _fullpath(), figure out a generic way of serving
        dlpath = self.storage._fullpath(path)

        headers = None
        if octetstream:
            headers = {'Content-Type': 'application/octet-stream'}
        try:
            if headers:
                return flask.send_file(dlpath), 200, headers
            else:
                return flask.send_file(dlpath), 200
        except (IOError, OSError) as e:
            return self.r500(e, path)

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
