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

class Screen:
    event_box = gtk.EventBox()
    current = event_box.get_screen()

