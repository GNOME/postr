# Postr, a Flickr Uploader
#
# Copyright (C) 2006-2008 Ross Burton <ross@burtonini.com>
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

from gi.repository import GObject, Gtk

class SafetyCombo(Gtk.ComboBox):
    __gtype_name__ = 'SafetyCombo'

    def __init__(self):
        Gtk.ComboBox.__init__(self)
        # Name, is_public, is_family, is_friend
        model = Gtk.ListStore(GObject.TYPE_STRING, GObject.TYPE_INT)
        model.append(["Safe", 1])
        model.append(["Moderate", 2])
        model.append(["Restricted", 3])
        self.model = model
        self.set_model(model)
        self.set_active(0)

        cell = Gtk.CellRendererText()
        self.pack_start(cell, True)
        self.add_attribute(cell, "text", 0)

    def get_safety_for_iter(self, it):
        if it is None: return None
        return self.model.get_value(it, 1)

    def get_active_safety(self):
        return self.get_safety_for_iter(self.get_active_iter())
