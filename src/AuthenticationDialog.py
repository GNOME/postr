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

import os
from gi.repository import Gtk, GConf, GObject

def on_url_clicked(button, url):
    """Global LinkButton handler that starts the default GNOME HTTP handler, or
    firefox."""
    # Get the HTTP URL handler
    client = GConf.Client.get_default()
    browser = client.get_string("/desktop/gnome/url-handlers/http/command") or "firefox"

    # Because the world sucks and everyone hates me, just use the first word and
    # hope that is enough.  The problem is that some people have [epiphany %s]
    # which means the & needs escaping or quoting, others have [iceweasel
    # -remote "openurl(%s,newtab)"] which means the & must not be escaped or
    # quoted.  I can't see a general solution
    browser = browser.split(" ")[0]
    os.spawnlp(os.P_NOWAIT, browser, browser, url)
    # TODO: if that didn't work fallback on x-www-browser or something

class AuthenticationDialog(Gtk.Dialog):
    def __init__(self, parent, url):
        Gtk.Dialog.__init__(self,
                            title=_("Flickr Uploader"), parent=parent,
                            buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,
                                     _("Continue"), Gtk.ResponseType.ACCEPT))
        vbox = Gtk.VBox(spacing=8)

        vbox.set_border_width(8)

        label = Gtk.Label(_("Postr needs to login to Flickr to upload your photos. "
                          "Please click on the link below to login to Flickr."))
        label.set_line_wrap(True)
        vbox.add(label)

        # Gtk.LinkButton is only in 2.10, so use a normal button if it isn't
        # available.
        if hasattr(Gtk, "LinkButton"):
            Gtk.link_button_set_uri_hook(on_url_clicked)
            button = Gtk.LinkButton(url, _("Login to Flickr"))
        else:
            button = Gtk.Button(_("Login to Flickr"))
            button.connect("clicked", on_url_clicked, url)
        vbox.add(button)

        self.vbox.add(vbox)
        self.show_all()
