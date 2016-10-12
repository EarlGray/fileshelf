from flask import url_for

my = '/my'


def join(*args):
    """ joins URLs """
    return '/'.join([arg.rstrip('/') for arg in args if len(arg)])


def prefixes(path):
    """ generates a list of [(path_chunk, path_href)] """
    url = url_for('path_handler')
    res = []
    for d in path.split('/'):
        url = join(url, d)
        res.append((d, url))
    return res
