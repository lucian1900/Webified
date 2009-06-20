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
import ConfigParser

from sugar.activity import activity
from sugar.graphics.toolbutton import ToolButton

class SSBToolbar(gtk.Toolbar):
    def __init__(self, activity):
        gtk.Toolbar.__init__(self)
        
        self._activity = activity
        self._browser = self._activity._browser
        
        self.bookmarklet = ToolButton('bookmarklet')
        self.bookmarklet.set_tooltip(_('Add bookmarklet'))
        self.bookmarklet.connect('clicked', self.__bookmarklet_clicked_cb)
        self.insert(self.bookmarklet, -1)
        self.bookmarklet.show()
        
        self._set_bm_config()

        self._set_bookmarklet('google', 'http://google.com', 'bla')
        
    def _set_bm_config(self):
        self._bm_config = ConfigParser.ConfigParser()
        self.config_path = activity.get_activity_root()
        self.config_path = os.path.join(self.config_path,
                                        'data/ssb/bookmarklets.info')
        self._bm_config.read(self.config_path)

        logging.debug(self.config_path)

    def _write_bm_config(self):
        f = open(self.config_path, 'w')
        self._bm_config.write(f)    
        f.close()

    def _get_bookmarklet(self, name):
        uri = self._bm_config.get(name, 'uri')
        description = self._bm_config.get(name, 'description')
        return uri, description
        
    def _set_bookmarklet(self, name, uri, description):
        self._bm_config.add_section(name)
        self._bm_config.set(name, 'uri', uri)
        self._bm_config.set(name, 'description', description)
    
    def __bookmarklet_clicked_cb(self, button):
        logging.debug('add bookmarklet clicked')
        # TODO everything
        self._write_bm_config()
        
