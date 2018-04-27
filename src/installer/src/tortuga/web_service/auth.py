from logging import getLogger

import cherrypy
from cherrypy.lib import httpauth
import pyjwt

from tortuga.auth.manager import AuthManager
from tortuga.auth.method import AuthenticationMethod, MultiAuthentionMethod, \
    UsernamePasswordAuthenticationMethod
from tortuga.auth.principal import AuthPrincipal
from tortuga.exceptions.authenticationFailed import AuthenticationFailed


logger = getLogger(__name__)


class TortugaHTTPAuthError(cherrypy.HTTPError):
    @staticmethod
    def set_response():
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        cherrypy.response.status = 401
        cherrypy.response.body = b'Authentication required'


def authentication_required():
    """
    A decorator that specifies whether or not authentication is required.

    """
    def decorate(f):
        if not hasattr(f, '_cp_config'):
            f._cp_config = dict()
        if 'auth.required' not in f._cp_config:
            f._cp_config['auth.required'] = True
        return f

    return decorate


class CherryPyAuthenticator(MultiAuthentionMethod):
    """
    An authenticator designed to be run as a CherryPy tool.

    """
    def __call__(self, *args, **kwargs):
        if cherrypy.request.config.get('auth.required', False):
            self.authenticate(**kwargs)

    def authenticate(self, skip_callbacks: bool = False, **kwargs) -> str:
        try:
            return super().authenticate(skip_callbacks=skip_callbacks,
                                        **kwargs)
        except AuthenticationFailed:
            raise TortugaHTTPAuthError()

    def on_authentication_succeeded(self, username: str):
        super().on_authentication_succeeded(username)

        principal: AuthPrincipal = AuthManager().get_principal(username)
        principal_attributes: dict = principal.get_attributes()

        cherrypy.request.login = username
        cherrypy.session['admin_id']: int = \
            principal_attributes.get('id', None)

    def on_authentication_failed(self):
        cherrypy.request.login: str = None
        cherrypy.session['admin_id']: int = None


class HttpSessionAuthenticationMethod(AuthenticationMethod):
    """
    Authenticates a user based on a stored session key who's value is
    the username of the user.

    """
    SESSION_KEY = '_cp_username'

    def do_authentication(self, **kwargs) -> str:
        username: str = cherrypy.session.get(self.SESSION_KEY, None)
        if not username:
            raise AuthenticationFailed()
        return username

    def on_authentication_succeeded(self, username: str):
        cherrypy.session[self.SESSION_KEY] = username

    def on_authentication_failed(self):
        cherrypy.session[self.SESSION_KEY] = None


class HttpBasicAuthenticationMethod(UsernamePasswordAuthenticationMethod):
    """
    Authenticate a user via username password, via HTTP basic authentication.

    """
    SCHEME = 'basic'

    def do_authentication(self, **kwargs) -> str:
        username = None
        password = None

        if 'authorization' in cherrypy.request.headers:
            authorization = cherrypy.request.headers['authorization']
            ah = httpauth.parseAuthorization(authorization)
            if ah['auth_scheme'] == 'basic':
                username = ah['username']
                password = ah['password']

        return super().do_authentication(username=username, password=password)


class HttpPostAuthenticatonMethod(UsernamePasswordAuthenticationMethod):
    """
    Authenticate a user via HTTP post data.

    """
    def do_authentication(self, username: str = None,
                          password: str =None) -> str:
        if int(cherrypy.request.headers['Content-Length']):
            postdata = cherrypy.request.json
        else:
            postdata = {}

        username = postdata.get('username', None)
        password = postdata.get('password', None)

        return super().do_authentication(username=username, password=password)


class HttpJwtAuthenticationMethod(AuthenticationMethod):
    """
    Authenticate a user via JWT tokens.

    """
    ALGORITHMS = ['HS256', 'RS256']

    def do_authentication(self, **kwargs) -> str:
        if 'authorization' not in cherrypy.request.headers:
            raise AuthenticationFailed()

        authorization = cherrypy.request.headers['authorization']
        scheme, value = self._parse_authorization_header(authorization)
        if not value or not scheme or scheme.lower() != 'bearer':
            raise AuthenticationFailed()

        decoded = pyjwt.decode(value, self._get_key(),
                               algorithms=self.ALGORITHMS)

        username = decoded.get('username', None)
        if not username:
            raise AuthenticationFailed()

        principal: AuthPrincipal = AuthManager().get_principal(username)
        if not principal:
            raise AuthenticationFailed()

        return username

    @staticmethod
    def _parse_authorization_header(header: str) -> (str, str):
        scheme = None
        value = None

        parts = header.split(' ', 1)
        if parts:
            scheme = parts[0]
        if len(parts) > 1:
            value = parts[1]

        return scheme, value

    def _get_key(self):
        return 'Abc123'
