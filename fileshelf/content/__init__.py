import time
import mimetypes

from fileshelf.content.Handler import Handler
from fileshelf.content.Plugins import Plugins

mime_by_extension = {
    'org': 'text/x-org',
    'scm': 'text/x-scheme',
    'erl': 'text/x-erlang',
    'rb': 'text/x-ruby',
    'sh': 'text/x-shell',
    'hs': 'text/x-haskell',
    'lhs': 'text/x-haskell',
    'md': 'text/markdown',
    'tex': 'text/x-latex',
    'Makefile': 'text/x-makefile',

    # non-text:
    'ipynb': 'application/ipynb',
}

mime_text_prefix = {
    'application/javascript': 'text/javascript',
    'application/xml': 'text/xml',
    'application/json': 'text/json',
    'application/x-sql': 'text/x-sql',
}


def guess_mime(path):
    if not path:
        return None
    ext = path.split('.')[-1]

    mime = mime_by_extension.get(ext)
    if mime:
        return mime

    mime = mimetypes.guess_type(path)[0]
    return mime_text_prefix.get(mime, mime)


def smart_time(tm):
    if isinstance(tm, float):
        tm = time.localtime(tm)
    if not isinstance(tm, time.struct_time):
        raise ValueError('Expected time.struct_time or float')

    t = time.strftime('%H:%M', tm)

    now = time.localtime()
    if now.tm_year == tm.tm_year:
        if now.tm_yday == tm.tm_yday:
            return t
        if now.tm_yday == tm.tm_yday + 1:
            return t + ', yesterday'
        if now.tm_yday - tm.tm_yday < 5:
            return t + time.strftime(', %a', tm)  # abbr. week day
        return t + time.strftime(', %b %d', tm)  # abbr. month and date
    return t + time.strftime(', %x', tm)


__all__ = [guess_mime, smart_time, Handler, Plugins]
