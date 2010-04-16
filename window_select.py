# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4
#
# Istanbul - A desktop recorder
# Copyright(C) 2006 Chong Kai Xiong(descender at phreaker dot org)
# All rights reserved.

# This file may be distributed and/or modified under the terms of
# the GNU General Public License version 2 as published by
# the Free Software Foundation.
# This file is distributed without any warranty; without even the implied
# warranty of merchantability or fitness for a particular purpose.
# See 'LICENSE.GPL' in the source distribution for more information.

import Xlib.X as X
import Xlib.display as XDisplay
import Xlib.xobject.drawable as XDrawable
import Xlib.Xcursorfont as XCursorFont

from istanbul.main.preferences import Preferences
import locale, gettext
_ = gettext.gettext

# color constants
BLACK_COLOR = (0, 0, 0)
WHITE_COLOR = (0xffff, 0xffff, 0xffff)

class WindowSelector:
    def __init__(self):
        self.target_window = None

    def select_window(self):
        self.target_window = self._select_window()

        return self.target_window

    def get_area(self):
        # Let user select window if we don't already have one selected
        if self.target_window == None:
            self.select_window()

        target_window = self.target_window

        settings = Preferences().Settings
        root_window = target_window.get_geometry().root

        # Exclude decorations if requested and if selected window isn't the root
        if target_window != root_window and not settings['record_decorations']:
            target_window = self._get_client_window (target_window)

        # Compute area in root window coordinates
        geometry = target_window.get_geometry()
        result = geometry.root.translate_coords (target_window, 0, 0)
        
        x1, y1 = result.x, result.y
        x2, y2 = x1 + geometry.width - 1, y1 + geometry.height - 1
        
        return x1, y1, x2, y2

    def _create_font_cursor(self, display, shape, fg_color = BLACK_COLOR, bg_color = WHITE_COLOR):
        # Create a glyph cursor from the cursor font. This is a almost a direct translation of
        # XCreateFontCursor().

        cursor_font = display.open_font('cursor')
        return cursor_font.create_glyph_cursor(cursor_font, shape, shape + 1, fg_color, bg_color)

    def _get_client_window(self, window):
        # Breadth-first search for window with WM_STATE set. This is
        # exactly what XmuClientWindow() does.

        if window.get_wm_state() != None:
            return window

        result = self._get_client_window_check_children(window)
        if result != None:
            return result
    
        return window

    def _get_client_window_check_children(self, window):
        children = window.query_tree().children

        for child in children:
            if child.get_wm_state() != None:
                return child

        for child in children:
            result = self._get_client_window_check_children(child)
            if result != None:
                return result

        return None

    def _select_window(self):
        display = XDisplay.Display()
        screen = display.screen()
        root_window = screen.root

        cursor = self._create_font_cursor(display, XCursorFont.crosshair)
    
        root_window.grab_pointer(False, X.ButtonPressMask | X.ButtonReleaseMask,
                                 X.GrabModeSync, X.GrabModeAsync,
                                 root_window, cursor,
                                 X.CurrentTime)

        target_window = None

        n_buttons = 0

        while target_window == None or n_buttons != 0:
            display.allow_events(X.SyncPointer, X.CurrentTime)
            event = display.next_event()

            if event.type == X.ButtonPress:
                target_window = event.child
                if target_window == None:
                    target_window = root_window

                n_buttons = n_buttons + 1

            elif event.type == X.ButtonRelease:
                if n_buttons > 0:
                    n_buttons = n_buttons - 1
                        
        display.ungrab_pointer(X.CurrentTime)
        display.flush()

        return target_window

def main(args):
    selector = WindowSelector()

    print 'Select window to grab now'
    window = selector.get_target_window()

    print window
    print window.get_geometry()

    return 0

if __name__ == '__main__':
    import sys, time

    sys.exit(main(sys.argv))
