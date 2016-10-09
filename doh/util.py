import os.path

def default_conf():
    return {
        'host': '127.0.0.1',
        'port': 5000,
        'rooturl': '/',
        'debug': False,
        'storage_dir': os.path.join(os.getcwd(), 'storage'),
        'static_dir': os.path.join(os.getcwd(), 'static') 
    }

my_url = '/my'

def url_join(*args):
    """ joins URLs """
    return '/'.join([arg.rstrip('/') for arg in args if len(arg)])


def path_prefixes(path):
    """ generates a list of [(path_chunk, path_href)] """
    url = my_url
    res = []
    for d in path.split('/'):
        url = url_join(url, d)
        res.append((d, url))
    return res
