import time

from fileshelf.content.Plugins import Plugins, Priority, Handler
from fileshelf.content.Mimetypes import guess_mime


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


__all__ = [guess_mime, smart_time, Handler, Plugins, Priority]
