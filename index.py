import os
import flask
from flask import Flask
from werkzeug.utils import secure_filename

app = Flask(__name__)
storage_dir = None
my_url = '/my'


def path_prefixes(path):
    url = my_url
    res = []
    for d in path.split('/'):
        url = url + '/' + d
        res.append((d, url))
    return res


@app.route('/')
def homepage_handler():
    return flask.redirect(my_url, 302)


@app.route(my_url, defaults={'path': ''}, methods=['GET', 'POST'])
@app.route(my_url + '/<path:path>', methods=['GET', 'POST'])
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

    lsdir = {}
    try:
        for entry in os.listdir(dpath):
            fname = entry.decode('utf-8')
            lsdir[fname] = {
                'href': os.path.join(my_url, path, fname)
            }
        templvars = {
            'path': path,
            'lsdir': lsdir,
            'path_prefixes': path_prefixes(path)
        }
        return flask.render_template('dir.htm', **templvars)
    except OSError:
        return flask.render_template('404.htm', path=path), 404


@app.errorhandler(500)
def error_handler(e):
    return flask.render_template('500.htm', e=e), 500

if __name__ == '__main__':
    app.debug = True
    storage_dir = os.path.join(os.getcwd(), 'storage')

    for k, v in app.config.iteritems():
        print '%s\t: %s' % (k, v)
    app.run()
