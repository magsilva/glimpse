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

from istanbul.main.constants import RecordingState
from istanbul.main.screencast import Screencast
from istanbul.main.tray_popup import TrayPopupMenu
from istanbul.main.screen import Screen
from istanbul.main.preferences import Preferences

import gtk
import egg.trayicon

import locale, gettext
_ = gettext.gettext

class TrayIcon:

    state = RecordingState.STOPPED
    current_screencast = None
    popup_menu = TrayPopupMenu()
    event_box = Screen().event_box

    def __init__(self):
        gtk.window_set_default_icon_name(gtk.STOCK_MEDIA_RECORD)
        self.tray_image = gtk.Image()
        self.tray_image.set_from_stock(gtk.STOCK_MEDIA_RECORD, gtk.ICON_SIZE_SMALL_TOOLBAR)
        self.event_box.add(self.tray_image)
        self.tooltips = gtk.Tooltips()
        self.tooltips.set_tip(self.event_box,
            _("Left click to start screencast.  Right click for menu."))
        self.tray_container = egg.trayicon.TrayIcon("istanbul")
        self.tray_container.add(self.event_box)
        self.event_box.connect("button-press-event", self._trayicon_clicked)
        self.tray_container.show_all()

    def _trayicon_clicked(self, widget, event):
        """
        left click triggers record/stop
        right click shows popup menu
        """
        if event.button == 1:
            if self.state == RecordingState.STOPPED:
                self.tray_image.set_from_stock(gtk.STOCK_MEDIA_STOP, 
                    gtk.ICON_SIZE_SMALL_TOOLBAR)
                self.tooltips.set_tip(self.event_box,
                    _("Left click to stop recording screencast."))
                self.state = RecordingState.RECORDING
                self.current_screencast = Screencast(self.stop_handler)
                self.current_screencast.selector = self.popup_menu.selector
                self.current_screencast.start_recording()

            elif self.state == RecordingState.RECORDING:
                self.tray_image.set_from_stock(gtk.STOCK_HARDDISK,
                    gtk.ICON_SIZE_SMALL_TOOLBAR)
                self.state = RecordingState.SAVING
                self.tooltips.set_tip(self.event_box,
                    _("In process of saving to disk."))
                self.current_screencast.stop_recording()
               
        # only show popup if in idle state                    
        elif event.button == 3 and self.state == RecordingState.STOPPED:
            self.popup_menu.show()
    
    def stop_handler(self, event):
        self.tray_image.set_from_stock(gtk.STOCK_MEDIA_RECORD, 
            gtk.ICON_SIZE_SMALL_TOOLBAR)
        self.state = RecordingState.STOPPED
        self.tooltips.set_tip(self.event_box,
            _("Left click to start screencast.  Right click for menu."))
        return False
