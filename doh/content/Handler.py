from __future__ import print_function


class Handler:
    # content priority
    DOESNT = 0
    CAN = 1
    SHOULD = 2
    MUST = 3

    def priority(self, req, storage, path):
        """ should return one of Handler.DOESNT, Handler.CAN,
            Handler.SHOULD, Handler.MUST
        """
        raise NotImplementedError('Handler.priority')

    def render(self, req, storage, path):
        """ hanldes GET requests """
        raise NotImplementedError('Handler.render')

    def action(self, req, storage, path):
        """ handles POST requests """
        raise NotImplementedError('Handler.action')

    def _log(self, *msgs):
        print('## ', end='')
        print(*msgs)
