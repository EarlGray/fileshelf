import fileshelf.content as content
import fileshelf.content.edit as edit


class MarkdownHandler(edit.EditHandler):
    conf = {
        'extensions': {
            'md': content.Priority.SHOULD,
            'markdown': content.Priority.SHOULD
        }
    }
