import io
import os
import stat
import errno
import shutil
import mimetypes

import doh.content as content


class LocalStorage:
    def __init__(self, storage_dir):
        if not os.path.isdir(storage_dir):
            raise OSError(errno.ENOENT, os.strerror(errno.ENOENT), storage_dir)
        self.storage_dir = storage_dir

    def _fullpath(self, *args):
        return os.path.join(self.storage_dir, *args)
        # fullpath = self.storage_dir
        # if args:
        #     path = os.path.join(*args)
        #     fullpath = os.path.join(

    def make_dir(self, path):
        path = self._fullpath(path)
        try:
            os.mkdir(path)
        except OSError as e:
            return e

    def list_dir(self, path):
        path = self._fullpath(path)
        return os.listdir(path)

    def rename(self, oldpath, newpath):
        old = self._fullpath(oldpath)
        new = self._fullpath(newpath)
        try:
            print("mv %s %s" % (old, new))
            shutil.move(old, new)
        except OSError as e:
            return e

    def delete(self, path):
        path = self._fullpath(path)
        try:
            if os.path.isdir(path):
                os.rmdir(path)
            else:
                os.remove(path)
        except OSError as e:
            return e

    def update_file(self, data):
        pass

    def file_info(self, path):
        fpath = os.path.join(self.storage_dir, path)

        def entry(): return 0

        st = os.lstat(fpath)
        entry.size = st.st_size
        entry.is_dir = stat.S_ISDIR(st.st_mode)

        entry.mimetype = content.guess_mime(path)

        def is_text():
            if entry.mimetype:
                return entry.mimetype.startswith('text/')
            return False

        def is_viewable():
            if entry.mimetype:
                if entry.mimetype in ['application/pdf']:
                    return True
            return False

        entry.is_text = is_text
        entry.is_viewable = is_viewable

        entry.can_rename = True
        entry.can_delete = True
        entry.can_read = True
        entry.can_write = True

        return entry

    def exists(self, path):
        path = self._fullpath(path)
        ret = os.path.exists(path)
        print('STORAGE: exists(%s) = %s' % (path, ret))
        return ret

    def is_dir(self, path):
        return os.path.isdir(self._fullpath(path))

    def read_text(self, path):
        """ returns (text or None, exception or None) """
        path = self._fullpath(path)
        try:
            text = io.open(path, encoding='utf8').read()
            return text, None
        except (IOError, OSError) as e:
            return None, e

    def write_text(self, path, data):
        path = self._fullpath(path)
        try:
            with io.open(path, 'w', encoding='utf8') as f:
                f.write(data.decode('utf8'))
        except (IOError, OSError) as e:
            return e
