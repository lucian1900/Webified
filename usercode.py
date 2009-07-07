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

import os
import logging
from gettext import gettext as _

import gobject
import gtk
import pango
import gtksourceview2

import xpcom
from xpcom.components import interfaces

from sugar.activity import activity
from sugar.graphics import style
from sugar.graphics.icon import Icon


class SourceEditor(gtk.ScrolledWindow):
    '''TextView-like widget with syntax coloring and scroll bars
    
    Much of the initialisation code is from Pippy'''
    
    __gtype_name__ = 'SugarSourceEditor'
    
    def __init__(self, mime_type='text/plain', width=None, height=None):
        gtk.ScrolledWindow.__init__(self)
        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
         
        self.mime_type = mime_type
        
        self._buffer = gtksourceview2.Buffer()
        lang_manager = gtksourceview2.language_manager_get_default()
        if hasattr(lang_manager, 'list_languages'):
            langs = lang_manager.list_languages()
        else:
            lang_ids = lang_manager.get_language_ids()
            langs = [lang_manager.get_language(lang_id) 
                                        for lang_id in lang_ids]
        for lang in langs:
            for m in lang.get_mime_types():
                if m == self.mime_type:
                    self._buffer.set_language(lang)

        if hasattr(self._buffer, 'set_highlight'):
            self._buffer.set_highlight(True)
        else:
            self._buffer.set_highlight_syntax(True)
        
        # editor view
        self._view = gtksourceview2.View(self._buffer)
        self._view.set_editable(True)
        self._view.set_cursor_visible(True)
        self._view.set_show_line_numbers(True)
        self._view.set_wrap_mode(gtk.WRAP_CHAR)
        self._view.set_auto_indent(True)
        self._view.modify_font(pango.FontDescription("Monospace " +
                              str(style.FONT_SIZE)))
                              
        if width is not None and height is not None:
            self._view.set_size_request(width, height)

        self.add(self._view)
        self.show_all()

    def get_text(self):
        end = self._buffer.get_end_iter()
        start = self._buffer.get_start_iter()
        return self._buffer.get_text(start, end)
        
    def set_text(self, text):
        self._buffer.set_text(text)
        
    text = property(get_text, set_text)
    
class Dialog(gtk.Window):
    def __init__(self, width=None, height=None):        
        self.width = width or int(gtk.gdk.screen_width()/2)
        self.height = height or int(gtk.gdk.screen_height()/1.5)
        
        gtk.Window.__init__(self)
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
        self.set_default_size(self.width, self.height)

class StyleEditor(Dialog):
    __gsignals__ = {
        'userstyle-changed': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE,
                             ([])),
    }
    
    def __init__(self):
        Dialog.__init__(self)
        self.css_path = os.path.join(activity.get_activity_root(),
                                     'data/style.user.css')
                
        # layout
        vbox = gtk.VBox()
        
        self.editor = SourceEditor('text/css', self.width, self.height)
        vbox.pack_start(self.editor)
        
        # buttons
        buttonbox = gtk.HBox()
        
        self._cancel_button = gtk.Button(label=_('Cancel'))
        self._cancel_button.set_image(Icon(icon_name='dialog-cancel'))
        self._cancel_button.connect('clicked', self._cancel_button_cb)
        buttonbox.pack_start(self._cancel_button)
        
        self._save_button = gtk.Button(label=_('Save'))
        self._save_button.set_image(Icon(icon_name='dialog-ok'))
        self._save_button.connect('clicked', self._save_button_cb)
        buttonbox.pack_start(self._save_button)
                                             
        vbox.pack_start(buttonbox)
        
        self.add(vbox)
        self.show_all()

        # load user sheet, if any
        if os.path.isfile(self.css_path):
            f = open(self.css_path, 'r')
            self.editor.text = f.read()
            f.close()

    def _save_button_cb(self, button):
        f = open(self.css_path, 'w')
        f.write(self.editor.text)
        f.close()
        
        self.emit('userstyle-changed')
        
        self.destroy()
        
    def _cancel_button_cb(self, button):
        self.destroy()

# TODO support multiple userscripts
class ScriptEditor(Dialog):
    __gsignals__ = {
        'inject-script': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE,
                             ([str])),
    }

    def __init__(self):
        Dialog.__init__(self)
        
        self.script_path = os.path.join(activity.get_activity_root(),
                                        'data/script.user.js')
                                        
        self._save_button.connect('clicked', self._save_button_cb)
        
    def _save_button_cb(self, button):
        self.emit('inject-script', self.text)
        
        self.destroy()
        
class ScriptListener(gobject.GObject):
    _com_interfaces_ = interfaces.nsIWebProgressListener

    __gsignals__ = {
        'userscript-found': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE,
                             ([])),
    }

    def __init__(self):
        gobject.GObject.__init__(self)

        self._wrapped_self = xpcom.server.WrapObject( \
                self, interfaces.nsIWebProgressListener)

    def onLocationChange(self, webProgress, request, location):
        if location.spec.endswith('.user.js'):
            self.emit('userscript-found')

    def setup(self, browser):
        browser.web_progress.addProgressListener(self._wrapped_self, 
                                interfaces.nsIWebProgress.NOTIFY_LOCATION)
