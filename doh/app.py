from __future__ import print_function

import os
import stat

import flask
from flask import Flask
from werkzeug.utils import secure_filename

from doh.util import *


class DohApp:
    def __init__(self, conf):
        template_dir = conf.get('template_dir', '../templates')

        app = Flask(__name__, template_folder=template_dir)

        app.debug = conf['debug']
        app.storage_dir = conf['storage_dir']
        app.static_dir = conf['static_dir']

        self.conf = conf

        @app.route('/')
        def homepage_handler():
            return flask.redirect(my_url, 302)


        @app.route(my_url, defaults={'path': ''}, methods=['GET', 'POST'])
        @app.route(url_join(my_url, '<path:path>'), methods=['GET', 'POST'])
        def path_handler(path):
            req = flask.request

            dpath = os.path.join(app.storage_dir, path)
            print('#### %s <%s> => listdir <%s>' % (req.method, path, dpath))

            if req.method == 'POST':
                if 'file' not in req.files:
                    return flask.render_template('500.htm', e='no file'), 400

                url = url_join(my_url, path)

                f = req.files['file']
                fpath = os.path.join(app.storage_dir, path, secure_filename(f.filename))
                print('Saving file as %s' % fpath)
                try:
                    f.save(fpath)
                except OSError as e:
                    return flask.render_template('500.htm', e=e), 500
                print('Success, redirecting back to %s' % url)
                return flask.redirect(url)

            if not os.path.exists(dpath):
                return flask.render_template('404.htm'), 404

            if not os.path.isdir(dpath):
                # TODO: for large files, redirect to nginx-served address
                return flask.send_file(dpath)

            lsdir = []
            try:
                for fname in os.listdir(dpath):
                    st = os.lstat(os.path.join(dpath, fname))
                    lsdir.append({
                        'name': fname,
                        'href': url_join(my_url, path, fname),
                        'size': st.st_size,
                        'isdir': stat.S_ISDIR(st.st_mode)
                    })
                templvars = {
                    'path': path,
                    'lsdir': sorted(lsdir, key=lambda d: (not d['isdir'], d['name'])),
                    'path_prefixes': path_prefixes(path)
                }
                return flask.render_template('dir.htm', **templvars)
            except OSError:
                return flask.render_template('404.htm', path=path), 404


        @app.route('/res/<path:path>')
        def static_handler(path):
            fname = secure_filename(path)
            fname = os.path.join(app.static_dir, fname)
            if not os.path.exists(fname):
                return flask.render_template('404.htm', path=path), 404

            print('Serving %s' % fname)
            return flask.send_file(fname)


        @app.errorhandler(404)
        def not_found(e):
            return flask.render_template('404.htm'), 404


        @app.errorhandler(500)
        def internal_error(e):
            return flask.render_template('500.htm', e=e), 500

        
        self.app = app

    
    def run(self):
        self.app.run(host=self.conf['host'], port=self.conf['port'])

