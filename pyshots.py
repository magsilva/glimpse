#!/usr/bin/env python
# pyshots (gtkShots) - An utility to grab screenshots continuosly
# Copyright (C) 2006 Flavio Gargiulo (FLAGAR.com)
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import gtk, time, os, os.path, sys, signal, gettext
from optparse import OptionParser
gettext.bindtextdomain('pyshots', 'po')
gettext.textdomain('pyshots')
gettext.install('pyshots', 'po', True)

class PyShots:
    """ PyShots main class """

    def __init__(self, folder, size, frequency, daemon, starttime, stoptime):
        """ PyShot init """
        self.size = int(size.replace('%', ''))/100.0
        self.frequency = int(frequency)
        self.folder = folder
        self.starttime = int(starttime)
        self.stoptime = int(stoptime)
        self.screens_session = True
        self.pidfile = os.path.join(os.path.expanduser('~'), '.pyshots')
        if daemon:
            self.Fork()
        
    def Fork(self):
        """ Run as daemon (double forking on Posix) """
        pid = os.fork()
        if pid > 0:
            os._exit(0)
        #pid = os.fork()
        #if pid > 0:
        #    sys.exit(0)

    def Start(self):
        """ Start grabbing screenshots """
        if not os.path.isdir(self.folder):
            os.makedirs(self.folder)
        pidf = open(self.pidfile, 'w+')
        pidf.write(str(os.getpid()))
        pidf.close()
        if self.starttime > 0:
            time.sleep(self.starttime)
        n_screenshots = int(self.stoptime/self.frequency)
        n_screenshot = 0
        while self.screens_session:
            try:
                screenshot = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, 
	                                    gtk.gdk.screen_width(), gtk.gdk.screen_height())
                screenshot.get_from_drawable(gtk.gdk.get_default_root_window(),
                                             gtk.gdk.colormap_get_system(), 0, 0, 0, 0,
                                             gtk.gdk.screen_width(), gtk.gdk.screen_height())
                if self.size < 1:
                    img_width = int(gtk.gdk.screen_width()*self.size)
                    img_height = int(gtk.gdk.screen_height()*self.size)
                    screenshot = screenshot.scale_simple(img_width, img_height, gtk.gdk.INTERP_BILINEAR)
                t = time.localtime()
                screenshot_filename = "screenshot-%s-%s-%s-%s-%s-%s.jpeg" % (t[0], t[1], t[2], t[3], t[4], t[5])
  	        screenshot_filename = os.path.join(self.folder, screenshot_filename)
      	        if not os.path.isfile(screenshot_filename):
  	            screenshot.save(screenshot_filename, "jpeg")
                if n_screenshots >= 0:
                    if n_screenshot >= n_screenshots:
                        self.Stop()
                    n_screenshot += 1
     	        time.sleep(self.frequency)
            except:
                self.Stop()

    def Stop(self):
        """ Stop grabbing screenshots """
	self.screens_session = False
        os.remove(self.pidfile)
	
    def Kill(self):
        """ Stop grabbing screenshots and exit """
        self.Stop()
        sys.exit()


if __name__ == '__main__':
    defaultfolder = os.path.join(os.path.expanduser('~'), 'Desktop', 'PyScreens')
    parser = OptionParser()
    parser.add_option('-f', '--folder', dest='folder', default=defaultfolder, help=_('The folder where screenshots should be saved. Default is ~/Desktop/PyScreens'))
    parser.add_option('-s', '--size', dest='size', default='100%', help=_('The resize percentage for the screenshots to save. Default is 100% (no resize)'))
    parser.add_option('-t', '--frequency', dest='frequency', default=300, help=_('Snap a screenshot every (the given number of) seconds. Default is 300 (5 minutes)'))
    parser.add_option('-z', '--start-after', dest='starttime', default=-1, help=_('Start after a number of seconds. Default is 0, start now'))
    parser.add_option('-u', '--stop-after', dest='stoptime', default=-1, help=_('Stop after a number of seconds. Default is -1, stop manually'))
    parser.add_option('-d', '--daemon', dest='daemon', action='store_true', default=False, help=_('Run as daemon'))
    opts, args = parser.parse_args()
    shots = PyShots(opts.folder, opts.size, opts.frequency, opts.daemon, opts.starttime, opts.stoptime)
    signal.signal(signal.SIGTERM, shots.Kill)
    try:
        shots.Start()
    except:
        shots.Stop()
