import os.path
import flask

_my = '/my'
_pub = '/pub'
_res = '/res'


def join(*args):
    """ joins URLs """
    return '/'.join([arg.rstrip('/') for arg in args if len(arg)])


def my(*args, **kwargs):
    path = join(*args) if args else None
    u = flask.url_for('path_handler', path=path)
    if kwargs.get('see'):
        u += '?see'
    elif kwargs.get('raw'):
        u += '?raw'
    return u


def res(*args):
    path = join(*args) if args else None
    u = flask.url_for('static_handler', path=path)
    return u


def prefixes(exists, path):
    """ generates a list of [(path_chunk, path_href or None)]
        `path_href` may be None if this path is not in the filesystem
    """
    url = my()
    res = []
    pre = ''
    for d in path.split('/'):
        pre = os.path.join(pre, d)

        if exists(pre):
            url = join(url, d)
        else:
            url = None

        res.append((d, url))
    return res


def codemirror(path=None):
    cdn_root = 'https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.23.0'
    return join(cdn_root, path) if path else cdn_root
