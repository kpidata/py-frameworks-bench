import functools

from aiohttp import web

from aiohttp_security import remember, forget, authorized_userid, permits


def require(permission):
    def wrapper(f):
        @functools.wraps(f)
        async def wrapped(self, request):
            has_perm = await permits(request, permission)
            if not has_perm:
                message = 'User has no permission %s' % permission
                raise web.HTTPForbidden(body=message.encode())
            return await f(self, request)
        return wrapped
    return wrapper


class Web(object):
    index_template = """
<!doctype html>
<head>
</head>
<body>
<p>{message}</p>
<form action="/login" method="post">
  Login:<br>
  <input type="text" name="login"><br>
  Password:<br>
  <input type="password" name="password">
  <input type="submit" value="Login">
</form>
<a href="/logout">Logout</a>
</body>
"""

    async def index(self, request):
        username = await authorized_userid(request)
        if username:
            template = self.index_template.format(
                message='Hello, {username}!'.format(username=username))
        else:
            template = self.index_template.format(message='You need to login')
        response = web.Response(body=template.encode())
        return response

    async def login(self, request):
        response = web.Response(body=b'This is index page')
        form = await request.post()
        login = form.get('login')
        password = form.get('password')
        # here you can check for correct user/password combination
        await remember(request, response, login)
        return web.HTTPFound('/')

    @require('public')
    async def logout(self, request):
        response = web.Response(body=b'You have been logged out')
        await forget(request, response)
        return response

    @require('public')
    async def internal_page(self, request):
        response = web.Response(
            body=b'This page is visible for all registered users')
        return response

    @require('protected')
    async def protected_page(self, request):
        response = web.Response(body=b'You are on protected page')
        return response

    def configure(self, app):
        router = app.router
        router.add_route('GET', '/', self.index, name='index')
        router.add_route('POST', '/login', self.login, name='login')
        router.add_route('GET', '/logout', self.logout, name='logout')
        router.add_route('GET', '/public', self.internal_page, name='public')
        router.add_route('GET', '/protected', self.protected_page,
                         name='protected')
