
#
# gPodder (a media aggregator / podcast client)
# Copyright (C) 2005-2006 Thomas Perl <thp at perli.net>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, 
# MA  02110-1301, USA.
#


#
#  libplayers.py -- get list of potential playback apps
#  thomas perl <thp@perli.net>   20060329
#
#

from glob import glob
from os.path import basename
from os.path import splitext
from os.path import exists

from ConfigParser import RawConfigParser

import gobject

from gtk import IconTheme
from gtk import ListStore

from gtk.gdk import pixbuf_new_from_file_at_size
from gtk.gdk import Pixbuf

from liblogger import log

# where are the .desktop files located?
userappsdirs = [ '/usr/share/applications/', '/usr/local/share/applications/' ]

# the name of the section in the .desktop files
sect = 'Desktop Entry'

class UserApplication(object):
    def __init__( self, name, cmd, mime, icon):
        self.name = name
        self.cmd = cmd
        self.icon = icon
        self.theme = IconTheme()

    def get_icon( self):
        if self.icon != None:
            if exists( self.icon):
                return pixbuf_new_from_file_at_size( self.icon, 24, 24)
            icon_name = splitext( basename( self.icon))[0]
            if self.theme.has_icon( icon_name):
                return self.theme.load_icon( icon_name, 24, 0)

    def get_name( self):
        return self.name

    def get_action( self):
        return self.cmd


class UserAppsReader(object):
    def __init__( self):
        self.apps = []

    def read( self):
        for dir in userappsdirs:
            if exists( dir):
                for file in glob( dir+'/*.desktop'):
                    self.parse_and_append( file)
        self.apps.append( UserApplication( 'Shell command', '', 'audio/*', 'gtk-execute'))

    def parse_and_append( self, filename):
        try:
            parser = RawConfigParser()
            parser.read( [ filename ])
            if not parser.has_section( sect):
                return
        
            app_name = parser.get( sect, 'Name')
            app_cmd = parser.get( sect, 'Exec')
            app_mime = parser.get( sect, 'MimeType')
            app_icon = parser.get( sect, 'Icon')
            if app_mime.find( 'audio/') != -1:
                log( 'Player found: %s (%s)', app_name, filename)
                self.apps.append( UserApplication( app_name, app_cmd, app_mime, app_icon))
        except:
            return

    def get_applications_as_model( self):
        result = ListStore( gobject.TYPE_STRING, gobject.TYPE_STRING, Pixbuf)
        for app in self.apps:
            iter = result.append()
            result.set_value( iter, 0, app.get_name())
            result.set_value( iter, 1, app.get_action())
            result.set_value( iter, 2, app.get_icon())
        return result
# end of UserAppsReader


def dotdesktop_command( command, filename):
    # the following flags are specified in the FDO standards for ".desktop" files:
    # http://standards.freedesktop.org/desktop-entry-spec/desktop-entry-spec-0.9.4.html
    if command.find( '%U') != -1:
        # A list of URLs. (we only need one, anyway..)
        return command.replace( '%U', ( '"file://%s"' % (filename) ) )
    if command.find( '%u') != -1:
        # A single URL.
        return command.replace( '%u', ( '"file://%s"' % (filename) ) )
    if command.find( '%F') != -1:
        # A list of files. (we only need one...)
        return command.replace( '%F', filename )
    if command.find( '%f') != -1:
        # A single file name, even if multiple files are selected.
        return command.replace( '%f', filename )

    # default known-good variant: 1st parameter = filename
    return '%s "%s"' % ( command, filename )
# end dotdesktop_command


