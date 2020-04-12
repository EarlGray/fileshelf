import os
import time

import fileshelf.url as url
import fileshelf.content as content
import fileshelf.response as resp


class DirHandler(content.Handler):
    def can_handle(self, storage, path):
        if storage.is_dir(path):
            return content.Priority.SHOULD
        return content.Priority.DOESNT

    def _prefixes(self, path, tabindex=1):
        return url.prefixes(path, self.storage.exists, tabindex)

    def _file_info(self, path):
        entry = self.storage.file_info(path)
        entry.href = url.my(path)

        # shared = self.shared.get(path)
        # if shared:
        #     shared = url.pub(shared)
        # entry.shared = shared

        if not entry.can_read:
            return entry

        entry.open_url = entry.href
        if entry.is_audio():
            dirpath = os.path.dirname(path)
            filename = os.path.basename(path)
            entry.open_url = url.my(dirpath) + '?play=' + url.quote(filename)
        elif entry.is_viewable():
            entry.open_url = entry.href + '?see'

        return entry

    def render(self, req, storage, path):
        self.storage = storage
        play = req.args.get('play')
        if play: play = url.unquote(play)

        tabindex = 2
        addressbar = self._prefixes(path, tabindex)
        tabindex += len(addressbar)

        lsdir = []

        for fname in self.storage.list_dir(path):
            file_path = url.join(path, fname)
            entry = self._file_info(file_path)

            lsfile = {
                'name': fname,
                'mime': content.guess_mime(fname),
                'href': entry.href,
                'size': entry.size,
                'isdir': entry.is_dir,
                'is_hidden': fname.startswith('.'),
                'ctime': entry.ctime,
                'full_ctime': time.ctime(entry.ctime)+' '+time.tzname[0],
                'created_at': content.smart_time(entry.ctime),
                # 'shared': entry.shared,
            }

            if hasattr(entry, 'open_url'):
                lsfile['open_url'] = entry.open_url

            if entry.is_dir:
                lsfile['icon_src'] = 'dir-icon'
                lsfile['icon_alt'] = 'd'
            else:
                lsfile['icon_src'] = 'file-icon'
                lsfile['icon_alt'] = '-'

            if fname == play:
                lsfile['play_url'] = entry.href
                if entry.href.endswith('.m3u'):
                    u, e = self.storage.read_text(file_path)
                    if e:
                        raise e
                    for line in u.splitlines():
                        if not line.startswith('#'):
                            lsfile['play_url'] = line
                            break

            if entry.can_rename:
                lsfile['rename_url'] = url.my(path) + '?rename=' + fname

            lsdir.append(lsfile)

        clipboard = []
        for entry in self.storage.clipboard_list():
            loc = entry['tmp'] if entry['cut'] else entry['path']
            isdir = self.storage.is_dir(loc)

            e = {}
            e['do'] = 'cut' if entry['cut'] else 'copy'
            e['path'] = entry['path']
            e['icon_src'] = 'dir-icon' if isdir else 'file-icon'
            clipboard.append(e)

        lsdir = sorted(lsdir, key=lambda d: (not d['isdir'], d['name']))
        for entry in lsdir:
            entry['tabindex'] = tabindex
            tabindex += 1

        user = getattr(req, 'user')
        templvars = {
            'path': path,
            'lsdir': lsdir,
            'title': path,
            'path_prefixes': addressbar,
            'rename': req.args.get('rename'),
            'clipboard': clipboard,
            'upload_tabidx': tabindex,
            'user': user
        }
        return resp.RenderTemplate('dir/index.htm', templvars)

    def action(self, req, storage, path):
        self.storage = storage

        actions = req.form.getlist('action')
        if 'rename' in actions:
            oldname = req.form.get('oldname')
            newname = req.form.get('newname')
            return self._rename(path, oldname, newname)

        action = actions[0]
        if action == 'upload':
            if 'file' not in req.files:
                raise resp.RequestError('no file in POST')
            return self._upload(req, path)
        # if action == 'share':
        #     return self._share(path)
        if action == 'delete':
            files = req.form.getlist('file')
            return self._delete(path, files)
        if action == 'create':
            mime = req.form.get('mime')
            name = req.form.get('name')
            if mime == 'fs/dir':
                return self._mkdir(name)
            elif mime.startswith('text/'):
                fpath = os.path.join(path, name)
                e = self.storage.write_text(fpath, '')
                if e:
                    raise e
                return resp.Redirect(url.my(name) + '?edit')
            raise resp.RequestError('cannot create file with type ' + mime)
        if action == 'cut':
            files = req.form.getlist('file')
            files = map(str.strip, files)
            for f in files:
                name = os.path.join(path, f)
                e = self.storage.clipboard_cut(name)
                if e:
                    raise e
            return resp.Redirect(url.my(path))
        if action == 'copy':
            files = req.form.getlist('file')
            files = map(str.strip, files)
            for f in files:
                name = os.path.join(path, f)
                e = self.storage.clipboard_copy(name)
                if e:
                    raise e
            return resp.Redirect(url.my(path))
        if action in ['paste', 'cb_clear']:
            into = path if action == 'paste' else None
            e = self.storage.clipboard_paste(into, dryrun=False)
            if e:
                raise e
            return resp.Redirect(url.my(path))
        if action == 'cb_clear':
            e = self.storage.clipboard_clear()
            if e:
                raise e
            return resp.Redirect(url.my(path))

        raise resp.RequestError('unknown POST: %s' % action)

    def _upload(self, req, path):
        redir_url = url.my(path)

        f = req.files['file']
        if not f.filename:
            return resp.Redirect(redir_url)

        tmppath = self.storage.mktemp(f.filename)

        self._log('Saving file as %s ...' % tmppath)
        f.save(tmppath)
        self.storage.move_from_fpath(tmppath, path, f.filename)

        return resp.Redirect(redir_url)

    def _mkdir(self, dirname):
        e = self.storage.make_dir(dirname)
        if e:
            raise e

        return resp.Redirect(url.my(dirname))

    def _rename(self, path, oldname, newname):
        self._log("mv %s/%s %s/%s" % (path, oldname, path, newname))

        if os.path.dirname(oldname):
            raise resp.RequestError('Expected bare filename: ' + oldname)
        if os.path.dirname(newname):
            raise resp.RequestError('Expected bare filename: ' + newname)

        old = os.path.join(path, oldname)
        new = os.path.join(path, newname)

        self.storage.rename(old, new)
        return resp.Redirect(url.my(path))

    def _delete(self, path, files):
        if isinstance(files, str):
            files = [files]

        for fname in files:
            if os.path.dirname(fname):
                return self.r400('Expected bare filename: ' + fname)

            fpath = os.path.join(path, fname)
            self._log("rm %s" % fpath)
            e = self.storage.delete(fpath)
            if e:
                raise e

        return resp.Redirect(url.my(path))

__all__ = [DirHandler]
