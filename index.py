import os
import stat

import flask
from flask import Flask
from werkzeug.utils import secure_filename


storage_dir = None
static_dir = None
my_url = '/my'


def url_join(*args):
    return '/'.join([arg.rstrip('/') for arg in args if len(arg)])


def path_prefixes(path):
    url = my_url
    res = []
    for d in path.split('/'):
        url = url_join(url, d)
        res.append((d, url))
    return res

app = Flask(__name__)
app.debug = False


@app.route('/')
def homepage_handler():
    return flask.redirect(my_url, 302)


@app.route(my_url, defaults={'path': ''}, methods=['GET', 'POST'])
@app.route(url_join(my_url, '<path:path>'), methods=['GET', 'POST'])
def path_handler(path):
    req = flask.request

    dpath = os.path.join(storage_dir, path)
    print '#### %s <%s> => listdir <%s>' % (req.method, path, dpath)

    if req.method == 'POST':
        if 'file' not in req.files:
            return flask.render_template('500.htm', e='no file'), 400

        url = os.path.join(my_url, path)
        url.strip(os.path.sep)

        f = req.files['file']
        fpath = os.path.join(storage_dir, path, secure_filename(f.filename))
        print 'Saving file as %s' % fpath
        try:
            f.save(fpath)
        except OSError as e:
            return flask.render_template('500.htm', e=e), 500
        print 'Success, redirecting back to %s' % url
        return flask.redirect(url)

    if not os.path.exists(dpath):
        return flask.render_template('404.htm'), 404

    if not os.path.isdir(dpath):
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
    fname = os.path.join(static_dir, fname)
    if not os.path.exists(fname):
        return flask.render_template('404.htm', path=path), 404

    print 'Serving %s' % fname
    return flask.send_file(fname)


def error_handler(code, e=None, path=None):
    return flask.render_template('%d.htm' % code, e=e, path=path), code


@app.errorhandler(404)
def not_found(e):
    return flask.render_template('404.htm'), 404


@app.errorhandler(500)
def internal_error(e):
    return flask.render_template('500.htm', e=e), 500

if __name__ == '__main__':
    storage_dir = os.path.join(os.getcwd(), 'storage')
    static_dir = os.path.join(os.getcwd(), 'static')

    for k, v in app.config.iteritems():
        print '%s\t: %s' % (k, v)

    app.run(host='0.0.0.0', port=5000)
