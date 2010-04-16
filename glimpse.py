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

class glimpse:
    def __init__(self):
        self.__initialize_gui()
        self.home = os.path.expanduser('~')
        self.prefsfile = os.path.join(self.home, '.glimpse')
        self.LoadPreferences()       
        self.win.signal_autoconnect(self.win_callbacks)

    def __initialize_gui(self):
        self.win = gtk.glade.XML('glimpse.glade', 'MainWindow', 'glimpse')
        self.win_callbacks = {
            'on_MainWindow_destroy':self.Quit,
            'on_StartItem_activate':(self.ToggleControl, True),
            'on_StopItem_activate':(self.ToggleControl, False), 
            'on_QuitItem_activate':self.Quit,
            'on_AboutItem_activate':self.About, 
            'on_AboutItem_close':self.CloseAbout, 
            'on_FolderChooserButton_current_folder_changed':self.UpdateFolder,
            'on_TimeTriggerCheckButton_toggled':self.EnableFrequency,
            'on_TimeTriggerSpinButton_value_changed':self.UpdateFrequency,
            'on_KeyboardTriggerCheckButton_toggled': self.EnableKeyboard, 
            'on_MouseTriggerCheckButton_toggled': self.EnableMouse, 
            'on_DelaySpinButton_change_value':self.UpdateDelay,
            'on_StopManuallyRadioButton_toggled':self.UpdateStopManually,
            'on_StopScheduledRadioButton_toggled':self.UpdateStopScheduled,
            'on_StopScheduledSpinButton_change_value':self.UpdateStopScheduledTime,
            'on_ToggleButton_toggled':self.Control
        }
        self.StartItem = self.win.get_widget('StartItem')
        self.StopItem = self.win.get_widget('StopItem')
        self.QuitItem = self.win.get_widget('QuitItem')
        self.AboutItem = self.win.get_widget('AboutItem')

        self.FolderChooserButton = self.win.get_widget('FolderChooserButton')

        self.TimeTriggerCheckButton = self.win.get_widget('TimeTriggerCheckButton')
        self.TimeTriggerSpinButton = self.win.get_widget('TimeTriggerSpinButton')
        self.KeyboardTriggerCheckButton = self.win.get_widget('KeyboardTriggerCheckButton')
        self.MouseTriggerSpinButton = self.win.get_widget('MouseTriggerSpinButton')

        self.DelaySpinButton = self.win.get_widget('DelaySpinButton')

        self.StopManuallyCheckButton = self.win.get_widget('StopManuallyCheckButton')
        self.StopScheduledCheckButton = self.win.get_widget('StopScheduledCheckButton')
        self.StopScheduledSpinButton = self.win.get_widget('StopScheduledSpinButton')
        
        self.ControlToggleButton = self.win.get_widget('ControlToggleButton')

        self.StatusBar = self.win.get_widget('StatusBar')
        self.StatusBarContext = self.StatusBar.get_context_id('glimpse')


    def UpdateFolder(self, widget):
        self.prefs['folder'] = self.folderchooserbutton.get_current_folder()

    def EnableFrequency(self,  widget):
        self.prefs['frequency_enabled'] - self.timertriggerspinbutton.get_value_as_int()

    def UpdateFrequency(self, widget):
        self.prefs['frequency'] = self.frequencies[self.frequencycombobox.get_active()]
        if self.prefs['scheduledstop']:
            self.UpdateStopTime(None)

    def EnableKeyboard(self,  widget):
        self.prefs['keyboard_enabled'] - self.keyboardtriggercheckbutton.get_value()

    def EnableMouse(self,  widget):
        self.prefs['mouse_enabled'] - self.mousetriggercheckbutton.get_value()

    def UpdateDelay(self, widget):
        self.prefs['scheduledstart'] = True
        self.prefs['starttime'] = self.delayspinbutton.get_value_as_int()

    def UpdateStopManually(self, widget):
        if self.stopmanuallyradiobutton.get_value_as_boolean():
            self.stopscheduledspinbutton.set_sensitive(False)
            self.prefs['stop_strategy'] = 'manual'
        else:
            self.stopscheduledspinbutton.set_sensitive(True)
            self.prefs['stop_strategy'] = 'scheduled'
        self.UpdateStopTime(widget)

    def UpdateStopScheduled(self, widget, schedule):
        if self.stopscheduledspinbutton.get_value_as_boolean():
            self.stopscheduledspinbutton.set_sensitive(True)
            self.prefs['stop_strategy'] = 'scheduled'
        else:
            self.stopscheduledspinbutton.set_sensitive(False)
            self.prefs['stop_strategy'] = 'manual'
        self.UpdateStopTime(widget)

    def UpdateStopScheduledTime(self, widget):
        self.prefs['stoptime'] = self.stopscheduledspinbutton.get_value_as_int()
        
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
        
    def CloseAbout(self,  widget):
        widget.destroy()

    def Start(self, widget):
        self.start1.set_sensitive(False)
        self.stop1.set_sensitive(True)
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
        self.statusbar.push(self.statusbar_context, _('gtkShots pyshots started!'))

    def Stop(self, widget):
        self.stop1.set_sensitive(False)
        self.start1.set_sensitive(True)
        pidfile = open(self.pyshotsfilename)
        pyshots = int(pidfile.read())
        pidfile.close()
        os.kill(pyshots, 15)  # SIGTERM
        self.statusbar.push(self.statusbar_context, _('gtkShots pyshots stopped!'))

    def About(self, widget):
        gtk.about_dialog_set_url_hook(self.LaunchBrowser)
        self.about = gtk.glade.XML('glimpse.glade', 'AboutDialog', 'glimpse')
        self.aboutdlg = self.about.get_widget('AboutDialog')
        self.aboutdlg.set_icon_from_file('glimpse.svg')

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
            
        self.FolderChooserButton.set_current_folder(self.prefs['folder'])
        # self.frequencycombobox.set_active(self.frequencies.index(self.prefs['frequency']))
        # self.daemoncheckbutton.set_active(self.prefs['daemon'])
#        if self.prefs['scheduledstart']:
#            self.win.get_widget('scheduledstartradiobutton').set_active(True)
#            self.starthspinbutton.set_sensitive(True)
#            self.startmspinbutton.set_sensitive(True)
#        else:
#            self.win.get_widget('startradiobutton').set_active(True)
#        if self.prefs['scheduledstop']:
#            self.win.get_widget('scheduledstopradiobutton').set_active(True)
#            self.stophspinbutton.set_sensitive(True)
#            self.stopmspinbutton.set_sensitive(True)
#        else:
#            self.win.get_widget('stopradiobutton').set_active(True)
#        self.starthspinbutton.set_value(self.prefs['starttime'][0])
#        self.startmspinbutton.set_value(self.prefs['starttime'][1])
#        self.stophspinbutton.set_value(self.prefs['stoptime'][0])
#        self.stopmspinbutton.set_value(self.prefs['stoptime'][1])


    def StorePreferences(self):
        prefsfile = open(self.prefsfile, 'w+')
        cPickle.dump(self.prefs, prefsfile)
        prefsfile.close()

if __name__ == '__main__':
    if os.path.basename(sys.argv[0]) == 'glimpse.py':
        if os.path.dirname(sys.argv[0]) != '':
            os.chdir(os.path.dirname(sys.argv[0]))
    gettext.bindtextdomain('glimpse', 'po')
    gettext.textdomain('glimpse')
    gettext.install('glimpse', 'po', True)
    gtk.glade.bindtextdomain('glimpse', 'po')
    glimpse()
    gtk.main()
