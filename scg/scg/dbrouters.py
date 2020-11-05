# -*- coding: utf-8 -*-

### built-in ###
#...

### third ###
#...

### own ###
from apps.help.models import Help


class MyDBRouter(object):

    def db_for_read(self, model, **hints):
        """ reading Help from help """
        if model == Help:
            return 'help'
        return None

    def db_for_write(self, model, **hints):
        """ writing Help to help """
        if model == Help:
            return 'help'
        return None
