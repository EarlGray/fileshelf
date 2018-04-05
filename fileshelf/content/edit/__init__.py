import fileshelf.url as url
import fileshelf.content as content
import fileshelf.response as resp


def codemirror_path(path=None):
    cdn_root = 'https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.23.0'
    return url.join(cdn_root, path) if path else cdn_root


class EditHandler(content.Handler):
    conf = {
        'mime_regex': {
            '^text/': content.Priority.CAN
        }
    }

    def render(self, req, storage, path):
        entry = storage.file_info(path)
        text, e = storage.read_text(path)
        if e:
            raise e

        args = {
            'js_links': [
                codemirror_path('codemirror.min.js'),
                codemirror_path('addon/dialog/dialog.min.js'),
                codemirror_path('addon/search/search.min.js'),
                codemirror_path('addon/search/searchcursor.min.js')
            ],
            'css_links': [
                codemirror_path('codemirror.min.css'),
                codemirror_path('addon/dialog/dialog.min.css')
            ],
            'codemirror_root': codemirror_path(),
            'text': text,
            'mimetype': content.guess_mime(path),
            'path_prefixes': url.prefixes(path, storage.exists),
            'user': getattr(req, 'user'),
            'read_only': not entry.can_write
        }
        tmpl = url.join(self.name, 'index.htm')
        return resp.RenderTemplate(tmpl, args)

    def action(self, req, storage, path):
        actlist = req.args.getlist(self.name)
        self._log(str(actlist))

        if 'update' in actlist:
            self._log('update request for %s:' % path)
            # self._log(req.data)
            # self._log('------------------------------')
            e = storage.write_text(path, req.data)
            if e:
                self._log('RequestError: ' + str(e))
                return resp.RequestError(str(e))
            self._log('SendContents: saved')
            return resp.SendContents("saved")

        return resp.RequestError('unknown POST: ' + str(req.args))

__all__ = [EditHandler]
