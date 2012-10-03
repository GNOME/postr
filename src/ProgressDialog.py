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

from gi.repository import Gtk, GObject

class ProgressDialog(Gtk.Dialog):
    def __init__(self, cancel_cb):
        Gtk.Dialog.__init__(self, title="")
        self.cancel_cb = cancel_cb

        self.set_resizable(False)
        self.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        self.connect("response", self.on_response)

        vbox = Gtk.VBox(False, 8)
        vbox.set_border_width(8)
        self.get_children()[0].add(vbox)

        hbox = Gtk.HBox(False, 8)
        vbox.add (hbox)

        self.thumbnail = Gtk.Image()
        hbox.pack_start (self.thumbnail, False, False, 0)

        self.label = Gtk.Label()
        self.label.set_alignment (0.0, 0.0)
        hbox.pack_start (self.label, True, True, 0)

        self.image_progress = Gtk.ProgressBar()
        vbox.add(self.image_progress)

        vbox.show_all()

    def on_response(self, dialog, response):
        if response == Gtk.ResponseType.CANCEL or response == Gtk.ResponseType.DELETE_EVENT:
            self.cancel_cb()

if __name__ == "__main__":
    import gettext; gettext.install('postr')

    d = ProgressDialog(Gtk.main_quit)
    d.thumbnail.set_from_icon_name ("stock_internet", Gtk.IconSize.DIALOG)
    d.label.set_text(_("Uploading"))
    def pulse():
        d.image_progress.pulse()
        return True
    GObject.timeout_add(200, pulse)
    d.show()
    Gtk.main()
