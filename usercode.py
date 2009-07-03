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

import os
import logging

import gtk
import pango
import gtksourceview2

from sugar.graphics import style

class TextEditor(gtk.Window):
    def __init__(self, mime_type='text/html', width=None, height=None):
        gtk.Window.__init__(self)
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
        
        self.mime_type = mime_type
        self.width = int(gtk.gdk.screen_width()/2)
        self.height = int(gtk.gdk.screen_height()/1.5)
        
        self.buffer = gtksourceview2.Buffer()
        lang_manager = gtksourceview2.language_manager_get_default()
        if hasattr(lang_manager, 'list_languages'):
            langs = lang_manager.list_languages()
        else:
            lang_ids = lang_manager.get_language_ids()
            langs = [lang_manager.get_language(lang_id) for lang_id in lang_ids]
        for lang in langs:
            for m in lang.get_mime_types():
                if m == self.mime_type:
                    self.buffer.set_language(lang)

        if hasattr(self.buffer, 'set_highlight'):
            self.buffer.set_highlight(True)
        else:
            self.buffer.set_highlight_syntax(True)

        # The GTK source view window
        self.view = gtksourceview2.View(self.buffer)
        self.view.set_size_request(self.width, self.height)
        self.view.set_editable(True)
        self.view.set_cursor_visible(True)
        self.view.set_show_line_numbers(True)
        self.view.set_wrap_mode(gtk.WRAP_CHAR)
        self.view.set_auto_indent(True)
        self.view.modify_font(pango.FontDescription("Monospace " +
                              str(style.FONT_SIZE)))

        codesw = gtk.ScrolledWindow()
        codesw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        codesw.add(self.view)

        self.add(codesw)
            
    def show(self):
        self.show_all()
        gtk.Window.show(self)
        
class StyleEditor(TextEditor):
    def __init__(self):
        TextEditor.__init__(self, mime_type='text/css')