from doh.content import Handler


class DirHandler(Handler):
    def __init__(self):
        pass

    def can_handle(self, req, storage, path):
        if storage.is_dir(path):
            return Handler.SHOULD
        return Handler.DOESNT

    def render(self, req, storage, path):
        print('dir.render(%s)' % path)
        return None


__all__ = [DirHandler]
