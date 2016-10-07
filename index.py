import os
import flask
from flask import Flask

app = Flask(__name__)
storage_dir = None


@app.route('/')
def homepage_handler():
    return flask.redirect('/my', 302)


@app.route('/my', defaults={'path': ''}, methods=['GET', 'POST'])
@app.route('/my/<path:path>', methods=['GET', 'POST'])
def my_path_handler(path):
    dpath = os.path.join(storage_dir, path)
    print '#### listdir %s' % dpath

    if not os.path.exists(dpath):
        return flask.render_template('404.htm'), 404

    if not os.path.isdir(dpath):
        return flask.send_file(dpath)

    lsdir = {}
    try:
        for entry in os.listdir(dpath):
            fname = entry.decode('utf-8')
            lsdir[fname] = {
                'href': os.path.join('/my', path, fname)
            }
        return flask.render_template('dir.htm', path=path, lsdir=lsdir)
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
