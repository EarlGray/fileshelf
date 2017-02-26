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
        raise NotImplementedError('Handler.render')
