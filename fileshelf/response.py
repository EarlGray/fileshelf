import flask


class RequestError(Exception):
    """ response status 400 is required """
    pass


class Response:
    """ content.Response is the base class for plugin responses """
    pass


class Redirect(Response):
    """ redirect to self.url """
    def __init__(self, url):
        self.url = url

    def __call__(self):
        return flask.redirect(self.url)


class SendContents(Response):
    """ send self.contents as response with status 200 """
    def __init__(self, contents):
        self.contents = contents

    def __call__(self):
        return flask.Response(self.contents), 200


class RenderTemplate(Response):
    """ render self.tmpl with self.params, status 200 """
    def __init__(self, tmpl, params):
        self.tmpl = tmpl
        self.params = params

    def __call__(self):
        return flask.render_template(self.tmpl, **self.params)
