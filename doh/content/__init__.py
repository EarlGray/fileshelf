import mimetypes

mime_by_extension = {
    'org': 'text/x-org',
    'scm': 'text/x-scheme',
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


__all__ = [guess_mime]
