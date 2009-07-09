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
from xpcom import components
from xpcom.components import interfaces

from sugar.activity import activity
from sugar.graphics import style
from sugar.graphics.icon import Icon

from jarabe.view import viewsource


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
        
    def show(self):
        self.show_all()
        gtk.Window.show(self)

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

        # load user sheet, if any
        if os.path.isfile(self.css_path):
            self.editor.text = open(self.css_path, 'r').read()

    def _save_button_cb(self, button):
        open(self.css_path, 'w').write(self.editor.text)
        
        self.emit('userstyle-changed')
        
        self.destroy()
        
    def _cancel_button_cb(self, button):
        self.destroy()


class ScriptEditor(Dialog):
    def __init__(self):
        Dialog.__init__(self)
        self.scripts_path = os.path.join(activity.get_activity_root(),
                                        'data/userscripts')
                                        
        # layout
        hbox = gtk.HBox()
        
        # file viewer
        self.fileview = viewsource.FileViewer(self.scripts_path,
                                                'test.user.js')
        self.fileview.connect('file-selected', self._file_selected_cb)
        hbox.pack_start(self.fileview)
        
        # editor
        editbox = gtk.VBox()
        
        self.editor = SourceEditor('text/javascript', self.width, self.height)
        editbox.pack_start(self.editor)
                                        
        # buttons
        buttonbox = gtk.HBox()

        self._cancel_button = gtk.Button(label=_('Close'))
        self._cancel_button.set_image(Icon(icon_name='dialog-cancel'))
        self._cancel_button.connect('clicked', self._cancel_button_cb)
        buttonbox.pack_start(self._cancel_button)

        self._save_button = gtk.Button(label=_('Save'))
        self._save_button.set_image(Icon(icon_name='dialog-ok'))
        self._save_button.connect('clicked', self._save_button_cb)
        buttonbox.pack_start(self._save_button)       
        
        editbox.pack_start(buttonbox)
        
        hbox.pack_start(editbox)
        
        self.add(hbox)
        
        self._file_selected_cb(self.fileview, 
                               self.fileview._initial_filename)
                
    def _save_button_cb(self, button):
        '''HACK'''
        selection = self.fileview._tree_view.get_selection()
        model, tree_iter = selection.get_selected()
        file_path = model.get_value(tree_iter, 1)
        
        open(file_path, 'w').write(self.editor.text)
        
    def _cancel_button_cb(self, button):
        self.destroy()
        
    def _file_selected_cb(self, view, file_path):
        self.editor.text = open(file_path, 'r').read()
        
def add_script(location):
    logging.debug('##### %s' % location)
    
    cls = components.classes["@mozilla.org/network/io-service;1"]
    io_service = cls.getService(interfaces.nsIIOService)
    
    cls = components.classes[ \
                        '@mozilla.org/embedding/browser/nsWebBrowserPersist;1']
    browser_persist = cls.getService(interfaces.nsIWebBrowserPersist)
    
    location_uri = io_service.newURI(location, None, None)
    file_uri = io_service.newURI('file:///tmp/user.js', None, None)
    
    browser_persist.saveURI(location_uri, None, None, None, None, file_uri)

class Injector():
    _com_interfaces_ = interfaces.nsIDOMEventListener
    
    def __init__(self, script_path):
        self.script_path = script_path
             
        self._wrapped = xpcom.server.WrapObject(
            self, interfaces.nsIDOMEventListener)

    def handleEvent(self, event):
        self.head.appendChild(self.script)
    
    def attach_to(self, window):
        # set up the script element to be injected
        self.script = window.document.createElement('script')
        self.script.type = 'text/javascript'
        #self.script.src = 'file://' + self.script_path # XSS security fail
        
        text = open(self.script_path,'r').read()
        self.script.appendChild( window.document.createTextNode(text) )
        
        # reference to head
        self.head = window.document.getElementsByTagName('head').item(0)   
        
        # actual attaching
        window.addEventListener('load', self._wrapped, False)
    
class ScriptListener(gobject.GObject):
    _com_interfaces_ = interfaces.nsIWebProgressListener

    __gsignals__ = {
        'userscript-found': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE,
                             ([str])),
        'userscript-inject': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE,
                             ([str])),
    }

    def __init__(self):
        gobject.GObject.__init__(self)

        self._wrapped = xpcom.server.WrapObject( \
                self, interfaces.nsIWebProgressListener)
                
        self.scripts_path = os.path.join(activity.get_activity_root(),
                                         'data/userscripts')

    def onLocationChange(self, webProgress, request, location):
        if location.spec.endswith('.user.js'):
            self.emit('userscript-found', location.spec)
        else:
            # TODO load scripts according to domain
            for i in os.listdir(self.scripts_path):                
                script_path = os.path.join(self.scripts_path, i)
                self.emit('userscript-inject', script_path)

    def setup(self, browser):
        browser.web_progress.addProgressListener(self._wrapped, 
                                interfaces.nsIWebProgress.NOTIFY_LOCATION)