from doh.content import Handler


class DirHandler(Handler):
    def can_handle(self, storage, path):
        if storage.is_dir(path):
            return Handler.SHOULD
        return Handler.DOESNT

    def render(self, req, storage, path):
        self._log('dir.render(%s)' % path)


__all__ = [DirHandler]
