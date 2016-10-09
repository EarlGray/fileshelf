import os.path

from flask import url_for

def default_conf(appdir):
    return {
        'host': '127.0.0.1',
        'port': 5000,
        'rooturl': '/',
        'debug': False,
        'application_dir': appdir,
        'storage_dir': os.path.join(appdir, 'storage'),
        'static_dir': os.path.join(appdir, 'static')
    }

my_url = '/my'

def url_join(*args):
    """ joins URLs """
    return '/'.join([arg.rstrip('/') for arg in args if len(arg)])


def path_prefixes(path):
    """ generates a list of [(path_chunk, path_href)] """
    url = url_for('path_handler')
    res = []
    for d in path.split('/'):
        url = url_join(url, d)
        res.append((d, url))
    return res
