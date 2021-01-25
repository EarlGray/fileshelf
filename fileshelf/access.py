from functools import wraps
from base64 import b64decode

import os.path
import flask
from passlib.apache import HtpasswdFile

from fileshelf.storage import LocalStorage


class AuthError(Exception):
    pass


class NoSuchUser(Exception):
    pass


class AuthChecker:
    methods = [None, 'basic']

    def __init__(self, conf):
        auth = conf.get('auth')
        if auth not in AuthChecker.methods:
            raise ValueError('unknown auth type: ' + auth)

        self.auth = auth
        self.https_only = conf.get('auth_https_only')

        if auth == 'basic':
            htpasswd = os.path.join(conf['data_dir'], 'htpasswd.db')
            htpasswd = conf.get('auth_htpasswd') or htpasswd
            self.htpasswd = HtpasswdFile(htpasswd)
            self._log('Using htpasswd: ' + str(htpasswd))

            self.realm = conf.get('auth_realm', 'fileshelf')

    def _log(self, msg):
        print('## Auth: ' + msg)

    def check_access(self, handler):
        @wraps(handler)
        def decorated(*args, **kwargs):
            req = flask.request
            if self.https_only and req.environ['wsgi.url_scheme'] != 'https':
                raise AuthError('HTTPS required')

            path = req.environ['PATH_INFO']

            user = None
            if self.auth is None:
                user = UserDb.DEFAULT
            elif self.auth == 'basic':
                user = self._check_basic_auth(req)
                if user is None:
                    hdrs = {
                        'WWW-Authenticate': 'Basic realm="%s"' % self.realm
                    }
                    # TODO: a nicer page
                    return flask.Response('Login Required', 401, hdrs)
            else:
                raise AuthError('unknown auth type: ' + self.auth)

            path = path.encode('latin1').decode('utf8')
            self._log('%s %s://%s@%s%s?%s' %
                      (req.method, req.environ['wsgi.url_scheme'],
                       user, req.environ['HTTP_HOST'], path,
                       req.environ['QUERY_STRING']))
            flask.request.user = user
            return handler(*args, **kwargs)
        return decorated

    def _check_basic_auth(self, req):
        auth = req.headers.get('Authorization')
        if not auth:
            self._log('basic auth: no Authorization')
            return None
        if not auth.startswith('Basic '):
            self._log('basic auth: not Basic')
            return None

        auth = auth.split()[1]
        auth = auth.encode('ascii')
        user, passwd = b64decode(auth).split(b':')
        ret = self.htpasswd.check_password(user, passwd)
        user = user.decode('ascii')
        passwd = passwd.decode('ascii')
        if ret is None:
            self._log('basic auth: user %s not found' % user)
            return None
        if ret is False:
            self._log('basic auth: check_password(<%s>, <%s>) failed'
                      % (user, passwd))
            return None
        return user

    def user_exists(self, user):
        return (user in self.htpasswd)


class UserDb:
    DEFAULT = ''

    def __init__(self, conf):
        data_dir = conf['data_dir']
        self.data_dir = data_dir

        if conf.get('multiuser'):
            self._init()
        else:
            store = LocalStorage(conf['storage_dir'], data_dir)
            default_user = {
                'name': UserDb.DEFAULT,
                'home': conf['storage_dir'],
                'storage': store
            }
            self.users = {self.DEFAULT: default_user}

    def _init(self):
        self.user_dir = os.path.join(self.data_dir, 'user')
        if not os.path.exists(self.user_dir):
            os.mkdir(self.user_dir)

        users = {}
        for u in os.listdir(self.user_dir):
            user_dir = os.path.join(self.user_dir, u)
            if not os.path.isdir(user_dir):
                continue

            home_dir = os.path.join(user_dir, 'home')
            if not os.path.exists(home_dir):
                os.mkdir(home_dir)

            store = LocalStorage(home_dir, user_dir)

            conf = {
                'name': u,
                'home': home_dir,
                'storage': store
            }
            users[u] = conf

        self.users = users

    def get_storage(self, user):
        try:
            user = user or self.DEFAULT
            return self.users[user]['storage']
        except KeyError:
            raise NoSuchUser('No such user: ' + user)
