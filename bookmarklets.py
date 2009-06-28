# Copyright (C) 2009, Lucian Branescu Mihaila
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import ConfigParser
import os
import gobject
import logging

from sugar.activity import activity

_store = None

def get_store():
    global _store
    if _store is None:
        _store = BookmarkletStore()
    return _store
    
class BookmarkletStore(gobject.GObject):
    __gsignals__ = {
        'add_bookmarklet': (gobject.SIGNAL_RUN_FIRST,
                            gobject.TYPE_NONE, ([str])),
        'overwrite_bookmarklet': (gobject.SIGNAL_RUN_FIRST,
                                  gobject.TYPE_NONE, ([str, str])),
    }
        
    def __init__(self):
        gobject.GObject.__init__(self)    
        
        self._config = ConfigParser.RawConfigParser()
        self.config_path = activity.get_activity_root()
        self.config_path = os.path.join(self.config_path,
                                        'data/bookmarklets.info')
        self._config.read(self.config_path)

    def __del__(self):
        '''Save bookmarklets (usually when the activity is closed)'''
        self.write()

    def write(self):
        # create data/ssb dir if it doesn't exist
        dir_path = os.path.dirname(self.config_path)
        if not os.path.isdir(dir_path):
            os.mkdir(dir_path)
        
        # write config
        f = open(self.config_path, 'w')
        self._config.write(f)    
        f.close()

    def list(self):
        return self._config.sections()
        
    def remove(self, name):
        self._config.remove_section(name)
        self.write()

    def get(self, name):
        return self._config.get(name, 'url')
    
    def add(self, name, url):        
        if not self._config.has_section(name):
            self._config.add_section(name)
            self._config.set(name, 'url', url) 
            self.write()       
        elif self.get(name) != url:
            self.emit('overwrite_bookmarklet', name, url)
        
        # we don't care when the bookmarklet was added
        if self._config.has_section(name) and self.get(name) == url:
            self.emit('add_bookmarklet', name)
        

