import fileshelf.content as content


class ImageHandler(content.Handler):
    conf = {
        'mime_regex': {
            #'^image/': content.Priority.CAN
        }
    }
