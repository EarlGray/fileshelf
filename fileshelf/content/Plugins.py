from __future__ import print_function

import os
import json
import re

import flask

import fileshelf.url as url
from fileshelf.content.Mimetypes import guess_mime


class Plugins:
    """ Manages plugins, their priorities and dispatches requests """

    def __init__(self, conf, plugins_dir):
        self.conf = conf
        self.plugins = {}

        for name, Plugin, conf in Plugins._scan(plugins_dir):
            try:
                plugin = Plugin(name, conf)
                self._init(plugins_dir, name)

                self.plugins[name] = plugin
                self._log('initialized: ' + name)
                # self._log('conf:', json.dumps(conf))
            except Exception as e:
                self._log('init error: plugin ' + name)
                self._log(e)

    def _init(self, plugins_dir, name):
        """ initializes directories for the plugin `name` """
        plugin_dir = os.path.join(plugins_dir, name)

        def check_and_link(sub_dir, into_dir):
            sub_dir = os.path.join(plugin_dir, sub_dir)
            if not os.path.isdir(sub_dir):
                return
            link_path = os.path.join(into_dir, name)
            if os.path.islink(link_path):
                os.remove(link_path)

            # self._log('ln "%s" -> "%s"' % (sub_dir, link_path))
            os.symlink(sub_dir, link_path)

        check_and_link('res', into_dir=self.conf['static_dir'])
        check_and_link('tmpl', into_dir=self.conf['template_dir'])

    def _log(self, *msgs):
        print('## Plugins: ', end='')
        print(*msgs)

    @staticmethod
    def _scan(plugins_dir):
        for entry in os.listdir(plugins_dir):
            plugin_dir = os.path.join(plugins_dir, entry)
            if not os.path.isdir(plugin_dir):
                continue

            # read `plugin.json` if exists
            conf = {}
            conf_path = os.path.join(plugin_dir, 'plugin.json')
            if os.path.exists(conf_path):
                conf = json.load(open(conf_path))

            if '__init__.py' in os.listdir(plugin_dir):
                # import Plugin class from __init__.py
                modname = 'fileshelf.content.' + entry
                mod = __import__(modname)
                mod = mod.content.__dict__[entry]

                Plugin = Plugins._find_plugin_in(mod)
                if Plugin:
                    yield (entry, Plugin, conf)
            elif os.path.exists(os.path.join(plugin_dir, 'tmpl/index.htm')):
                # no plugin class, but `tmpl/index.htm` is there
                yield (entry, Handler, conf)

    @staticmethod
    def _find_plugin_in(mod):
        for name, Plugin in mod.__dict__.items():
            if hasattr(Plugin, '__bases__') and Handler in Plugin.__bases__:
                return Plugin
        return None

    def __contains__(self, name):
        return name in self.plugins

    def get(self, name, default=None):
        return self.plugins.get(name, default)

    def dispatch(self, storage, path):
        handlers = {
            Priority.SHOULD: [],
            Priority.CAN: []
        }
        for name, plugin in self.plugins.items():
            prio = plugin.can_handle(storage, path)
            if prio == Priority.DOESNT:
                continue
            if prio == Priority.MUST:
                return name
            handlers[prio].append(name)

        if handlers[Priority.SHOULD]:
            return handlers[Priority.SHOULD][0]
        elif handlers[Priority.CAN]:
            return handlers[Priority.CAN][0]
        return None

    def render(self, req, storage, path, name=None):
        name = name or self.dispatch(storage, path)
        if not name:
            return
        plugin = self.plugins[name]
        return plugin.render(req, storage, path)


class Priority:
    DOESNT = 0
    CAN = 1
    SHOULD = 2
    MUST = 3

    @staticmethod
    def val(s):
        if isinstance(s, int):
            return s
        if isinstance(s, str):
            try:
                return int(s)
            except ValueError:
                return getattr(Priority, s)


class Handler:
    def __init__(self, name, conf):
        """
        `name` is the name of this plugin and its directory
        `conf` is a config dict (maybe read from `plugin.json`)
        """
        self.name = name
        self.conf = conf

    def can_handle(self, storage, path):
        """ return content handler priority for `path`: DOESNT/CAN/SHOULD/MUST
        """

        extensions = self.conf.get('extensions')
        if extensions:
            _, ext = os.path.splitext(path)
            ext = ext.strip('.')
            # self._log('Handler.can_handle .' + ext)
            if ext in extensions:
                return Priority.val(extensions[ext])

        mime_conf = self.conf.get('mime_regex')
        mime = guess_mime(path)
        if mime_conf and mime:
            assert isinstance(mime_conf, dict)
            for regex, prio in mime_conf.items():
                if re.match(regex, mime):
                    return Priority.val(prio)

        return Priority.DOESNT

    def render(self, req, storage, path):
        """ handles GET requests """
        self._log('Handler.render(%s)' % path)

        tmpl = url.join(self.name, 'index.htm')
        self._log('rendering ' + tmpl)
        args = {
            'file_url': url.my(path),
            'user': getattr(flask.request, 'user'),
            'path_prefixes': url.prefixes(path, storage.exists)
        }
        return flask.render_template(tmpl, **args)

    def action(self, req, storage, path):
        """ handles POST requests, to override """
        raise NotImplementedError('Handler.action')

    def _log(self, *msgs):
        print('## Plugin[%s]: ' % self.name, end='')
        print(*msgs)
