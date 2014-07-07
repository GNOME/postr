# Postr, a Flickr Uploader
#
# Copyright (C) 2008 Ross Burton <ross@burtonini.com>
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51 Franklin
# St, Fifth Floor, Boston, MA 02110-1301 USA

from gi.repository import Gtk, GObject, GdkPixbuf
from ErrorDialog import ErrorDialog
import util

from twisted.python import log

(COL_SELECTED,
 COL_ID,
 COL_NAME,
 COL_ICON) = range(0, 4)

class GroupSelector(Gtk.TreeView):
    __gtype_name__ = 'GroupSelector'
    __gsignals__ = {
        'changed' : (GObject.SignalFlags.RUN_LAST, None, ())
        }

    def __init__(self):
        self.flickr = None
        self.model = Gtk.ListStore(GObject.TYPE_BOOLEAN,
                                   GObject.TYPE_STRING,
                                   GObject.TYPE_STRING,
                                   GdkPixbuf.Pixbuf)
        self.model.connect("row-changed", lambda model, path, iter: self.emit("changed"))

        Gtk.TreeView.__init__(self, self.model)

        # Calculate the size of thumbnails based on the size of the text
        # renderer, but provide a default in case style-set isn't called.
        self.connect("style-set", self.style_set);
        self.thumb_size = 24

        column = Gtk.TreeViewColumn('Selected')
        self.append_column(column)

        renderer = Gtk.CellRendererToggle()
        def toggled(r, path):
            self.model[path][COL_SELECTED] = not r.get_active()
        renderer.connect("toggled", toggled)
        column.pack_start(renderer, False)
        column.add_attribute(renderer, "active", COL_SELECTED)

        column = Gtk.TreeViewColumn('Group')
        self.append_column(column)

        renderer = Gtk.CellRendererPixbuf()
        column.pack_start(renderer, False)
        column.add_attribute(renderer, "pixbuf", COL_ICON)

        self.text_renderer = Gtk.CellRendererText()
        column.pack_start(self.text_renderer, True)
        column.add_attribute(self.text_renderer, "text", COL_NAME)

        # FIXME: Port to GTK3
        # self.set_size_request(-1, 24 * 3 + self.style_get_property("vertical-separator") * 6)
        self.set_headers_visible(False)
        self.set_search_column(COL_NAME)
        def search_func(model, column, key, iter, user_data):
            s = model.get_value(iter, column)
            # This API is braindead, false=matches
            return key.lower() not in s.lower()
        self.set_search_equal_func(search_func, None)
        # TODO: enable case insensitive substring searching

    def style_set(self, widget, old_style):
        self.thumb_size = self.text_renderer.get_size(self, None)[3]

    def update(self):
        # TODO: block changed signals
        deferred = self.flickr.groups_pools_getGroups()
        deferred.addCallback(self.got_groups)
        deferred.addErrback(self.twisted_error)

    def got_groups(self, rsp):
        for group in rsp.findall("groups/group"):
            it = self.model.append()
            self.model.set (it,
                            COL_ID, group.get("id"),
                            COL_NAME, group.get("name"))
            def got_thumb(thumb, it):
                self.model.set (it, COL_ICON, thumb)

            deferred = util.get_buddyicon(self.flickr, group, self.thumb_size)
            deferred.addCallback(got_thumb, it)
            deferred.addErrback(self.twisted_error)

    def twisted_error(self, failure):
        dialog = ErrorDialog()
        dialog.set_from_failure(failure)
        dialog.show_all()

        log.err(failure, 'Exception in %s' % self.__gtype_name__)
        return failure

    def get_selected_groups(self):
        return [row[COL_ID] for row in self.model if row[COL_SELECTED]]

    def set_selected_groups(self, groups):
        # Handle groups being None */
        if groups is None: groups = ()
        for row in self.model:
            row[COL_SELECTED] = row[COL_ID] in groups
