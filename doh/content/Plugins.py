from __future__ import print_function

import os
import json
from doh.content import Handler


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
                modname = 'doh.content.' + entry
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

    def dispatch(self, storage, path):
        handlers = {
            Handler.MUST: [],
            Handler.SHOULD: [],
            Handler.CAN: []
        }
        for name, plugin in self.plugins.items():
            prio = plugin.can_handle(storage, path)
            if prio == Handler.DOESNT:
                continue
            elif prio == Handler.MUST:
                return name
            else:
                handlers[prio].append(name)

        if handlers[Handler.SHOULD]:
            return handlers[Handler.SHOULD][0]
        elif handlers[Handler.CAN]:
            return handlers[Handler.CAN][0]
        else:
            return None

    def render(self, req, storage, path, name=None):
        name = name or self.dispatch(storage, path)
        if not name:
            return
        plugin = self.plugins[name]
        return plugin.render(req, storage, path)
