# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4
#
# Istanbul - A desktop recorder
# Copyright (C) 2005 Zaheer Abbas Merali (zaheerabbas at merali dot org)
# Copyright (C) 2006 John N. Laliberte (allanonjl@gentoo.org) (jlaliberte@gmail.com)
# Copyright (C) 2006 Wouter Bolsterlee (wbolster@gnome.org)
# Portions Copyright (C) 2004,2005 Fluendo, S.L. (www.fluendo.com).
# All rights reserved.

# This file may be distributed and/or modified under the terms of
# the GNU General Public License version 2 as published by
# the Free Software Foundation.
# This file is distributed without any warranty; without even the implied
# warranty of merchantability or fitness for a particular purpose.
# See "LICENSE.GPL" in the source distribution for more information.

# Headers in this file shall remain intact.

import gtk
import os
import gobject
import locale, gettext
_ = gettext.gettext

import pygst
pygst.require('0.10')
import gst
import gst.interfaces

from istanbul.main.preferences import Preferences
from istanbul.main.gst_player import GstPlayer

class VideoWidget(gtk.DrawingArea):
    def __init__(self):
        gtk.DrawingArea.__init__(self)
        self.imagesink = None
        self.unset_flags(gtk.DOUBLE_BUFFERED)

    def do_expose_event(self, event):
        if self.imagesink:
            self.imagesink.expose()
            return False
        else:
            return True

    def set_sink(self, sink):
        assert self.window.xid
        self.imagesink = sink
        self.imagesink.set_xwindow_id(self.window.xid)

class SaveWindow(gtk.Window):
    UPDATE_INTERVAL = 500

    def __init__(self, location, width, height):
        #print "SaveWindow with file: %s" % location
        gtk.Window.__init__(self)

        self.create_ui(width, height)

        self.player = GstPlayer(self.videowidget)
        self.player.set_location("file://%s" % location)
        self.location = location

        def on_eos():
            self.player.seek(0L)
            self.play_toggled()
        self.player.on_eos = lambda *x: on_eos()

        self.update_id = -1
        self.changed_id = -1
        self.seek_timeout_id = -1

        self.p_position = gst.CLOCK_TIME_NONE
        self.p_duration = gst.CLOCK_TIME_NONE

        self.connect('delete-event', lambda *x: self.on_delete_event())

        self.already_saved = False

    def create_ui(self, width, height):
        self.set_border_width(18)
        table = gtk.Table(rows=3, columns=2)
        table.set_row_spacings(18)
        table.set_col_spacings(12)
        table.show()
        self.add(table)
        self.set_title(_("Save Screencast"))

        self.videowidget = VideoWidget()
        self.videowidget.show()
        table.attach(self.videowidget,0,1,0,1)
        self.filechooser = gtk.FileChooserWidget(
            action=gtk.FILE_CHOOSER_ACTION_SAVE)
        self.filechooser.show()
        self.filechooser.connect("file-activated", lambda *args: self.save())
        self.filechooser.set_do_overwrite_confirmation(True)
        if Preferences().has_gnomevfs():
            self.filechooser.set_local_only(False)
        else:
            self.filechooser.set_local_only(True)
        # add ogg media file filter
        oggfilter = gtk.FileFilter()
        oggfilter.set_name(_("Ogg Media File (*.ogg)"))
        oggfilter.add_pattern("*.ogg")
        self.filechooser.add_filter(oggfilter)
        table.attach(self.filechooser,1,2,0,1,xoptions=0,
            yoptions=gtk.EXPAND|gtk.FILL)

        self.pause_image = gtk.image_new_from_stock(gtk.STOCK_MEDIA_PAUSE,
            gtk.ICON_SIZE_BUTTON)
        self.pause_image.show()
        self.play_image = gtk.image_new_from_stock(gtk.STOCK_MEDIA_PLAY,
            gtk.ICON_SIZE_BUTTON)
        self.play_image.show()
        self.button = button = gtk.Button()
        button.add(self.play_image)
        button.set_property('can-default', False)
        button.set_focus_on_click(False)
        button.show()
        table.attach(button, 0,1,2,3,xoptions=gtk.EXPAND|gtk.FILL,
            yoptions=0)

        button.connect('clicked', lambda *args: self.play_toggled())

        self.adjustment = gtk.Adjustment(0.0, 0.00, 100.0, 0.1, 1.0, 1.0)
        hscale = gtk.HScale(self.adjustment)
        hscale.show()
        hscale.set_digits(2)
        hscale.set_update_policy(gtk.UPDATE_CONTINUOUS)
        hscale.connect('button-press-event', self.scale_button_press_cb)
        hscale.connect('button-release-event', self.scale_button_release_cb)
        hscale.connect('format-value', self.scale_format_value_cb)
        hscale.set_value_pos(gtk.POS_RIGHT)
        hscale.set_sensitive(False)
        self.hscale = hscale
        table.attach(hscale, 0,1,1,2,xoptions=gtk.EXPAND|gtk.FILL,
            yoptions=0)
        table.set_row_spacing(0,6)
        table.set_row_spacing(1,6)
        self.videowidget.connect_after('realize',
                                       lambda *x: self.player.pause() )
        self.videowidget.set_size_request(width, height)

        # create save, edit, cancel buttons
        buttonbox = gtk.HButtonBox()
        buttonbox.set_layout(gtk.BUTTONBOX_END)
        buttonbox.show()
        self.cancel_button = gtk.Button(label=_("Close _without saving"))
        self.cancel_button.show()
        self.cancel_button.connect("clicked", lambda *args: self.on_cancel())
        buttonbox.add(self.cancel_button)
        # The edit buttom seems useless? (Wouter Bolsterlee)
        #self.edit_button = gtk.Button(stock="gtk-edit")
        #self.edit_button.set_sensitive(False)
        #self.edit_button.show()
        #buttonbox.add(self.edit_button)
        self.save_button = gtk.Button(stock="gtk-save")
        self.save_button.show()
        self.save_button.connect("clicked", lambda *args: self.save())
        self.save_button.set_property('can-default', True)
        buttonbox.add(self.save_button)

        table.attach(buttonbox, 1,2,2,3,xoptions=gtk.EXPAND|gtk.FILL, 
            yoptions=0)

        self.save_button.set_property('has-default', True)

    def play_toggled(self):
        self.button.remove(self.button.child)
        if self.player.is_playing():
            self.player.pause()
            self.button.add(self.play_image)
        else:
            self.player.play()
            if self.update_id == -1:
                self.update_id = gobject.timeout_add(self.UPDATE_INTERVAL,
                    self.update_scale_cb)
            self.button.add(self.pause_image)
            self.hscale.set_sensitive(True)

    def scale_format_value_cb(self, scale, value):
        if self.p_duration == -1:
            real = 0
        else:
            real = value * self.p_duration / 100

        seconds = real / gst.SECOND

        return "%02d:%02d" % (seconds / 60, seconds % 60)

    def scale_button_press_cb(self, widget, event):
        gst.debug("starting seek")
        
        self.button.set_sensitive(False)
        self.was_playing = self.player.is_playing()
        if self.was_playing:
            self.player.pause()

        if self.update_id != -1:
            gobject.source_remove(self.update_id)
            self.update_id = -1

        if self.changed_id == -1:
            self.changed_id = self.hscale.connect('value-changed',
                self.scale_value_changed_cb)

    def scale_value_changed_cb(self, scale):
        real = long(scale.get_value() * self.p_duration / 100)
        gst.debug("value changed, perform seek to %r" % real)
        self.player.seek(real)
        self.player.get_state(timeout=50*gst.MSECOND)

    def scale_button_release_cb(self, widget, event):
       # see seek.cstop_seek
        widget.disconnect(self.changed_id)
        self.changed_id = -1

        self.button.set_sensitive(True)
        if self.seek_timeout_id != -1:
            gobject.source_remove(self.seek_timeout_id)
            self.seek_timeout_id = -1
        else:
            gst.debug('released slider, setting back to playing')
            if self.was_playing:
                self.player.play()

        if self.update_id != -1:
            self.error('Had a previous update timeout id')
        else:
            self.update_id = gobject.timeout_add(self.UPDATE_INTERVAL,
                self.update_scale_cb)

    def update_scale_cb(self):
        self.p_position, self.p_duration = self.player.query_position()
        if self.p_position != gst.CLOCK_TIME_NONE:
            try:
                value = self.p_position * 100.0 / self.p_duration
                self.adjustment.set_value(value)
            except ZeroDivisionError:
                pass
        return True

    def save(self):
        """Save the file, then close this window"""

        if self.already_saved:
            return

        self.player.stop()

        save_succesful = False

        if Preferences().has_gnomevfs():
            import gnomevfs
            try:
                trysave = gnomevfs.xfer_uri(gnomevfs.URI("file://%s" % self.location), 
                    gnomevfs.URI(self.filechooser.get_uri()), 
                    gnomevfs.XFER_DELETE_ITEMS,
                    gnomevfs.XFER_ERROR_MODE_ABORT, 
                    gnomevfs.XFER_OVERWRITE_MODE_ABORT)
            except gnomevfs.FileExistsError:
                dialog = gtk.MessageDialog(self,
                    gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                    gtk.MESSAGE_QUESTION,
                    gtk.BUTTONS_YES_NO,
                    _("A file named \"%s\" already exists.  Do you want to replace it?") % self.filechooser.get_uri())
                dialog.format_secondary_text (
                    _("The file already exists in \"%s\".  Replacing it will overwrite its contents.") % (
                            self.filechooser.get_current_folder()))
                res = dialog.run()
                dialog.hide()
                if res == gtk.RESPONSE_YES:
                    try:
                        trysave = gnomevfs.xfer_uri(
                        gnomevfs.URI("file://%s" % self.location), 
                        gnomevfs.URI(self.filechooser.get_uri()), 
                        gnomevfs.XFER_DELETE_ITEMS,
                        gnomevfs.XFER_ERROR_MODE_ABORT, 
                        gnomevfs.XFER_OVERWRITE_MODE_REPLACE)
                    except Exception:
                        dialog = gtk.MessageDialog(self,
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                            gtk.MESSAGE_QUESTION,
                            gtk.BUTTONS_OK,
                            _("There was an unknown error writing to \"%s\".  Please try a different file or location.") % (
                            self.filechooser.get_uri()))
                        dialog.run()
                        dialog.hide()
                    else:
                        save_succesful = True
            else:
                save_succesful = True
        else:
            # we do not have Gnomevfs so let us use normal python calls to 
            # move the file
            # the file chooser uri will start with file:// so take character 8
            # onwards
            import shutil

            try:
                shutil.move(self.location, self.filechooser.get_uri()[7:])
            except Exception:
                dialog = gtk.MessageDialog(self,
                    gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                    gtk.MESSAGE_QUESTION,
                    gtk.BUTTONS_OK,
                    _("There was an unknown error writing to \"%s\".  Please try a different file or location.") % (
                    self.filechooser.get_uri()))
                dialog.run()
                dialog.hide()
            else:
                save_succesful = True

        if save_succesful:

            # Save seemed to be succesful
            self.already_saved = True
            self.save_location = self.filechooser.get_uri()
            self.player.set_location(self.save_location)
            self.save_button.set_sensitive(False)

            # Close the save dialog. This should be removed if the
            # "edit" stuff has been implemented
            self.destroy()

    def on_delete_event(self):
        if not self.already_saved:
            dialog = gtk.MessageDialog(self, 
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                gtk.MESSAGE_QUESTION,
                gtk.BUTTONS_NONE,
                _("You have not saved the screencast.  Are you really sure you want to lose it?"))
            dialog.add_buttons(_("Close _without saving"), gtk.RESPONSE_OK, gtk.STOCK_CANCEL,
                gtk.RESPONSE_CANCEL)
            dialog.set_default_response(gtk.RESPONSE_CANCEL)
            result = dialog.run()
            dialog.hide()
            if result != gtk.RESPONSE_OK:
                return True
            self.player.stop()
            os.remove(self.location)
            return False
        else:
            self.player.stop()
        return False

    def on_cancel(self):
        if not self.on_delete_event():
            self.destroy()
