import mimetypes


# TODO: make it an external file
mime_by_extension = {
    'Makefile': 'text/x-makefile',

    'erl': 'text/x-erlang',
    'hs': 'text/x-haskell',
    'ini': 'text/x-ini',
    'lhs': 'text/x-haskell',
    'md': 'text/markdown',
    'org': 'text/x-org',
    'rb': 'text/x-ruby',
    'rs': 'text/x-rust',
    'scala': 'text/x-scala',
    'scm': 'text/x-scheme',
    'sh': 'text/x-shell',
    'tex': 'text/x-latex',

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
