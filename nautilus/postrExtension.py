# Postr's Nautilus Extension, an extension to upload to Flickr using Postr
#
# Copyright (C) 2007 German Poo-Caaman~o <gpoo@gnome.org>
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

import gettext
gettext.install('postr')

from gi.repository import Nautilus, GObject
import os, os.path

PROGRAM_NAME = 'postr'

class PostrExtension(GObject.GObject, Nautilus.MenuProvider):
    def __init__(self):
        # The constructor must be exists, even if there is nothing
        # to initialize (See Bug #374958)
        #self.program = None
        pass

    def locate_program(self, program_name):
        path_list = os.environ['PATH']
        for d in path_list.split(os.path.pathsep):
            try:
                if program_name in os.listdir(d):
                    return os.path.sep.join([d, program_name])
            except OSError:
                # Normally is a bad idea use 'pass' in a exception,
                # but in this case we don't care if the directory
                # in path exists or not.
                pass

        return None

    def upload_files(self, menu, files):
        # This is the method invoked when our extension is activated
        # Do whatever you want to do with the files selected
        if len(files) == 0:
            return

        names = [ file.get_uri() for file in files ]

        argv = [ PROGRAM_NAME ] + names

        # TODO: use startup notification
        GObject.spawn_async(argv, flags=GObject.SPAWN_SEARCH_PATH)

    def get_file_items(self, window, files):
        # Show the menu iif:
        # - There is at least on file selected
        # - All the selected files are images
        # - All selected images are locals (currently Postr doesn't have
        #   support for gnome-vfs
        # - Postr is installed (is in PATH)
        if len(files) == 0:
            return

        for fd in files:
            if fd.is_directory() or fd.get_uri_scheme() != 'file':
                return
            if not fd.is_mime_type("image/*"):
                return

        #self.program = self.locate_program(PROGRAM_NAME)
        #if not self.program:
        #    return

        item = Nautilus.MenuItem(name='PostrExtension::upload_files',
                                 label=_('Upload to Flickr...'),
                                 tip=_('Upload the selected files into Flickr'),
                                 icon="postr")
        item.connect('activate', self.upload_files, files)

        return item,

    def get_background_items(self, window, files):
        # If nothing is selected, Nautils still can show a contextual
        # menu item.
        # This method must exist even if we have nothing to offer here.
        return
