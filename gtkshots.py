#!/usr/bin/env python
# gtkShots - An utility to grab screenshots continuosly
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

import gtk, gtk.glade, gobject, os, os.path, cPickle, time, webbrowser, gettext, sys
if os.path.basename(sys.argv[0]) == 'gtkshots.py':
    if os.path.dirname(sys.argv[0]) != '':
        os.chdir(os.path.dirname(sys.argv[0]))
gettext.bindtextdomain('gtkshots', 'po')
gettext.textdomain('gtkshots')
gettext.install('gtkshots', 'po', True)
gtk.glade.bindtextdomain('gtkshots', 'po')

class gtkShots:

    def __init__(self):
        self.homepage = 'http://www.flagar.com/en/software/gtkshots'
        self.home = os.path.expanduser('~')
	self.prefsfile = os.path.join(self.home, '.gtkshots')
        self.LoadPreferences()
        self.win = gtk.glade.XML('gtkshots.glade', 'window1', 'gtkshots')
        self.win_callbacks = {'on_window1_destroy':self.Quit, 'on_controlbutton_toggled':self.Control,
                              'on_start1_activate':(self.ToggleControl, True), 'on_stop1_activate':(self.ToggleControl, False), 
                              'on_quit1_activate':self.Quit,
                              'on_donate1_activate':(self.LaunchBrowser, 'https://www.paypal.com/xclick/business=flagar%40gmail.com&item_name=Helping+gtkShots+development&no_shipping=1&tax=0&currency_code=EUR&lc=US'),
                              'on_folderchooserbutton_current_folder_changed':self.UpdateFolder, 'on_sizecombobox_changed':self.UpdateSize,
                              'on_frequencycombobox_changed':self.UpdateFrequency, 'on_daemoncheckbutton_toggled':self.UpdateDaemon,
                              'on_startradiobutton_toggled':(self.ScheduledStart, False), 'on_scheduledstartradiobutton_toggled':(self.ScheduledStart, True),
                              'on_stopradiobutton_toggled':(self.ScheduledStop, False), 'on_scheduledstopradiobutton_toggled':(self.ScheduledStop, True),
                              'on_starthspinbutton_value_changed':self.UpdateStartTime, 'on_startmspinbutton_value_changed':self.UpdateStartTime,
                              'on_stophspinbutton_value_changed':self.UpdateStopTime, 'on_stopmspinbutton_value_changed':self.UpdateStopTime,
                              'on_about1_activate':self.About}
        self.pyshotsfilename = os.path.join(os.path.expanduser('~'), '.pyshots')
        self.start1 = self.win.get_widget('start1')
        self.stop1 = self.win.get_widget('stop1')
        self.starthspinbutton = self.win.get_widget('starthspinbutton')
        self.startmspinbutton = self.win.get_widget('startmspinbutton')
        self.stophspinbutton = self.win.get_widget('stophspinbutton')
        self.stopmspinbutton = self.win.get_widget('stopmspinbutton')
        self.controlbutton = self.win.get_widget('controlbutton')
        self.controlbutton_image = self.win.get_widget('image5')
        self.controlbutton_label = self.win.get_widget('label5')
        self.statusbar = self.win.get_widget('statusbar1')
        self.statusbar_context = self.statusbar.get_context_id('gtkShots')
        if os.path.isfile(self.pyshotsfilename):
            self.controlbutton.set_active(True)
            self.controlbutton_image.set_from_stock(gtk.STOCK_STOP, gtk.ICON_SIZE_BUTTON)
            self.controlbutton_label.set_text(_('Stop'))
            self.start1.set_sensitive(False)
            self.statusbar.push(self.statusbar_context, _('gtkShots pyshots running...'))
        else:
            self.stop1.set_sensitive(False)
            self.statusbar.push(self.statusbar_context, _('Ready.'))
        self.sizes = ['100%', '75%', '50%', '25%', '10%']
        self.frequencies = [5, 15, 30, 60, 300, 600, 900, 1200, 1800, 3600, 10800, 21600, 43200, 86400]
        self.folderchooserbutton = self.win.get_widget('folderchooserbutton')
        self.sizecombobox = self.win.get_widget('sizecombobox')
        self.frequencycombobox = self.win.get_widget('frequencycombobox')
        self.daemoncheckbutton = self.win.get_widget('daemoncheckbutton')
        self.folderchooserbutton.set_current_folder(self.prefs['folder'])
        self.sizecombobox.set_active(self.sizes.index(self.prefs['size']))
        self.frequencycombobox.set_active(self.frequencies.index(self.prefs['frequency']))
        self.daemoncheckbutton.set_active(self.prefs['daemon'])
        if self.prefs['scheduledstart']:
            self.win.get_widget('scheduledstartradiobutton').set_active(True)
            self.starthspinbutton.set_sensitive(True)
            self.startmspinbutton.set_sensitive(True)
        else:
            self.win.get_widget('startradiobutton').set_active(True)
        if self.prefs['scheduledstop']:
            self.win.get_widget('scheduledstopradiobutton').set_active(True)
            self.stophspinbutton.set_sensitive(True)
            self.stopmspinbutton.set_sensitive(True)
        else:
            self.win.get_widget('stopradiobutton').set_active(True)
        self.starthspinbutton.set_value(self.prefs['starttime'][0])
        self.startmspinbutton.set_value(self.prefs['starttime'][1])
        self.stophspinbutton.set_value(self.prefs['stoptime'][0])
        self.stopmspinbutton.set_value(self.prefs['stoptime'][1])
        self.win.signal_autoconnect(self.win_callbacks)

    def UpdateFolder(self, widget):
        self.prefs['folder'] = self.folderchooserbutton.get_current_folder()

    def UpdateSize(self, widget):
        self.prefs['size'] = self.sizes[self.sizecombobox.get_active()]
        scale = int(self.sizes[self.sizecombobox.get_active()][:-1])/100.0
        width = int(gtk.gdk.screen_width()*scale)
        height = int(gtk.gdk.screen_height()*scale)
	self.statusbar.push(self.statusbar_context, _('Image size will be %sx%s') % (width, height))

    def UpdateFrequency(self, widget):
        self.prefs['frequency'] = self.frequencies[self.frequencycombobox.get_active()]
        if self.prefs['scheduledstop']:
            self.UpdateStopTime(None)

    def UpdateDaemon(self, widget):
        self.prefs['daemon'] = self.daemoncheckbutton.get_active()
        if self.prefs['daemon']:
            self.statusbar.push(self.statusbar_context, _('Then relaunch gtkShots to stop'))
        else:
            self.statusbar.push(self.statusbar_context, '')

    def ScheduledStart(self, widget, schedule):
        if schedule:
            self.starthspinbutton.set_sensitive(True)
            self.startmspinbutton.set_sensitive(True)
            self.prefs['scheduledstart'] = True
        else:
            self.starthspinbutton.set_sensitive(False)
            self.startmspinbutton.set_sensitive(False)
            self.prefs['scheduledstart'] = False

    def ScheduledStop(self, widget, schedule):
        if schedule:
            self.stophspinbutton.set_sensitive(True)
            self.stopmspinbutton.set_sensitive(True)
            self.prefs['scheduledstop'] = True
            self.UpdateStopTime(None)
        else:
            self.stophspinbutton.set_sensitive(False)
            self.stopmspinbutton.set_sensitive(False)
            self.prefs['scheduledstop'] = False
            self.statusbar.push(self.statusbar_context, '')

    def UpdateStartTime(self, widget):
        self.prefs['starttime'] = (self.starthspinbutton.get_value_as_int(), self.startmspinbutton.get_value_as_int())

    def UpdateStopTime(self, widget):
        self.prefs['stoptime'] = (self.stophspinbutton.get_value_as_int(), self.stopmspinbutton.get_value_as_int())
        imgs = (self.prefs['stoptime'][0]*3600+self.prefs['stoptime'][1]*60)/self.prefs['frequency']+1
        self.statusbar.push(self.statusbar_context, _('%s images will be saved') % imgs)

    def ToggleControl(self, widget, is_active):
        self.controlbutton.set_active(is_active)

    def Control(self, widget):
        while gtk.events_pending():
            gtk.main_iteration(False)
        if self.controlbutton.get_active():
            self.controlbutton_image.set_from_stock(gtk.STOCK_STOP, gtk.ICON_SIZE_BUTTON)
            self.controlbutton_label.set_text(_('Stop'))
            self.Start(None)
        else:
            self.controlbutton_image.set_from_stock(gtk.STOCK_MEDIA_RECORD, gtk.ICON_SIZE_BUTTON)
            self.controlbutton_label.set_text(_('Start'))
            self.Stop(None)
        while gtk.events_pending():
            gtk.main_iteration(False)

    def Quit(self, widget):
        self.StorePreferences()
        gtk.main_quit()

    def Start(self, widget):
        self.start1.set_sensitive(False)
        self.stop1.set_sensitive(True)
        #while gtk.events_pending():
        #    gtk.main_iteration()
        #self.pyshots = os.spawnvp(os.P_NOWAIT, 'python', ('python', '/home/flagar/gtkshots/pyshots.py', '-d'))
        self.StorePreferences()
        time.sleep(1)
        pyshots_opts = ['python', './pyshots.py', '-t', str(self.prefs['frequency']), '-s', self.prefs['size'], '-f', self.prefs['folder']]
        if self.prefs['scheduledstart']:
            pyshots_opts.extend(['-z', str(self.prefs['starttime'][0]*3600+self.prefs['starttime'][1]*60)])
        if self.prefs['scheduledstop']:
            pyshots_opts.extend(['-u', str(self.prefs['stoptime'][0]*3600+self.prefs['stoptime'][1]*60)])
        if self.prefs['daemon']:
            pyshots_opts.append('-d')
            os.execvp('python', pyshots_opts)
        else:
            os.spawnvp(os.P_NOWAIT, 'python', pyshots_opts)
        #while gtk.events_pending():
        #    gtk.main_iteration()
        self.statusbar.push(self.statusbar_context, _('gtkShots pyshots started!'))

    def Stop(self, widget):
        self.stop1.set_sensitive(False)
        self.start1.set_sensitive(True)
        pidfile = open(self.pyshotsfilename)
        pyshots = int(pidfile.read())
        pidfile.close()
        os.kill(pyshots, 15)  # SIGTERM
        #os.kill(pyshots, 9)  # SIGKILL
        #os.remove(self.pyshotsfilename)
        self.statusbar.push(self.statusbar_context, _('gtkShots pyshots stopped!'))

    def About(self, widget):
	gtk.about_dialog_set_url_hook(self.LaunchBrowser)
        self.about = gtk.glade.XML('gtkshots.glade', 'aboutdialog1', 'gtkshots')
	self.aboutdlg = self.about.get_widget('aboutdialog1')
	self.aboutdlg.set_icon_from_file('gtkshots.svg')

    def LaunchBrowser(self, widget, link):
        webbrowser.open(link)

    def DefaultPreferences(self):
        self.prefs['folder'] = os.path.join(self.home, 'Desktop', 'PyScreens')
	self.prefs['size'] = '50%'
	self.prefs['frequency'] = 30
        self.prefs['daemon'] = False
        self.prefs['scheduledstart'] = False
        self.prefs['starttime'] = (0, 0)
        self.prefs['scheduledstop'] = False
        self.prefs['stoptime'] = (1, 0)

    def LoadPreferences(self):
        self.prefs = {}
        self.DefaultPreferences()
        if os.path.isfile(self.prefsfile):
            prefsfile = open(self.prefsfile, 'r')
   	    prefs = cPickle.load(prefsfile)
	    for prefkey, prefvalue in prefs.iteritems():
	        self.prefs[prefkey] = prefvalue
	    prefsfile.close()

    def StorePreferences(self):
        prefsfile = open(self.prefsfile, 'w+')
	cPickle.dump(self.prefs, prefsfile)
	prefsfile.close()

if __name__ == '__main__':
    gtkShots()
    gtk.main()
