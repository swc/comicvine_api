#!/usr/bin/env python
#encoding:utf-8
#author:swc/Steve
#project:comicvine_api
#repository:http://github.com/swc/comicvine_api
#license:Creative Commons GNU GPL v2
# (http://creativecommons.org/licenses/GPL/2.0/)

"""Contains included user interfaces for Comicvine volume selection.
Modified from http://github.com/dbr/tvdb_api

A UI is a callback. A class, it's __init__ function takes two arguments:

- config, which is the Comicvine config dict, setup in comicvine_api.py
- log, which is Comicvine's logger instance (which uses the logging module). You can
call log.info() log.warning() etc

It must have a method "selectvolume", this is passed a list of dicts, each dict
contains the the keys "name" (human readable volume name), and "sid" (the volume
ID as on comicvine.com). For example:

[{'name': u'Lost', 'sid': u'73739'},
 {'name': u'Lost Universe', 'sid': u'73181'}]

The "selectvolume" method must return the appropriate dict, or it can raise
comicvine_userabort (if the selection is aborted), comicvine_volumenotfound (if the volume
cannot be found).

A simple example callback, which returns a random volume:

>>> import random
>>> from comicvine_ui import BaseUI
>>> class RandomUI(BaseUI):
...    def selectvolume(self, allvolume):
...            import random
...            return random.choice(allvolume)

Then to use it..

>>> from comicvine_api import Comicvine
>>> c = Comicvine(custom_ui = RandomUI)
>>> random_matching_volume = c['Fables']
>>> type(random_matching_volume)
<class 'comicvine_api.volume'>
"""

__author__ = "swc/Steve"
__version__ = "1.01"

import logging
import warnings

from comicvine_exceptions import comicvine_userabort

def log():
    return logging.getLogger(__name__)

class BaseUI:
    """Default non-interactive UI, which auto-selects first results
    """
    def __init__(self, config, log = None):
        self.config = config
        if log is not None:
            warnings.warn("the UI's log parameter is deprecated, instead use\n"
                "use import logging; logging.getLogger('ui').info('blah')\n"
                "The self.log attribute will be removed in the next version")
            self.log = logging.getLogger(__name__)

    def selectvolume(self, allvolume):
        return allvolume[0]


class ConsoleUI(BaseUI):
    """Interactively allows the user to select a volume from a console based UI
    """

    def _displayvolume(self, allvolume):
        """Helper function, lists volume with corresponding ID
        """
        print "ComicVine Search Results:"
        for i, cvolume in enumerate(allvolume[:6]):
            i_volume = i + 1 # Start at more human readable number 1 (not 0)
            log().debug('Showing allvolume[%s], volume %s)' % (i_volume, allvolume[i]['volumename']))
            print "%s -> %s # http://api.comicvine.com/volume/%s/" % (
                i_volume,
                cvolume['volumename'].encode("UTF-8", "ignore"),
                str(cvolume['id'])
            )

    def selectvolume(self, allvolume):
        self._displayvolume(allvolume)

        if len(allvolume) == 1:
            # Single result, return it!
            print "Automatically selecting only result"
            return allvolume[0]

        if self.config['select_first'] is True:
            print "Automatically returning first search result"
            return allvolume[0]

        while True: # return breaks this loop
            try:
                print "Enter choice (first number, ? for help):"
                ans = raw_input()
            except KeyboardInterrupt:
                raise comicvine_userabort("User aborted (^c keyboard interupt)")
            except EOFError:
                raise comicvine_userabort("User aborted (EOF received)")

            log().debug('Got choice of: %s' % (ans))
            try:
                selected_id = int(ans) - 1 # The human entered 1 as first result, not zero
            except ValueError: # Input was not number
                if ans == "q":
                    log().debug('Got quit command (q)')
                    raise comicvine_userabort("User aborted ('q' quit command)")
                elif ans == "?":
                    print "## Help"
                    print "# Enter the number that corresponds to the correct volume."
                    print "# ? - this help"
                    print "# q - abort comicnamer"
                else:
                    log().debug('Unknown keypress %s' % (ans))
            else:
                log().debug('Trying to return ID: %d' % (selected_id))
                try:
                    return allvolume[ selected_id ]
                except IndexError:
                    log().debug('Invalid volume number entered!')
                    print "Invalid number (%s) selected!"
                    self._displayvolume(allvolume)
            #end try
        #end while not valid_input

