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

from sourceedit import SourceView
from jarabe.view.viewsource import FileViewer #HACK

SCRIPTS_PATH = os.path.join(activity.get_activity_root(),
                            'data/userscripts')
STYLE_PATH = os.path.join(activity.get_activity_root(),
                          'data/style.user.css')

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
        
        # layout
        vbox = gtk.VBox()
        
        self.editor = SourceView()
        self.editor.file_path = STYLE_PATH
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

    def _save_button_cb(self, button):
        self.editor.write()
        self.emit('userstyle-changed')
        self.destroy()
        
    def _cancel_button_cb(self, button):
        self.destroy()

class ScriptEditor(Dialog):
    def __init__(self):
        Dialog.__init__(self)
                                        
        # layout
        hbox = gtk.HBox()
        
        self.fileview = FileViewer(SCRIPTS_PATH, 'test.user.js')
        self.fileview.connect('file-selected', self._file_selected_cb)
        hbox.pack_start(self.fileview)
        
        editbox = gtk.VBox()        
        self.editor = SourceView()
        editbox.pack_start(self.editor)
                                        
        buttonbox = gtk.HBox()

        self._cancel_button = gtk.Button(label=_('Close'))
        self._cancel_button.set_image(Icon(icon_name='dialog-cancel'))
        self._cancel_button.connect('clicked', self._cancel_button_cb)
        buttonbox.pack_start(self._cancel_button)
        
        self._delete_button = gtk.Button(label=_('Delete'))
        self._delete_button.set_image(Icon(icon_name='stock_delete'))
        self._delete_button.connect('clicked', self._delete_button_cb)
        buttonbox.pack_start(self._delete_button)
        
        self._save_button = gtk.Button(label=_('Save'))
        self._save_button.set_image(Icon(icon_name='dialog-ok'))
        self._save_button.connect('clicked', self._save_button_cb)
        buttonbox.pack_start(self._save_button)
        
        editbox.pack_start(buttonbox)
        hbox.pack_start(editbox)
        
        self.add(hbox)
        
        # HACK
        self._file_selected_cb(self.fileview, 
                               self.fileview._initial_filename)

    def _get_selected_file(self):
        # HACK
        selection = self.fileview._tree_view.get_selection()
        model, tree_iter = selection.get_selected()
        if tree_iter is None:
            return None
        else:
            return model.get_value(tree_iter, 1)
    
    def _save_button_cb(self, button):
        self.editor.write()
        
    def _delete_button_cb(self, button):
        file_path = self._get_selected_file()
                
        # HACK remove from model
        model = self.fileview._tree_view.get_model()
        for i in model:
            if i[0] == os.path.basename(file_path):
                model.remove(model.get_iter(i.path))
                break
        
        # remove actual file
        os.remove(file_path)
        
    def _cancel_button_cb(self, button):
        self.destroy()
        
    def _file_selected_cb(self, view, file_path):
        self.editor.file_path = self._get_selected_file()

def add_script(location):
    cls = components.classes["@mozilla.org/network/io-service;1"]
    io_service = cls.getService(interfaces.nsIIOService)

    cls = components.classes[ \
                        '@mozilla.org/embedding/browser/nsWebBrowserPersist;1']
    browser_persist = cls.getService(interfaces.nsIWebBrowserPersist)


    location_uri = io_service.newURI(location, None, None)

    file_name = os.path.basename(location_uri.path)
    file_path = os.path.join(SCRIPTS_PATH, file_name)
    file_uri = io_service.newURI('file://'+file_path, None, None)

    logging.debug('##### %s -> %s' % (location_uri.spec, file_uri.spec))

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
    
    def onLocationChange(self, webProgress, request, location):
        if location.spec.endswith('.user.js'):
            self.emit('userscript-found', location.spec)
        else:
            # TODO load scripts according to domain regex
            for i in os.listdir(SCRIPTS_PATH):                
                script_path = os.path.join(SCRIPTS_PATH, i)
                self.emit('userscript-inject', script_path)

    def setup(self, browser):
        browser.web_progress.addProgressListener(self._wrapped, 
                                interfaces.nsIWebProgress.NOTIFY_LOCATION)