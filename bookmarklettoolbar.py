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

from gettext import gettext as _
import os
import gtk
import logging
import gobject

from sugar.graphics.toolbutton import ToolButton
from sugar.graphics.palette import Palette

import bookmarklets

# HACK until we have toolbox.get_toolbars()
_TOOLBAR_BROWSE = 2
_TOOLBAR_BOOKMARKLETS = 4

def alert(activity, text):
    from sugar.graphics.alert import NotifyAlert
        
    a = NotifyAlert()
    a.props.title = 'DEBUG'
    a.props.msg = str(text)
    activity.add_alert(a)
    a.show()

class BookmarkletButton(ToolButton):
    def __init__(self, toolbar, name, uri):
        self._name = name
        self._uri = uri
        self._toolbar = toolbar
        self._browser = toolbar._activity._browser
    
        # set up the button
        ToolButton.__init__(self, 'bookmarklet')
        self.connect('clicked', self._clicked_cb)
        toolbar.insert(self, -1)
        
        # and its palette
        palette = Palette(name, text_maxlen=50)
        self.set_palette(palette)
        
        menu_item = gtk.MenuItem(_('Remove'))
        menu_item.connect('activate', self._remove_cb)
        palette.menu.append(menu_item)
        menu_item.show()
            
    def animate(self):          
        gobject.timeout_add(500, self.set_icon, 'bookmarklet-thick')
        gobject.timeout_add(800, self.set_icon, 'bookmarklet')
        
    def flash(self):
        gobject.timeout_add(500, self.set_icon, 'bookmarklet-inverted')
        gobject.timeout_add(800, self.set_icon, 'bookmarklet')
                    
    def _clicked_cb(self, button):
        self._browser.load_uri(self._uri)

    def _remove_cb(self, widget):
        bookmarklets.get_store().remove(self._name)
        del self._toolbar.bookmarklets[self._name]        
        self.destroy()
        
        #alert(self._activity, self._toolbar.bookmarklets)
        if len(self._toolbar.bookmarklets) == 0:
            self._toolbar.destroy()
        
class BookmarkletToolbar(gtk.Toolbar):
    def __init__(self, activity):
        gtk.Toolbar.__init__(self)
        
        self._activity = activity
        self._browser = self._activity._browser

        self.store = bookmarklets.get_store()
        
        self.bookmarklets = {}
            
    def _add_bookmarklet(self, name):
        url = self.store.get(name)
        bm = BookmarkletButton(self, name, url)
        self.bookmarklets[name] = bm
        bm.show()
        
    def destroy(self):
        self._activity.toolbox.remove_toolbar(_TOOLBAR_BOOKMARKLETS)
        self._activity.toolbox.set_current_toolbar(_TOOLBAR_BROWSE)
        
        gtk.Toolbar.destroy(self)