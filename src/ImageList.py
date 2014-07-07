# Postr, a Flickr Uploader
# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2008 Ross Burton <ross@burtonini.com>
# Copyright (C) 2012 Germán Poo-Caamaño <gpoo@gnome.org>
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

from gi.repository import Gtk, Pango, Gdk

import ImageStore

# Constants for the drag handling
(DRAG_URI,
 DRAG_IMAGE) = range (0, 2)

class ImageList(Gtk.TreeView):
    __gtype_name__ = 'ImageList'

    def __init__(self):
        Gtk.TreeView.__init__(self)

        column = Gtk.TreeViewColumn('Preview',
                                    Gtk.CellRendererPixbuf(),
                                    pixbuf=ImageStore.COL_THUMBNAIL)

        self.append_column(column)

        renderer = Gtk.CellRendererText()
        renderer.set_property('ellipsize', Pango.EllipsizeMode.END)

        column = Gtk.TreeViewColumn('Info', renderer)
        column.set_cell_data_func(renderer, self.data_func)
        self.append_column(column)

        self.set_headers_visible(False)
        self.set_enable_search(False)

        selection = self.get_selection()
        selection.set_mode(Gtk.SelectionMode.MULTIPLE)

        # Setup the drag and drop
        self.targets = self.drag_dest_get_target_list()
        if not self.targets:
            self.targets = Gtk.TargetList.new([])
        self.targets.add_image_targets (DRAG_IMAGE, True)
        self.targets.add_uri_targets (DRAG_URI)
        self.drag_dest_set (Gtk.DestDefaults.ALL, [], Gdk.DragAction.COPY)
        self.drag_dest_set_target_list(self.targets)

    def enable_targets(self):
        """Enable the drag and drop destination. """
        self.drag_dest_set(Gtk.DestDefaults.ALL, [], Gdk.DragAction.COPY)
        self.drag_dest_set_target_list(self.targets)

    def unable_targets(self):
        """Unable the drag and drop destination. """
        self.drag_dest_unset()

    def data_func(self, column, cell, model, it, data):
        from xml.sax.saxutils import escape

        (title, description, tags) = model.get(it, ImageStore.COL_TITLE, ImageStore.COL_DESCRIPTION, ImageStore.COL_TAGS)

        if title:
            info_title = title
        else:
            info_title = _("No title")

        if description:
            # Clip the description because it could be long and have multiple lines
            # TODO: Clip at 20 characters, or the first line.
            info_desc = description[:20]
        else:
            info_desc = ""

        s = "<b><big>%s</big></b>\n%s\n" % (escape (info_title), escape (info_desc))
        if tags:
            s = s + '%s' % (escape (tags))

        cell.set_property("markup", s)

