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

import tempfile

# import 0.10 as required
import pygst
pygst.require('0.10')

import gst
import gtk

from istanbul.main.screen import Screen
from istanbul.main.preferences import Preferences
from istanbul.main.save_window import SaveWindow
import locale, gettext
_ = gettext.gettext

class Screencast:

    def __init__(self, finished_callback):
        self._pipeline = None

        # what is this selector bizness? look in tray_popup
        self.selector = None
        self.finished_callback = finished_callback

    def start_recording(self, filename = None, settings = None):
        """
        mainpipeline is the core pipeline string
        save_pipeline is for saving to disk
        icecast_pipeline is for sending to an icecast server
        """
        screen = Screen().current
        width = screen.get_width()
        height = screen.get_height()
        box_left = 0
        box_right = 0
        box_top = 0
        box_bottom = 0
        display_name = screen.get_display().get_name()
        screen_number = screen.get_number()
        if not settings:
            settings = Preferences().Settings
        self.video_framerate = settings["video_framerate"]

        if self.selector:
            area_x1, area_y1, area_x2, area_y2 = self.selector.get_area()
            if area_x2 < area_x1:
                area_x1, area_x2 = area_x2, area_x1
            if area_y2 < area_y1:
                area_y1, area_y2 = area_y2, area_y1
            width = area_x2 - area_x1 - 1
            height = area_y2 - area_y1 - 1
        scaling_needed = False
        if settings["video_size"] == "half":
            width = width / 2
            height = height / 2
            scaling_needed = True
        elif settings["video_size"] == "quarter":
            width = width / 4
            height = height / 4
            scaling_needed = True

        if width % 8 > 0:
            whatsleft = 8 - width % 8
            box_left = int(whatsleft / 2)
            box_right = whatsleft - box_left
            print "whatsleft %d boxing left wth %d and right with %d" % (whatsleft, box_left,
                box_right)
            box_left = -box_left
            box_right = -box_right
        if height % 8 > 0:
            whatsleft = 8 - height % 8
            box_top = int(whatsleft / 2)
            box_bottom = whatsleft - box_top
            print "whatsleft %d boxing top wth %d and bottom with %d" % (whatsleft, box_top,
                box_bottom)
            box_top = -box_top
            box_bottom = -box_bottom

        videoscale_method = 1

        if gst.gst_version >= (0,9):
            framerate = '%d/1' % (int(self.video_framerate))
        else:
            framerate = '%d' % (int(self.video_framerate))
            videoscale_method=2

        #source = 'ximagesrc'
        vsource = 'istximagesrc name=videosource display-name=%s screen-num=%d'\
            % (display_name, screen_number)
        if self.selector:
            vsource = '%s startx=%d starty=%d endx=%d endy=%d '\
                % (vsource,
                area_x1, area_y1, area_x2-1,
                area_y2-1)

        if settings["record_3d"]:
            vsource = "%s use-damage=false" % vsource
        if not settings["record_mousepointer"]:
            vsource = "%s show-pointer=false" % vsource

        vcappipeline = '%s ! video/x-raw-rgb,framerate=%s ! videorate ! '\
            'ffmpegcolorspace'  % (vsource,
                framerate)
        if scaling_needed:
            vcappipeline += " ! videoscale method=%d" % (videoscale_method)
        acappipeline = ''
        asource = ''
        if settings["record_sound"]:
            if Preferences().has_gconf():
                asource = 'gconfaudiosrc name=audiosource'
            else:
                asource = 'alsasrc name=audiosource'
            acappipeline = '%s ! audioconvert ! vorbisenc' % asource

        vbox_pipeline = ""
        if box_left + box_right + box_bottom + box_top != 0:
            vbox_pipeline = \
                " ! videobox left=%d right=%d top=%d bottom=%d " % (
                box_left, box_right, box_top, box_bottom)
        vencode_pipeline = 'video/x-raw-yuv,width=%d,height=%d,framerate=%s %s'\
            '! theoraenc quality=63 sharpness=2 ' % (width, height, framerate,
            vbox_pipeline)

        if settings["record_in_images"]:
            vencode_pipeline = 'pngenc snapshot=false'
            mux_pipeline = 'multifilesink location="/tmp/blah-%05d"'
        else:
            if filename:
                self.temp_file = (open(filename, 'w'), filename)
            else:
                self.temp_file = tempfile.mkstemp()

            mux_pipeline = 'oggmux name=mux ! filesink location=%s' % (
                self.temp_file[1])
        if settings["record_sound"]:
            final_pipeline = '%s %s ! %s ! queue ! mux. %s ! queue ! mux.' % (
                mux_pipeline, vcappipeline, vencode_pipeline, acappipeline)
        else:
            final_pipeline = '%s ! %s ! %s' % (vcappipeline,
                vencode_pipeline, mux_pipeline)
        print("DEBUG: final pipeline: %s" % final_pipeline)
        self._pipeline = gst.parse_launch(final_pipeline)
        self._vsource = self._pipeline.get_by_name("videosource")
        if asource != '':
            self._asource = self._pipeline.get_by_name("audiosource")
        else:
            self._asource = None
        self._bus = self._pipeline.get_bus()
        self._bus.add_signal_watch()
        self._bus.connect("message", self.bus_message_cb)
        self._pipeline.set_state(gst.STATE_PLAYING)

    def bus_message_cb(self, bus, message):
        if message.type == gst.MESSAGE_ERROR:
            gerror, debug = message.parse_error()
            m = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_ERROR,
                gtk.BUTTONS_CLOSE, "Error recording")
            m.format_secondary_text(_('There was an error recording: %s\n\nDebug Information:\n%s') % (gerror, debug))
            m.run()
            m.destroy()
            self.finished_callback(message)
        # FIXME: should be fixed in oggmux in gstreamer not worked around
        elif message.type == gst.MESSAGE_EOS or \
             message.type == gst.MESSAGE_CLOCK_LOST:
            self._pipeline.set_state(gst.STATE_NULL)
            self.on_eos()

    def stop_recording(self):
        # Gst Docs rock!
        # http://gstreamer.freedesktop.org/data/doc/gstreamer/head/gstreamer-libs/html/gstreamer-libs-GstBaseSrc.html
        if self._vsource:
            self._vsource.set_state(gst.STATE_NULL)
            self._vsource.set_locked_state(True)
        if self._asource:
            self._asource.set_state(gst.STATE_NULL)
            self._asource.set_locked_state(True)

    def on_eos(self):
        # let us present a cool save widget
        screen = Screen().current
        width = screen.get_width()/4
        height = screen.get_height()/4

        savewindow = SaveWindow(self.temp_file[1], width, height)
        savewindow.connect('destroy', self.finished_callback)
        savewindow.show()

    def save(self):
        pass


class CmdlineScreencast(Screencast):
    def __init__(self, finished_callback, options):
        self.options = options
        Screencast.__init__(self, finished_callback)

    def start_recording(self, filename = None):
        if self.options.coords:
            # create selector from cmdline args
            class CmdlineSelector:
                def get_area(self):
                    return self.x1, self.y1, self.x2, self.y2

            self.selector = CmdlineSelector()
            self.selector.x1 = self.options.coords[0]
            self.selector.y1 = self.options.coords[1]
            self.selector.x2 = self.options.coords[2]
            self.selector.y2 = self.options.coords[3]

        settings = Preferences().Settings
        for optkey, optvalue in self.options.__dict__.items():
            if optvalue is not None:
                settings[optkey] = optvalue

        Screencast.start_recording(self, self.options.record_file, settings = settings)

    def on_eos(self):
        print 'on eos!'
        gtk.main_quit()
