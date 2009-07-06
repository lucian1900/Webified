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
    
    Much of the initialisation code if from Pippy'''
    
    __gtype_name__ = 'SugarSourceEditor'
    
    def __init__(self, mime_type='text/plain', width=None, height=None):
        gtk.ScrolledWindow.__init__(self)
        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
         
        self.mime_type = mime_type
        self.width = width or int(gtk.gdk.screen_width()/2)
        self.height = height or int(gtk.gdk.screen_height()/1.5)
        
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
        self._view.set_size_request(self.width, self.height)
        self._view.set_editable(True)
        self._view.set_cursor_visible(True)
        self._view.set_show_line_numbers(True)
        self._view.set_wrap_mode(gtk.WRAP_CHAR)
        self._view.set_auto_indent(True)
        self._view.modify_font(pango.FontDescription("Monospace " +
                              str(style.FONT_SIZE)))

        self.add(self._view)
        self.show_all()

    def get_text(self):
        end = self._buffer.get_end_iter()
        start = self._buffer.get_start_iter()
        return self._buffer.get_text(start, end)
        
    def set_text(self, text):
        self._buffer.set_text(text)
        
    text = property(get_text, set_text)

class TextEditor(gtk.Window):
    def __init__(self, mime_type='text/html', width=None, height=None):
        gtk.Window.__init__(self)
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
        
        self.mime_type = mime_type
        self.width = width or int(gtk.gdk.screen_width()/2)
        self.height = height or int(gtk.gdk.screen_height()/1.5)
        
        # layout
        vbox = gtk.VBox()
        editorbox = gtk.HBox()
        buttonbox = gtk.HBox()
        
        # editor buffer
        self.buffer = gtksourceview2.Buffer()
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
                    self.buffer.set_language(lang)

        if hasattr(self.buffer, 'set_highlight'):
            self.buffer.set_highlight(True)
        else:
            self.buffer.set_highlight_syntax(True)

        # editor view
        view = gtksourceview2.View(self.buffer)
        view.set_size_request(self.width, self.height)
        view.set_editable(True)
        view.set_cursor_visible(True)
        view.set_show_line_numbers(True)
        view.set_wrap_mode(gtk.WRAP_CHAR)
        view.set_auto_indent(True)
        view.modify_font(pango.FontDescription("Monospace " +
                              str(style.FONT_SIZE)))

        codesw = gtk.ScrolledWindow()
        codesw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        codesw.add(view)
        #editorbox.pack_start(codesw)
        
        #vbox.pack_start(editorbox)
        vbox.pack_start(codesw)
        
        # buttons
        self._cancel_button = gtk.Button(label=_('Cancel'))
        self._cancel_button.set_image(Icon(icon_name='dialog-cancel'))
        self._cancel_button.connect('clicked', self._cancel_button_cb)
        buttonbox.pack_start(self._cancel_button)
        
        self._save_button = gtk.Button(label=_('Save'))
        self._save_button.set_image(Icon(icon_name='dialog-ok'))
        buttonbox.pack_start(self._save_button)
        
        self._apply_button = gtk.Button(label=_('Apply'))
        self._apply_button.set_image(Icon(icon_name='dialog-ok'))
        buttonbox.pack_start(self._apply_button)
        
        vbox.pack_start(buttonbox)
        self.add(vbox)
        
    def _cancel_button_cb(self, button):
        self.destroy()
    
    def show(self):
        self.show_all()
        gtk.Window.show(self)
        
    def get_text(self):
        end = self.buffer.get_end_iter()
        start = self.buffer.get_start_iter()
        return self.buffer.get_text(start, end)
        
    def set_text(self, text):
        self.buffer.set_text(text)
        
    text = property(get_text, set_text)


class StyleEditor(TextEditor):
    __gsignals__ = {
        'userstyle-changed': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE,
                             ([])),
    }
    
    def __init__(self):
        TextEditor.__init__(self, mime_type='text/css')

        self.css_path = os.path.join(activity.get_activity_root(),
                                     'data/style.user.css')
                                     
        self._save_button.connect('clicked', self._save_button_cb)
        self._apply_button.connect('clicked', self._apply_button_cb)
        
        if os.path.isfile(self.css_path):
            f = open(self.css_path, 'r')
            self.text = f.read()
            f.close()
        
    def _apply_button_cb(self, button):
        f = open(self.css_path, 'w')
        f.write(self.text)
        f.close()
        
        self.emit('userstyle-changed')
        
    def _save_button_cb(self, button):
        self._apply_button_cb(button)
        
        self.destroy()

# TODO support multiple userscripts
class ScriptEditor(TextEditor):
    __gsignals__ = {
        'inject-script': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE,
                             ([str])),
    }

    def __init__(self):
        TextEditor.__init__(self, mime_type='text/javascript')
        
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
