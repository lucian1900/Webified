# Copyright (C) 2007, One Laptop Per Child
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

from gettext import gettext as _
import os
import gtk
import logging

from sugar.graphics.toolbutton import ToolButton

import ssb

class BookmarkletButton(ToolButton):
    def __init__(self, toolbar, name, uri):
        self._name = name
        self._uri = uri
        self._toolbar = toolbar
        self._browser = toolbar._activity._browser
    
        # set up button
        ToolButton.__init__(self, 'bm-' + self._name)
        self.set_tooltip(self._name)
        self.connect('clicked', self._clicked_cb)
        toolbar.insert(self, -1)
        
    def _clicked_cb(self, button):
        logging.debug('clicked ' + self._name)
        self._browser.load_uri(self._uri)

class BookmarkletToolbar(gtk.Toolbar):
    def __init__(self, activity):
        gtk.Toolbar.__init__(self)
        
        self._activity = activity
        self._browser = self._activity._browser

        # set up the bookmarklet ConfigParser
        self._bm_store = ssb.get_bm_store()
        
        # DEBUG
        #self._set_bookmarklet('google', 'http://google.com')
        #self._set_bookmarklet('hello', 'javascript:alert("hello");')
        
        self.bookmarklets = {}
        
        # add buttons for each stored bookmarklet
        for name in self._bm_store.list():
            uri = self._bm_store.get(name)
            bm = BookmarkletButton(self, name, uri)
            self.bookmarklets[name] = bm
            bm.show()
        