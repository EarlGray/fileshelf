import os.path
import flask

_my = '/my'
_pub = '/pub'
_res = '/res'


def join(*args):
    """ joins URLs """
    return '/'.join([arg.rstrip('/') for arg in args if len(arg)])


def my(*args):
    path = join(*args) if args else None
    return flask.url_for('path_handler', path=path)


def prefixes(storage_dir, path):
    """ generates a list of [(path_chunk, path_href or None)]
        `path_href` may be None if this path is not in the filesystem
    """
    url = my()
    res = []
    for d in path.split('/'):
        storage_dir = os.path.join(storage_dir, d)

        if os.path.exists(storage_dir):
            url = join(url, d)
        else:
            url = None

        res.append((d, url))
    return res
