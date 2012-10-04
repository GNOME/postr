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
from twisted.python import log

class LicenseCombo(Gtk.ComboBox):
    __gtype_name__ = 'LicenseCombo'

    def __init__(self):
        Gtk.ComboBox.__init__(self)
        self.flickr = None

        self.model = Gtk.ListStore(GObject.TYPE_STRING, GObject.TYPE_INT)
        self.model.append([_("Default"), -1])
        self.set_model(self.model)
        self.set_active(-1)

        cell = Gtk.CellRendererText()
        self.pack_start(cell, True)
        self.add_attribute(cell, "text", 0)

    def __got_licenses(self, rsp):
        """Callback for the photos.licenses.getInfo call"""
        for license in rsp.findall("licenses/license"):
            license_id = int(license.get("id"))
            self.model.append([license.get("name"), license_id])

    def update(self):
        deferred = self.flickr.photos_licenses_getInfo()
        deferred.addCallback(self.__got_licenses)
        deferred.addErrback(log.err)

    def get_license_for_iter(self, it):
        if it is None: return None

        '''There is no way yet to get the default license using the
           API provided by Flickr.  However, if we return None, Flickr
           will set the default defined by the user.  In our case,
           Default was defined as -1.'''
        value = self.model.get_value(it, 1)
        if value == -1:
            return None
        else:
            return value

    def get_active_license(self):
        return self.get_license_for_iter(self.get_active_iter())
