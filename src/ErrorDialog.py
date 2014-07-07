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

from gi.repository import Gtk

class ErrorDialog(Gtk.MessageDialog):
    def __init__(self, parent=None):
        Gtk.MessageDialog.__init__(self,
                                   flags=Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                   type=Gtk.MessageType.ERROR,
                                   buttons=Gtk.ButtonsType.OK,
                                   parent=parent,
                                   message_format=_("An error occurred"))
        self.set_destroy_with_parent(True)
        self.connect("response", lambda dialog, response: dialog.destroy())
        self.expander = None

    def set_from_failure (self, failure):
        print failure
        # TODO: format nicer
        self.format_secondary_text (str (failure.value))

    def set_from_exception (self, exception):
        print exception
        # TODO: format nicer
        self.format_secondary_text (str (exception))

    def set_from_string(self, message):
        # TODO: format nicer
        self.format_secondary_text (message)

    def add_details(self, message):
        # TODO: format nicer
        if not self.expander:
            self.expander = Gtk.Expander(_('Details'))
            self.view = Gtk.TextView();
            self.buffer = self.view.get_buffer()

            sw = Gtk.ScrolledWindow()
            sw.set_shadow_type(Gtk.Shadow.ETCHED_IN)
            sw.set_policy(Gtk.Policy.AUTOMATIC, Gtk.Policy.AUTOMATIC)

            sw.add(self.view)

            self.expander.add(sw)
            self.expander.show_all()
            self.vbox.pack_start(self.expander, True, True, 0)


        iter = self.buffer.get_end_iter()
        self.buffer.insert(iter, message+'\n')

