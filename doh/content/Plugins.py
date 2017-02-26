from __future__ import print_function

import os
from doh.content import Handler


class Plugins:
    def __init__(self, plugins_dir):
        self.plugins_dir = plugins_dir
        self.plugins = {}

        for entry in os.listdir(plugins_dir):
            plugin_dir = os.path.join(plugins_dir, entry)
            if not os.path.isdir(plugin_dir):
                continue
            if '__init__.py' not in os.listdir(plugin_dir):
                continue

            modname = 'doh.content.' + entry
            mod = __import__(modname)
            mod = mod.content.__dict__[entry]
            for name, item in mod.__dict__.iteritems():
                if not hasattr(item, '__bases__'):
                    continue
                if Handler not in item.__bases__:
                    continue

                plugin = item()
                self.plugins[item] = plugin
                break

    def dispatch(self, req, storage, path):
        handlers = {
            Handler.MUST: [],
            Handler.SHOULD: [],
            Handler.CAN: []
        }
        for name, plugin in self.plugins.iteritems():
            prio = plugin.can_handle(req, path)
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

    def render(self, req, storage, path):
        name = self.dispatch(req, storage, path)
        if name:
            plugin = self.plugins[name]
            return plugin.render(req, storage, path)
