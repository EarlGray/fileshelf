
import fileshelf.content as content


class EpubHandler(content.Handler):
    conf = {
        'extensions': {
            'epub': content.Priority.SHOULD
        }
    }
