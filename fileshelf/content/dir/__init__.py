import fileshelf.content as content


class DirHandler(content.Handler):
    def can_handle(self, storage, path):
        if storage.is_dir(path):
            return content.Priority.SHOULD
        return content.Priority.DOESNT

    def render(self, req, storage, path):
        self._log('dir.render(%s)' % path)


__all__ = [DirHandler]
