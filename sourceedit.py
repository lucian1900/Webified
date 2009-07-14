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

import gobject
import pango
import gtk
import gtksourceview2

from sugar.graphics import style
from sugar import mime

class SourceView(gtk.ScrolledWindow):
    '''TextView-like widget with syntax coloring and scroll bars
    
    Initialisation code from Pippy and viewsource'''
    
    __gtype_name__ = 'SugarSourceView'
    
    def __init__(self, width=None, height=None, syntax_color=True):
        gtk.ScrolledWindow.__init__(self)
        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
         
        self.width = width or int(gtk.gdk.screen_width()/2)
        self.height = height or int(gtk.gdk.screen_height()/1.5)

        self.mime_type = None
        self._file_path = None
        
        # buffer
        self._buffer = gtksourceview2.Buffer()
        if syntax_color:
            if hasattr(self._buffer, 'set_highlight'):
                self._buffer.set_highlight(True)
            else:
            	self._buffer.set_highlight_syntax(True)
            
        # editor view
        self.view = gtksourceview2.View(self._buffer)
        self.view.set_size_request(self.width, self.height)
        self.view.set_editable(True)
        self.view.set_cursor_visible(True)
        self.view.set_show_line_numbers(True)
        self.view.set_wrap_mode(gtk.WRAP_CHAR)
        self.view.set_right_margin_position(80)
        #self.view.set_highlight_current_line(True) #FIXME: Ugly color
        self.view.set_auto_indent(True)
        self.view.modify_font(pango.FontDescription("Monospace " +
                              str(style.FONT_SIZE)))
        self.add(self.view)
        self.view.show()
        
    def set_mime_type(self, mime_type):
        self.mime_type = mime_type
        
        lang_manager = gtksourceview2.language_manager_get_default()
        if hasattr(lang_manager, 'list_languages'):
            langs = lang_manager.list_languages()
        else:
            lang_ids = lang_manager.get_language_ids()
            langs = [lang_manager.get_language(lang_id) 
                                        for lang_id in lang_ids]
        for lang in langs:
            for m in lang.get_mime_types():
                if m == mime_type:
                    self._buffer.set_language(lang)
    
    def get_text(self):
        end = self._buffer.get_end_iter()
        start = self._buffer.get_start_iter()
        return self._buffer.get_text(start, end)
    
    def set_text(self, text):
        self._buffer.set_text(text)
    
    text = property(get_text, set_text)
    
    def _set_file_path(self, file_path):
        if file_path == self._file_path:
            return
        else:
            self._file_path = file_path

        if self._file_path is None:
            self.text = ''
            return

        mime_type = mime.get_for_file(self._file_path)
        self.set_mime_type(mime_type)
    
        self.text = open(self._file_path, 'r').read()
    
    def _get_file_path(self):
        return self._file_path
    
    file_path = property(_get_file_path, _set_file_path)
    
    def write(self, path=None):
        open(path or self.file_path, 'w').write(self.text)
        
class FileViewer(gtk.ScrolledWindow):
    '''TreeView of the contents of a directory
    
    Mostly taken from viewsource.FileViewer'''
    
    __gtype_name__ = 'SugarFileViewer'

    __gsignals__ = {
        'file-selected': (gobject.SIGNAL_RUN_FIRST,
                           gobject.TYPE_NONE,
                           ([str])),
    }

    def __init__(self, path, initial_filename=None):
        gtk.ScrolledWindow.__init__(self)
        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.set_size_request(style.GRID_CELL_SIZE * 3, -1)

        self._path = None
        self._initial_filename = initial_filename

        self._tree_view = gtk.TreeView()
        self.add(self._tree_view)
        self._tree_view.show()

        self._tree_view.props.headers_visible = False
        selection = self._tree_view.get_selection()
        selection.connect('changed', self.__selection_changed_cb)

        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn()
        column.pack_start(cell, True)
        column.add_attribute(cell, 'text', 0)
        self._tree_view.append_column(column)
        self._tree_view.set_search_column(0)

        self.set_path(path)

    def set_path(self, path):
        self.emit('file-selected', None)
        if self._path == path:
            return
        self._path = path
        self._tree_view.set_model(gtk.TreeStore(str, str))
        self._add_dir_to_model(path)

    def _add_dir_to_model(self, dir_path, parent=None):
        model = self._tree_view.get_model()
        for f in os.listdir(dir_path):
            if not f.endswith('.pyc'):
                full_path = os.path.join(dir_path, f)
                if os.path.isdir(full_path):
                    new_iter = model.append(parent, [f, full_path])
                    self._add_dir_to_model(full_path, new_iter)
                else:                    
                    current_iter = model.append(parent, [f, full_path])
                    if f == self._initial_filename:
                        selection = self._tree_view.get_selection()
                        selection.select_iter(current_iter)

    def __selection_changed_cb(self, selection):
        model, tree_iter = selection.get_selected()
        if tree_iter is None:
            file_path = None
        else:
            file_path = model.get_value(tree_iter, 1)
        self.emit('file-selected', file_path)