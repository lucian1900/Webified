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

import gtk

from sugar.graphics.toolbutton import ToolButton

class SSBToolbar(gtk.Toolbar):
    def __init__(self, activity):
        gtk.Toolbar.__init__(self)

        self._activity = activity        
        self._activity.tray.connect('unmap', self.__unmap_cb)
        self._activity.tray.connect('map', self.__map_cb)

        self._browser = self._activity._browser
        
        self.bookmarklet = ToolButton('bookmarklet')
        self.bookmarklet.set_tooltip(_('Add bookmarklet'))
        self.bookmarklet.connect('clicked', self.__bookmarklet_clicked_cb)
        self.insert(self.bookmarklet, -1)
        self.bookmarklet.show()
                
    def __bookmarklet_clicked_cb(self, button):
        logging.debug('add bookmarklet clicked')
        
    def __tray_clicked_cb(self, button):        
        if self._activity.tray.props.visible is False:
            self._activity.tray.show()
        else:
            self._activity.tray.hide()

    def __map_cb(self, tray):
        if len(self._activity.tray.get_children()) > 0:
            self.tray_set_hide()
             
    def __unmap_cb(self, tray):
        if len(self._activity.tray.get_children()) > 0:
            self.tray_set_show()
        
    def tray_set_show(self):     
        self.traybutton.set_icon('tray-show')
        self.traybutton.set_tooltip(_('Show Tray'))
        
    def tray_set_hide(self):
        self.traybutton.set_icon('tray-hide')
        self.traybutton.set_tooltip(_('Hide Tray'))
        
