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

import datetime
from gi.repository import GObject, Gtk, GdkPixbuf
from twisted.web.client import getPage
from twisted.python import log

_NO_PHOTOSET_ID = "-1"
_NO_PHOTOSET_LABEL = _("None")
_DEFAULT_NEW_PHOTOSET_LABEL = _("Create Photoset \"%s\"")
_DEFAULT_NEW_PHOTOSET_NAME = datetime.datetime.strftime(datetime.datetime.today(),
                                                        _("new photoset (%m-%d-%y)"))

# Column Indexes
(COL_SETID,
  COL_SETLABEL,
  COL_THUMBNAIL) = range(0, 3)

class SetCombo(Gtk.ComboBox):
    __gtype_name__ = 'SetCombo'

    def __init__(self):
        Gtk.ComboBox.__init__(self)
        self.flickr = None

        # Calculate the size of thumbnails based on the size of the text
        # renderer, but provide a default in case style-set isn't called.
        self.text_renderer = Gtk.CellRendererText()
        self.connect("style-set", self.style_set)
        self.thumb_size = 24

        # ID, name, thumbnail
        self.model = Gtk.ListStore (GObject.TYPE_STRING, GObject.TYPE_STRING, GdkPixbuf.Pixbuf)
        self.model.set (self.model.append(),
                        COL_SETID, _NO_PHOTOSET_ID,
                        COL_SETLABEL, _NO_PHOTOSET_LABEL)
        self._create_new_photoset_iter()

        self.set_model(self.model)
        self.set_active (-1)

        renderer = Gtk.CellRendererPixbuf()
        self.pack_start (renderer, expand=False)
        self.add_attribute(renderer, 'pixbuf', COL_THUMBNAIL)

        self.pack_start (self.text_renderer, expand=False)
        self.add_attribute(self.text_renderer, 'text', COL_SETLABEL)

    def style_set(self, widget, old_style):
        self.thumb_size = self.text_renderer.get_size(self, None)[3]

    def twisted_error(self, failure):
        from ErrorDialog import ErrorDialog
        dialog = ErrorDialog()
        dialog.set_from_failure(failure)
        dialog.show_all()

        log.err(failure, 'Exception in %s' % self.__gtype_name__)
        return failure

    def __got_set_thumb(self, page, it):
        loader = GdkPixbuf.PixbufLoader()
        loader.set_size (self.thumb_size, self.thumb_size)
        loader.write(page)
        loader.close()
        self.model.set (it, COL_THUMBNAIL, loader.get_pixbuf())

    def __got_photosets(self, rsp):
        """Callback for the photosets.getList call"""
        for photoset in rsp.findall("photosets/photoset"):
            it = self.model.append()
            self.model.set (it,
                           0, photoset.get("id"),
                           1, photoset.find("title").text)

            url = "https://static.flickr.com/%s/%s_%s%s.jpg" % (photoset.get("server"), photoset.get("primary"), photoset.get("secret"), "_s")
            deferred = getPage(url)
            deferred.addCallback(self.__got_set_thumb, it)
            deferred.addErrback(self.twisted_error)

    def update(self):
        deferred = self.flickr.photosets_getList()
        deferred.addCallback(self.__got_photosets)
        deferred.addErrback(self.twisted_error)

    def get_id_for_iter(self, it):
        if it is None: return None
        return self.model.get(it, COL_SETID)

    # This is needed for imports to behave correctly.  The
    #   index of the iterator on export might no longer be valid
    #   when the upload set is imported.
    def get_iter_for_set(self, set_id):
        iter = self.model.get_iter_first()
        while iter:
            iter_set_id = self.model.get(iter, COL_SETID)
            if iter_set_id[0] == set_id:
                return iter
            iter = self.model.iter_next(iter)
        return None

    def _get_new_photoset_iter(self):
        return self.model.get_iter(1)

    def _create_new_photoset_iter(self):
        self.model.set(self.model.insert(1))
        self.update_new_photoset("", id=_NO_PHOTOSET_ID)

    def update_new_photoset(self, new_photoset_name, id=None):
        self.new_photoset_name = new_photoset_name \
            if new_photoset_name else _DEFAULT_NEW_PHOTOSET_NAME
        new_set_label = _DEFAULT_NEW_PHOTOSET_LABEL % self.new_photoset_name
        it = self._get_new_photoset_iter()
        if id is not None:
            self.model.set_value(it, COL_SETID, id)
        self.model.set_value(it, COL_SETLABEL, new_set_label)

    def _response_to_dialog(self, entry, dialog, response):
        dialog.response(response)

    def name_new_photoset(self, window=None):
        dialog = Gtk.MessageDialog(window,
                                   Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                   Gtk.MessageType.QUESTION,
                                   Gtk.ButtonsType.OK_CANCEL,
                                   None)
        dialog.set_markup(_("Name for the new photoset:"))
        entry = Gtk.Entry()
        entry.set_text(self.new_photoset_name)
        # so that you can press 'enter' to close dialog
        entry.connect("activate", self._response_to_dialog, dialog, Gtk.ResponseType.OK)
        dialog.vbox.pack_end(entry, True, True, 0)
        dialog.show_all()

        response = dialog.run()
        text = entry.get_text()
        dialog.destroy()
        if response == Gtk.ResponseType.OK:
            self.update_new_photoset(text.strip())
        return self.new_photoset_name

    def set_recently_created_photoset(self, photoset_name, photoset_id):
        if photoset_name == self.new_photoset_name and photoset_id:
            self.update_new_photoset(photoset_name, id=photoset_id)
            self._create_new_photoset_iter()
