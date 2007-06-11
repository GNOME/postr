# Postr, a Flickr Uploader
#
# Copyright (C) 2006 Ross Burton <ross@burtonini.com>
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

import gettext, logging, os, urllib
from urlparse import urlparse
from os.path import basename

import pygtk; pygtk.require ("2.0")
import gobject, gtk, gtk.glade

from AboutDialog import AboutDialog
from AuthenticationDialog import AuthenticationDialog
import ErrorDialog, ImageStore, ImageList

from flickrest import Flickr
from twisted.web.client import getPage
import EXIF
from iptcinfo import IPTCInfo
from util import *


try:
    import gtkunique
    UniqueApp = gtkunique.UniqueApp
except ImportError:
    class UniqueApp:
        """A dummy UniqueApp for when gtkunique isn't installed."""
        def __init__(self, name):
            pass
        def add_window(self, window):
            pass
        def is_running(self):
            return False

logging.basicConfig(level=logging.DEBUG)

# Exif information about image orientation
(ROTATED_0,
 ROTATED_180,
 ROTATED_90_CW,
 ROTATED_90_CCW
 ) = (1, 3, 6, 8)


class Postr (UniqueApp):
    def __init__(self):
        UniqueApp.__init__(self, 'com.burtonini.Postr')
        try:
            self.connect("message", self.on_message)
        except AttributeError:
            pass
        
        self.flickr = Flickr(api_key="c53cebd15ed936073134cec858036f1d",
                             secret="7db1b8ef68979779",
                             perms="write")

        gtk.window_set_default_icon_name("postr")
        gtk.glade.set_custom_handler(self.get_custom_handler)
        glade = gtk.glade.XML(os.path.join (os.path.dirname(__file__), "postr.glade"))
        glade.signal_autoconnect(self)

        get_glade_widgets (glade, self,
                           ("window",
                            "upload_menu",
                            "statusbar",
                            "thumbnail_image",
                            "title_entry",
                            "desc_entry",
                            "tags_entry",
                            "set_combo",
                            "thumbview",
                            "progress_dialog",
                            "progressbar",
                            "progress_filename",
                            "progress_thumbnail")
                           )
        
        # Just for you, Daniel.
        try:
            if os.getlogin() == "daniels":
                self.window.set_title("Respecognise")
        except Exception:
            pass
        
        self.model = ImageStore.ImageStore ()
        self.thumbview.set_model(self.model)
        self.thumbview.connect("drag_data_received", self.on_drag_data_received)

        selection = self.thumbview.get_selection()
        selection.connect("changed", self.on_selection_changed)

        self.current_it = None
        
        # last opened folder
        self.last_folder = None

        self.change_signals = []
        self.change_signals.append((self.title_entry, self.title_entry.connect('changed', self.on_field_changed, ImageStore.COL_TITLE)))
        self.change_signals.append((self.desc_entry, self.desc_entry.connect('changed', self.on_field_changed, ImageStore.COL_DESCRIPTION)))
        self.change_signals.append((self.tags_entry, self.tags_entry.connect('changed', self.on_field_changed, ImageStore.COL_TAGS)))
        self.thumbnail_image.connect('size-allocate', self.update_thumbnail)
        self.old_thumb_allocation = None
    
        # The set selector combo
        self.sets = gtk.ListStore (gobject.TYPE_STRING, # ID
                                   gobject.TYPE_STRING, # Name
                                   gtk.gdk.Pixbuf) # Thumbnail
        self.sets.set (self.sets.append(), 0, None, 1, "None")
        self.set_combo.set_model (self.sets)
        self.set_combo.set_active (-1)
        
        renderer = gtk.CellRendererPixbuf()
        self.set_combo.pack_start (renderer, expand=False)
        self.set_combo.set_attributes(renderer, pixbuf=2)
        renderer = gtk.CellRendererText()
        self.set_combo.pack_start (renderer, expand=False)
        self.set_combo.set_attributes(renderer, text=1)
        
        # The upload progress dialog
        self.uploading = False
        self.progress_dialog.set_transient_for(self.window)
        # Disable the Upload menu until the user has authenticated
        self.upload_menu.set_sensitive(False)
        
        # Connect to flickr, go go go
        self.token = self.flickr.authenticate_1().addCallbacks(self.auth_open_url, ErrorDialog.twisted_error)
    
    def get_custom_handler(self, glade, function_name, widget_name, str1, str2, int1, int2):
        """libglade callback to create custom widgets."""
        handler = getattr(self, function_name)
        return handler(str1, str2, int1, int2)
    
    def image_list_new (self, *args):
        """Custom widget creation function to make the image list."""
        view = ImageList.ImageList ()
        view.show()
        return view
    
    def on_message(self, app, command, command_data, startup_id, screen, workspace):
        """Callback from UniqueApp, when a message arrives."""
        if command == gtkunique.OPEN:
            self.add_image_filename(command_data)
            return gtkunique.RESPONSE_OK
        else:
            return gtkunique.RESPONSE_ABORT

    def auth_open_url(self, state):
        """Callback from midway through Flickr authentication.  At this point we
        either have cached tokens so can carry on, or need to open a web browser
        to authenticate the user."""
        if state is None:
            self.connected(True)
        else:
            dialog = AuthenticationDialog(self.window, state['url'])
            if dialog.run() == gtk.RESPONSE_ACCEPT:
                self.flickr.authenticate_2(state).addCallbacks(self.connected, ErrorDialog.twisted_error)
            dialog.destroy()
    
    def connected(self, connected):
        """Callback when the Flickr authentication completes."""
        if connected:
            self.upload_menu.set_sensitive(True)
            self.flickr.people_getUploadStatus().addCallbacks(self.got_quota, ErrorDialog.twisted_error)
            self.flickr.photosets_getList().addCallbacks(self.got_photosets, ErrorDialog.twisted_error)

    def got_quota(self, rsp):
        """Callback for the getUploadStatus call, which updates the remaining
        quota in the status bar."""
        bandwidth = rsp.find("user/bandwidth").get("remainingbytes")
        context = self.statusbar.get_context_id("quota")
        self.statusbar.pop(context)
        self.statusbar.push(context, _("You have %s remaining this month") %
                            greek(int(bandwidth)))

    def got_set_thumb(self, page, it):
        loader = gtk.gdk.PixbufLoader()
        loader.set_size (32, 32)
        loader.write(page)
        loader.close()
        self.sets.set (it, 2, loader.get_pixbuf())
    
    def got_photosets(self, rsp):
        """Callback for the photosets.getList call"""
        for photoset in rsp.findall("photosets/photoset"):
            it = self.sets.append()
            self.sets.set (it,
                           0, photoset.get("id"),
                           1, photoset.find("title").text)

            url = "http://static.flickr.com/%s/%s_%s%s.jpg" % (photoset.get("server"), photoset.get("primary"), photoset.get("secret"), "_s")
            getPage (url).addCallback (self.got_set_thumb, it)
    
    def on_field_changed(self, entry, column):
        """Callback when the entry fields are changed."""
        selection = self.thumbview.get_selection()
        (model, items) = selection.get_selected_rows()
        for path in items:
            it = self.model.get_iter(path)
            self.model.set_value (it, column, entry.get_text())
            (title, desc, tags) = self.model.get(it,
                                                 ImageStore.COL_TITLE,
                                                 ImageStore.COL_DESCRIPTION,
                                                 ImageStore.COL_TAGS)
            self.model.set_value (it, ImageStore.COL_INFO, self.get_image_info(title, desc, tags))

    def on_set_combo_changed(self, combo):
        """Callback when the set combo is changed."""
        set_it = self.set_combo.get_active_iter()
        selection = self.thumbview.get_selection()
        (model, items) = selection.get_selected_rows()
        for path in items:
            it = self.model.get_iter(path)
            self.model.set_value (it, ImageStore.COL_SET, set_it)
    
    def on_add_photos_activate(self, menuitem):
        """Callback from the File->Add Photos menu item."""
        dialog = gtk.FileChooserDialog(title=_("Add Photos"), parent=self.window,
                                       action=gtk.FILE_CHOOSER_ACTION_OPEN,
                                       buttons=(gtk.STOCK_CANCEL,
                                                gtk.RESPONSE_CANCEL,
                                                gtk.STOCK_OPEN,
                                                gtk.RESPONSE_OK))
        dialog.set_select_multiple(True)
        if self.last_folder:
            dialog.set_current_folder(self.last_folder)

        # Add filters for all reasonable image types
        filters = gtk.FileFilter()
        filters.set_name(_("Images"))
        filters.add_mime_type("image/png")
        filters.add_mime_type("image/jpeg")
        filters.add_mime_type("image/gif")
        dialog.add_filter(filters)
        filters = gtk.FileFilter()
        filters.set_name(_("All Files"))
        filters.add_pattern("*")
        dialog.add_filter(filters)

        # Add a preview widget
        preview = gtk.Image()
        dialog.set_preview_widget(preview)
        def update_preview_cb(file_chooser, preview):
            filename = file_chooser.get_preview_filename()
            try:
                pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(filename, 128, 128)
                preview.set_from_pixbuf(pixbuf)
                have_preview = True
            except:
                have_preview = False
            file_chooser.set_preview_widget_active(have_preview)
        dialog.connect("update-preview", update_preview_cb, preview)
        
        if dialog.run() == gtk.RESPONSE_OK:
            dialog.hide()
            for f in dialog.get_filenames():
                self.add_image_filename(f)
            
            self.last_folder = dialog.get_current_folder()

        dialog.destroy()
            
    def on_quit_activate(self, widget, *args):
        """Callback from File->Quit."""
        if self.uploading:
            dialog = gtk.MessageDialog(type=gtk.MESSAGE_WARNING, parent=self.window)
            dialog.add_buttons(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                               gtk.STOCK_QUIT, gtk.RESPONSE_OK)
            dialog.set_markup(_('<b>Currently Uploading</b>'))
            dialog.format_secondary_text(_('Photos are still being uploaded. '
                                         'Are you sure you want to quit?'))
            response = dialog.run()
            dialog.destroy()
            if response == gtk.RESPONSE_CANCEL:
                return True
        
        import twisted.internet.reactor
        twisted.internet.reactor.stop()
    
    def on_delete_activate(self, menuitem):
        """Callback from Edit->Delete."""
        selection = self.thumbview.get_selection()
        (model, items) = selection.get_selected_rows()
        for path in items:
            self.model.remove(self.model.get_iter(path))
    
    def on_select_all_activate(self, menuitem):
        """Callback from Edit->Select All."""
        selection = self.thumbview.get_selection()
        selection.select_all()

    def on_deselect_all_activate(self, menuitem):
        """Callback from Edit->Deselect All."""
        selection = self.thumbview.get_selection()
        selection.unselect_all()

    def on_invert_selection_activate(self, menuitem):
        """Callback from Edit->Invert Selection."""
        selection = self.thumbview.get_selection()
        def inverter(model, path, iter, selection):
            (model, selected) = selection.get_selected_rows()
            if path in selected:
                selection.unselect_iter(iter)
            else:
                selection.select_iter(iter)
        self.model.foreach(inverter, selection)

    def on_upload_activate(self, menuitem):
        """Callback from File->Upload."""
        if self.uploading:
            print "Upload should be disabled, currently uploading"
            return
        
        it = self.model.get_iter_first()
        if it is None:
            print "Upload should be disabled, no photos"
            return

        menuitem.set_sensitive(False)
        self.uploading = True
        self.thumbview.set_sensitive(False)
        self.progress_dialog.show()

        self.upload_count = self.model.iter_n_children (None)
        self.upload_index = 0
        self.upload()
        
    def on_about_activate(self, menuitem):
        """Callback from Help->About."""
        dialog = AboutDialog(self.window)
        dialog.run()
        dialog.destroy()

    def update_thumbnail(self, widget, allocation = None):
        """Update the preview, as the selected image was changed."""
        if self.current_it:
            if not allocation:
                allocation = widget.get_allocation()
                force = True
            else:
                force = False

            # hrngh.  seemingly a size-allocate call (with identical params,
            # mind) gets called every time we call set_from_pixbuf.  even if
            # we connect it to the window.  so very braindead.
            if not force and self.old_thumb_allocation and \
               self.old_thumb_allocation.width == allocation.width and \
               self.old_thumb_allocation.height == allocation.height:
                return;

            self.old_thumb_allocation = allocation

            (image, simage, filename) = self.model.get(self.current_it,
                                                       ImageStore.COL_IMAGE,
                                                       ImageStore.COL_PREVIEW,
                                                       ImageStore.COL_FILENAME)

            tw = allocation.width
            th = allocation.height
            # Clamp the size to 512
            if tw > 512: tw = 512
            if th > 512: th = 512
            (tw, th) = self.get_thumb_size(simage.get_width(),
                                           simage.get_height(),
                                           tw, th)

            thumb = simage.scale_simple(tw, th, gtk.gdk.INTERP_BILINEAR)
            widget.set_from_pixbuf(thumb)

    def on_selection_changed(self, selection):
        """Callback when the selection was changed, to update the entries and
        preview."""
        [obj.handler_block(i) for obj,i in self.change_signals]
        
        def enable_field(field, text):
            field.set_sensitive(True)
            field.set_text(text)
        def disable_field(field):
            field.set_sensitive(False)
            field.set_text("")

        (model, items) = selection.get_selected_rows()
        
        if items:
            # TODO: do something clever with multiple selections
            self.current_it = self.model.get_iter(items[0])
            (title, desc, tags, set_it) = self.model.get(self.current_it,
                                                      ImageStore.COL_TITLE,
                                                      ImageStore.COL_DESCRIPTION,
                                                      ImageStore.COL_TAGS,
                                                      ImageStore.COL_SET)

            enable_field(self.title_entry, title)
            enable_field(self.desc_entry, desc)
            enable_field(self.tags_entry, tags)
            self.set_combo.set_sensitive(True)
            if (set_it):
                self.set_combo.set_active_iter(set_it)
            else:
                self.set_combo.set_active(0)
            self.update_thumbnail(self.thumbnail_image)
        else:
            self.current_it = None
            disable_field(self.title_entry)
            disable_field(self.desc_entry)
            disable_field(self.tags_entry)
            self.set_combo.set_sensitive(False)
            self.set_combo.set_active(-1)

            self.thumbnail_image.set_from_pixbuf(None)

        [obj.handler_unblock(i) for obj,i in self.change_signals]

    @staticmethod
    def get_thumb_size(srcw, srch, dstw, dsth):
        """Scale scrw x srch to an dimensions with the same ratio that fits as
        closely as possible to dstw x dsth."""
        ratio = srcw/float(srch)
        if srcw > srch:
            return (dstw, int(dstw/ratio))
        else:
            return (int(dsth*ratio), dsth)

    def get_image_info(self, title, description, tags):
        if title:
            info_title = title
        else:
            info_title = _("No title")

        if description:
            info_desc = description
        else:
            info_desc = _("No description")

        s = "<b><big>%s</big></b>\n%s\n" % (info_title, info_desc)
        if tags:
            colour = self.window.style.text[gtk.STATE_INSENSITIVE].pixel
            s = s + "<span color='#%X'>%s</span>" % (colour, tags)
        return s
    
    def add_image_filename(self, filename):
        """Add a file to the image list.  Called by the File->Add Photo and drag
        and drop callbacks."""
        # TODO: MIME type check

        # TODO: we open the file three times now, which is madness, especially
        # if gnome-vfs is used to read remote files.  Need to find/write EXIF
        # and IPTC parsers that are incremental.
        
        # First we load the image scaled to 512x512 for the preview.
        preview = gtk.gdk.pixbuf_new_from_file_at_size(filename, 512, 512)
        
        # On a file that doesn't contain EXIF, like a PNG, this just returns an
        # empty set.
        try:
            exif = EXIF.process_file(open(filename, 'rb'))
        except:
            exif = {}
        try:
            iptc = IPTCInfo(open(filename, 'rb')).data
        except:
            iptc = {}
        
        # Rotate the preview if required.  We don't need to manipulate the
        # original data as Flickr will do that for us.
        if "Image Orientation" in exif:
            rotation = exif["Image Orientation"].values[0]
            if rotation == ROTATED_180:
                preview = preview.rotate_simple(gtk.gdk.PIXBUF_ROTATE_UPSIDEDOWN)
            elif rotation == ROTATED_90_CW:
                preview = preview.rotate_simple(gtk.gdk.PIXBUF_ROTATE_CLOCKWISE)
            elif rotation == ROTATED_90_CCW:
                preview = preview.rotate_simple(gtk.gdk.PIXBUF_ROTATE_COUNTERCLOCKWISE)
        
        # Now scale the preview to a thumbnail
        sizes = self.get_thumb_size(preview.get_width(), preview.get_height(), 64, 64)
        thumb = preview.scale_simple(sizes[0], sizes[1], gtk.gdk.INTERP_BILINEAR)

        # Slurp data from the EXIF and IPTC tags
        title_tags = (
            (iptc, "headline"),
            )
        desc_tags = (
            (exif, "Image ImageDescription"),
            (exif, "UserComment"),
            (iptc, "caption/abstract"),
            )
        tag_tags = (
            (iptc, "keywords"),
            )
        def slurp(tags, default=""):
            for (data, tag) in tags:
                if data.has_key(tag):
                    value = data[tag]
                    if isinstance (value, list):
                        return ' '.join(map (lambda s: '"' + s + '"', value))
                    return value
            return default
        
        title = slurp(title_tags, os.path.splitext(os.path.basename(filename))[0])
        desc = slurp(desc_tags)
        tags = slurp(tag_tags)
        
        self.model.set(self.model.append(),
                       ImageStore.COL_FILENAME, filename,
                       ImageStore.COL_IMAGE, None,
                       ImageStore.COL_PREVIEW, preview,
                       ImageStore.COL_THUMBNAIL, thumb,
                       ImageStore.COL_TITLE, title,
                       ImageStore.COL_DESCRIPTION, desc,
                       ImageStore.COL_TAGS, tags,
                       ImageStore.COL_INFO, self.get_image_info(title, desc, tags))
    
    def on_drag_data_received(self, widget, context, x, y, selection, targetType, timestamp):
        """Drag and drop callback when data is received."""
        if targetType == ImageList.DRAG_IMAGE:
            pixbuf = selection.get_pixbuf()

            # TODO: don't scale up if the image is smaller than 512/512
            
            # Scale the pixbuf to a preview
            sizes = self.get_thumb_size (pixbuf.get_width(), pixbuf.get_height(), 512, 512)
            preview = pixbuf.scale_simple(sizes[0], sizes[1], gtk.gdk.INTERP_BILINEAR)
            # Now scale to a thumbnail
            sizes = self.get_thumb_size (pixbuf.get_width(), pixbuf.get_height(), 64, 64)
            thumb = pixbuf.scale_simple(sizes[0], sizes[1], gtk.gdk.INTERP_BILINEAR)
            
            self.model.set(self.model.append(),
                           ImageStore.COL_IMAGE, pixbuf,
                           ImageStore.COL_FILENAME, None,
                           ImageStore.COL_PREVIEW, preview,
                           ImageStore.COL_THUMBNAIL, thumb,
                           ImageStore.COL_TITLE, "",
                           ImageStore.COL_DESCRIPTION, "",
                           ImageStore.COL_TAGS, "",
                           ImageStore.COL_INFO, self.get_image_info(None, None, None))
        
        elif targetType == ImageList.DRAG_URI:
            for uri in selection.get_uris():
                # TODO: use gnome-vfs to handle remote files
                filename = urllib.unquote(urlparse(uri)[2])
                if os.path.isfile(filename):
                    self.add_image_filename(filename)
                elif os.path.isdir(filename):
                    for root, dirs, files in os.walk(filename):
                        for f in files:
                            # TODO: handle symlinks to directories as they are
                            # in files
                            self.add_image_filename (os.path.join(root, f))
                else:
                    print "Unhandled file %s" % filename
                    
        else:
            print "Unhandled target type %d" % targetType
        
        context.finish(True, True, timestamp)

    def update_progress(self, title, filename, thumb):
        """Update the progress bar whilst uploading."""
        label = '<b>%s</b>\n<i>%s</i>' % (title, basename(filename))
        self.progress_filename.set_label(label)

        try:
            self.progress_thumbnail.set_from_pixbuf(thumb)
            self.progress_thumbnail.show()
        except:
            self.progress_thumbnail.set_from_pixbuf(None)
            self.progress_thumbnail.hide()

        self.progressbar.set_fraction(float(self.upload_index) / float(self.upload_count))
        # Use named args for i18n
        progress_label = _('Uploading %(index)d of %(count)d') % {
            "index": self.upload_index+1,
            "count": self.upload_count
            }
        self.progressbar.set_text(progress_label)

    def add_to_set(self, rsp, set):
        """Callback from the upload method to add the picture to a set."""
        if set:
            self.flickr.photosets_addPhoto(photoset_id=set,
                                           photo_id=rsp.find("photoid").text)
            return rsp
    
    def upload(self, response=None):
        """Upload worker function, called by the File->Upload callback.  As this
        calls itself in the deferred callback, it takes a response argument."""
        if self.upload_index >= self.upload_count:
            self.upload_menu.set_sensitive(True)
            self.uploading = False
            self.progress_dialog.hide()
            self.model.clear()
            self.thumbview.set_sensitive(True)
            self.flickr.people_getUploadStatus().addCallbacks(self.got_quota, ErrorDialog.twisted_error)
            return

        it = self.model.get_iter_from_string(str(self.upload_index))
        (filename, thumb, pixbuf, title, desc, tags, set_it) = self.model.get(it,
                                                                              ImageStore.COL_FILENAME,
                                                                              ImageStore.COL_THUMBNAIL,
                                                                              ImageStore.COL_IMAGE,
                                                                              ImageStore.COL_TITLE,
                                                                              ImageStore.COL_DESCRIPTION,
                                                                              ImageStore.COL_TAGS,
                                                                              ImageStore.COL_SET)
        if set_it:
            (set_id,) = self.sets.get (set_it, 0)
        else:
            set_id = 0
        
        self.update_progress(filename, title, thumb)
        self.upload_index += 1

        if filename:
            d = self.flickr.upload(filename=filename,
                               title=title, desc=desc,
                               tags=tags)
            d.addCallback(self.add_to_set, set_id)
            d.addCallbacks(self.upload, ErrorDialog.twisted_error)
        elif pixbuf:
            # This isn't very nice, but might be the best way
            data = []
            pixbuf.save_to_callback(lambda d: data.append(d), "png", {})
            d = self.flickr.upload(imageData=''.join(data),
                                title=title, desc=desc,
                                tags=tags)
            d.addCallback(self.add_to_set, set_id)
            d.addCallbacks(self.upload, ErrorDialog.twisted_error)
        else:
            print "No filename or pixbuf stored"
