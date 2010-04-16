# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4
#
# Istanbul - A desktop recorder
# Copyright (C) 2005 Zaheer Abbas Merali (zaheerabbas at merali dot org)
# Copyright (C) 2006 John N. Laliberte (allanonjl@gentoo.org) (jlaliberte@gmail.com)
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
import locale, gettext
_ = gettext.gettext

from istanbul.configure import config
from istanbul.main.constants import RecordingState
from istanbul.main.preferences import Preferences
from istanbul.main.gconf_client import GConfClient
from istanbul.main.area_select import GtkAreaSelector
from istanbul.main.window_select import WindowSelector
from istanbul.main.constants import Widgets
from istanbul.main.constants import Widget
from istanbul.main.checkradio_widget import GtkCheckRadio

DEBUG=False
class TrayPopupMenu:

    def __init__(self):
        self.tooltips = gtk.Tooltips()
        self._setup_popup_menu()
        self._setup_menu()
        self.selector = None

    def _setup_popup_menu(self):
        self.popupmenu = gtk.Menu()
        self._setup_about()
        self._setup_select_area()
        self._setup_select_window()
        self._setup_record_3d()
        self._setup_record_pointer()
        self._setup_record_sound()
        self._setup_size()
        self._setup_quit()

    def _setup_about(self):
        self.popupmenu_aboutitem = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
        self.popupmenu_aboutitem.connect('activate', self._about)
        self.popupmenu.add(self.popupmenu_aboutitem)

    def _about(self, button):
        aboutdialog = gtk.AboutDialog()
        aboutdialog.set_name(_('istanbul'))
        aboutdialog.set_version(config.version)
        aboutdialog.set_comments(_('Records a video of your desktop session'))
        aboutdialog.set_copyright(_('Copyright (c) 2005-6 Zaheer Abbas Merali, John N. Laliberte\nPortions Copyright (C) Fluendo S.L.'))
        aboutdialog.set_authors(['Zaheer Abbas Merali','John N. Laliberte'])
        aboutdialog.set_website('http://live.gnome.org/Istanbul')
        aboutdialog.set_license('GPL-2')
        aboutdialog.set_translator_credits(_('translator-credits'))
        aboutdialog.connect('response', lambda widget, response: widget.destroy())
        aboutdialog.show_all()

    def _setup_select_area(self):
        self.popupmenu_selectarea = gtk.ImageMenuItem(
            _("_Select Area to Record"))
        self.popupmenu.add(self.popupmenu_selectarea)
        self.popupmenu_selectarea.connect("activate", self._select_area_cb)
        self.tooltips.set_tip(self.popupmenu_selectarea,
            _("Use a selector to select area of screen to capture."))

    def _select_area_cb(self, menuitem):
        self.popupmenu.hide()
        self.selector = GtkAreaSelector()
        self.selector.show()

    def _setup_select_window(self):
        self.popupmenu_selectwindow = gtk.ImageMenuItem(
            _("Select _Window to Record"))
        self.popupmenu.add(self.popupmenu_selectwindow)
        self.popupmenu_selectwindow.connect("activate", self._select_window_cb)
        self.tooltips.set_tip(self.popupmenu_selectwindow,
            _("Select a window on the screen to capture"))

    def _select_window_cb(self, menuitem):
        self.popupmenu.hide()
        self.selector = WindowSelector()
        self.selector.select_window()

    def _setup_record_3d(self):
        record_3d = gtk.CheckMenuItem(_("Record _3D"))
        record_3d.set_name("record_3d")
        self.popupmenu.add(record_3d)

        new_widget = Widget(record_3d)
        new_widget.events["gui"] = new_widget.preference.generate_gui_event(record_3d, None)
        new_widget.events["gconf"] = new_widget.preference.generate_gconf_event(new_widget)
        Widgets.widgets[str(new_widget.name)] = new_widget
        self.tooltips.set_tip(record_3d,
            _("Tick this if you want to screencast a 3d application.  This will however take more CPU power."))
        
    def _setup_record_pointer(self):
        record_mousepointer = gtk.CheckMenuItem(_("Record _Mouse Pointer"))
        record_mousepointer.set_name("record_mousepointer")
        self.popupmenu.add(record_mousepointer)

        new_widget = Widget(record_mousepointer)
        new_widget.events["gui"] = new_widget.preference.generate_gui_event(record_mousepointer, None)
        new_widget.events["gconf"] = new_widget.preference.generate_gconf_event(new_widget)
        Widgets.widgets[str(new_widget.name)] = new_widget
        self.tooltips.set_tip(record_mousepointer,
            _("Tick this if you want to record the mouse pointer during the screencast."))

    def _setup_record_sound(self):
        record_sound = gtk.CheckMenuItem(_("Record _Sound"))
        record_sound.set_name("record_sound")
        self.popupmenu.add(record_sound)
        
        new_widget = Widget(record_sound)
        new_widget.events["gui"] = new_widget.preference.generate_gui_event(
            record_sound, None)
        new_widget.events["gconf"] = new_widget.preference.generate_gconf_event(
            new_widget)
        Widgets.widgets[str(new_widget.name)] = new_widget
        self.tooltips.set_tip(record_sound,
            _("Tick this if you want to record audio with the screencast.  You can choose the audio device to record from in the Multimedia Systems Selector in Preferences."))

    def _setup_size(self):
        """
        We should redo the framework so its easy to do ( ie, as above with setup_record_pointer and such. )
        """
        self.popupmenu_size_sep = gtk.SeparatorMenuItem()

        self.video_size_full = gtk.CheckMenuItem(_("_Full Size"))
        self.video_size_full.set_name("video_size_full")
        self.video_size_full.set_draw_as_radio(True)
        self.tooltips.set_tip(self.video_size_full,
            _("Select this if you do not want to scale down the size of the recording."))
        #self.video_size_half = gtk.CheckMenuItem(_("_Half width and height"))
        #self.video_size_full.set_name("video_size_half")
        #self.video_size_half.set_draw_as_radio(True)

        #video_size = GtkCheckRadio({    _("_Full Size"):"video_size_full",
        #                                _("_Half width and height"):"video_size_half"})
        #video_size.set_name("video_size")

        #new_widget = Widget(video_size)
        #new_widget.events["gui"] = new_widget.preference.generate_gui_event(video_size, None)
        #new_widget.events["gconf"] = new_widget.preference.generate_gconf_event(new_widget)
        #Widgets.widgets[str(new_widget.name)] = new_widget

        #self.popupmenu.add(video_size)

        self.video_size_full_toggle = self.video_size_full.connect(
            "toggled", self._video_size_toggled)

        self.popupmenu_size_half = gtk.CheckMenuItem(_("_Half width and height"))
        self.popupmenu_size_half.set_draw_as_radio(True)
        self.video_size_half_toggle = self.popupmenu_size_half.connect(
            "toggled", self._video_size_toggled)
        self.tooltips.set_tip(self.popupmenu_size_half,
            _("Select this to scale down the recording resolution by 1/2."))
        self.popupmenu_size_quarter = gtk.CheckMenuItem(
            _("_Quarter width and height"))
        self.popupmenu_size_quarter.set_draw_as_radio(True)
        self.video_size_quarter_toggle = self.popupmenu_size_quarter.connect(
            "toggled", self._video_size_toggled)
        self.tooltips.set_tip(self.popupmenu_size_quarter,
            _("Select this to scale down the recording resolution by 1/4."))
        self.popupmenu.add(self.popupmenu_size_sep)
        self.popupmenu.add(self.video_size_full)
        self.popupmenu.add(self.popupmenu_size_half)
        self.popupmenu.add(self.popupmenu_size_quarter)
        
        # Commenting out but want an advanced preferences
        #self.popupmenu_settingsitem = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES)
        #self.popupmenu_settingsitem.connect('activate', self._settings)
        #self.popupmenu.add(self.popupmenu_settingsitem)

    def _video_size_toggled(self, widget, data=None):
        # let's set the gconf key if we have gconf
        # or let's do things manually
        # its a radio button so we don;t want it unset

        # lets remove signal handlers
        self.video_size_full.disconnect(self.video_size_full_toggle)
        self.popupmenu_size_half.disconnect(self.video_size_half_toggle)
        self.popupmenu_size_quarter.disconnect(self.video_size_quarter_toggle)

        if widget == self.video_size_full:
            if Preferences().has_gconf():
                GConfClient('/apps/istanbul').set_entry("video_size", "full", "string")
            self.video_size_full.set_active(True)
            self.popupmenu_size_half.set_active(False)
            self.popupmenu_size_quarter.set_active(False)
        elif widget == self.popupmenu_size_half:
            if Preferences().has_gconf():
                GConfClient('/apps/istanbul').set_entry("video_size", "half", "string")
            self.video_size_full.set_active(False)
            self.popupmenu_size_half.set_active(True)
            self.popupmenu_size_quarter.set_active(False)
        elif widget == self.popupmenu_size_quarter:
            if Preferences().has_gconf():
                GConfClient('/apps/istanbul').set_entry("video_size", "quarter", "string")
            self.video_size_full.set_active(False)
            self.popupmenu_size_half.set_active(False)
            self.popupmenu_size_quarter.set_active(True)

        # readd signal handlers
        self.video_size_full_toggle = self.video_size_full.connect(
            "toggled", self._video_size_toggled)
        self.video_size_half_toggle = self.popupmenu_size_half.connect(
            "toggled", self._video_size_toggled)
        self.video_size_quarter_toggle = self.popupmenu_size_quarter.connect(
            "toggled", self._video_size_toggled)

    def _setup_quit(self):
        self.popupmenu_quititem = gtk.ImageMenuItem(gtk.STOCK_QUIT)
        self.popupmenu_quititem.connect('activate', self._quit)
        self.popupmenu.add(self.popupmenu_quititem)

    def _quit(self, button):
        # get state of current screencast and quit if its still recording
        #if self.state == RecordingState.RECORDING:
        gtk.main_quit()

    def show(self):
        self.popupmenu.show_all()
        self.popupmenu.popup(None, None, None, 3, gtk.get_current_event_time())

    def _setup_menu(self):
        """
        Select any GUI elements we need to based on the settings.
        """

        video_size = Preferences().Settings["video_size"]
        popupmenu = {"full":self.video_size_full, "half":self.popupmenu_size_half, "quarter":self.popupmenu_size_quarter}
        popupmenu[video_size].set_active(True)

        self.record_3d = Preferences().Settings["record_3d"]
        if self.record_3d:
            Widgets().widgets["record_3d"].widget.set_active(True)

        self.record_mousepointer = Preferences().Settings["record_mousepointer"]
        if self.record_mousepointer:
            Widgets().widgets["record_mousepointer"].widget.set_active(True)

        self.record_sound = Preferences().Settings["record_sound"]
        if self.record_sound:
            Widgets().widgets["record_sound"].widget.set_active(True)
        #if Preferences().has_gconf():
        #    client = GConfClient("/apps/istanbul")
        #    client.client.notify_add("/apps/istanbul/video_size", self._video_size_toggled, "gconf")
        #    client.client.notify_add("/apps/istanbul/record_3d", self._3drecord_toggled, "gconf")
        #    client.client.notify_add("/apps/istanbul/record_mousepointer", self._record_pointer_toggled, "gconf")
        #    client.client.notify_add("/apps/istanbul/video_framerate", self._setup_menu)


# will be migrated with settings
#    def _video_size_changed(self, client, *args, **kwargs):
#        self.video_size = self.gconf_client.get_entry("/video_size", "string")
#        print "video size changed to: %s" % self.video_size
#        # lets remove signal handlers
#        self.popupmenu_size_full.disconnect(self.video_size_full_toggle)
#        self.popupmenu_size_half.disconnect(self.video_size_half_toggle)
#        self.popupmenu_size_quarter.disconnect(self.video_size_quarter_toggle)
#        if self.video_size:
#            if self.video_size == "full":
#                self.popupmenu_size_full.set_active(True)
#                self.popupmenu_size_half.set_active(False)
#                self.popupmenu_size_quarter.set_active(False)
#
#            elif self.video_size == "half":
#                self.popupmenu_size_half.set_active(True)
#                self.popupmenu_size_full.set_active(False)
#                self.popupmenu_size_quarter.set_active(False)
#
#            elif self.video_size == "quarter":
#                self.popupmenu_size_quarter.set_active(True)
#                self.popupmenu_size_full.set_active(False)
#                self.popupmenu_size_half.set_active(False)
#
#        else:
#            self.popupmenu_size_full.set_active(True)
#            self.popupmenu_size_full.set_active(False)
#            self.popupmenu_size_half.set_active(False)
#            self.video_size = "full"
#
#        # readd signal handlers
#        self.video_size_full_toggle = self.popupmenu_size_full.connect(
#            "toggled", self._video_size_toggled)
#        self.video_size_half_toggle = self.popupmenu_size_half.connect(
#            "toggled", self._video_size_toggled)
#        self.video_size_quarter_toggle = self.popupmenu_size_quarter.connect(
#            "toggled", self._video_size_toggled)
#
#    def _video_framerate_changed(self, client, *args, **kwargs):
#        self.video_framerate = self.gconf_client.get_entry(
#            "/video_framerate", "integer")
#        
#        if self.video_framerate <= 0 and self.video_framerate > 40:
#            self.video_framerate = 10

