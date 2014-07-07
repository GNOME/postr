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

from gi.repository import Gtk
from version import __version__

class AboutDialog(Gtk.AboutDialog):
    def __init__(self, parent=None):
        Gtk.AboutDialog.__init__(self)
        self.set_transient_for(parent)
        self.set_name(_('Flickr Uploader'))
        self.set_copyright(u'Copyright \u00A9 2006-2008 Ross Burton\n'
                           u'Copyright \u00A9 2009-2012 Germán Poo-Caamaño')
        self.set_authors(('Ross Burton <ross@burtonini.com>',
                          'Germán Poo-Caamaño <gpoo@gnome.org>'))
        self.set_website('https://wiki.gnome.org/Apps/Postr')
        self.set_logo_icon_name('postr')
        self.set_version (__version__)


if __name__ == "__main__":
    import gettext; gettext.install('postr')

    AboutDialog().show()
    Gtk.main()
