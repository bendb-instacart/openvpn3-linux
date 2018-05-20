#  OpenVPN 3 Linux client -- Next generation OpenVPN client
#
#  Copyright (C) 2018         OpenVPN Inc. <sales@openvpn.net>
#  Copyright (C) 2018         David Sommerseth <davids@openvpn.net>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, version 3 of the
#  License.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

##
# @file  SessionManager.py
#
# @brief  Provides a Python class to communicate with the OpenVPN 3
#         session manager service over D-Bus
#

import dbus
from openvpn3.constants import StatusMajor, StatusMinor

##
#  The Session object represents a single OpenVPN VPN session as
#  presented via the OpenVPN 3 session manager D-Bus service.
class Session(object):
    ##
    #  Initialize the Session object.  It requires a D-Bus connection
    #  object and the D-Bus object path to the VPN session
    #
    #  @param dbuscon  D-Bus connection object
    #  @param objpath  D-Bus object path to the VPN session
    #
    def __init__(self, dbuscon, objpath):
        self.__dbuscon = dbuscon

        # Retrieve access to the session object
        self.__session = self.__dbuscon.get_object('net.openvpn.v3.sessions',
                                                   objpath)

        # Retrive access to the session interface in the object
        self.__session_intf = dbus.Interface(self.__session,
                                             dbus_interface="net.openvpn.v3.sessions")

        # Retrive access to the property interface in the object
        self.__prop_intf = dbus.Interface(self.__session,
                                          dbus_interface="org.freedesktop.DBus.Properties")

        self.__session_path = objpath


    ##
    #  Returns the D-Bus configuration object path
    #
    #  @return String containing the D-Bus object path
    #
    def GetPath(self):
        return self.__session_path


    ##
    #  Sets a specific property in the VPN session object
    #
    #  @param propname   String containing the property name to modify
    #  @param propvalue  The new value the property should have. The data
    #                    type ov the value must match the data type of the
    #                    property in the D-Bus object
    #
    def SetProperty(self, propname, propvalue):
        self.__prop_intf.Set('net.openvpn.v3.sessions',
                             propname, propvalue)


    ##
    #  Retrieve the value of a property in a VPN session object
    #
    #   @param propname  String containing the property name to query
    #
    def GetProperty(self, propname):
        return self.__prop_intf.Get('net.openvpn.v3.sessions', propname)


    ##
    #  Checks if the VPN backend process is ready to start connecting
    #
    def Ready(self):
        self.__session_intf.Ready()


    ##
    #  Tells the VPN backend process to start the connection
    def Connect(self):
        self.__session_intf.Connect()


    ##
    #  Tells the VPN backend to disconnect and shutdown the connection
    #
    def Disconnect(self):
        self.__session_intf.Disconnect()


    ##
    #  Retrive the session status
    #
    #  @return  Returns a type of (StatusMajor, StatusMinor, Status message)
    #           The Status message is a plain string.
    def GetStatus(self):
        status = self.__prop_intf.Get('net.openvpn.v3.sessions',
                                      'status')
        return (StatusMajor(status['major']),
                StatusMinor(status['minor']),
                status['status_message'])


    ##
    #  Retrieve session statistics
    #
    #  @return Returns a formatted string containing the statistics
    #
    def GetStatistics(self):
        return self.__prop_intf.Get('net.openvpn.v3.sessions',
                                        'statistics')

    ##
    #  Retrieve session statistics as a pre-formatted string
    #
    #  @param prefix      Start the result with the provides string
    #                     Defaults to: 'Connection statistics:\n'
    #  @param format_str  Format string to use.  It will always be a string
    #                     and an integer, in that order.
    #                     Defaults to: '    %25s: %i\n'
    #  @return Returns a formatted string containing the statistics
    #
    def GetFormattedStatistics(self, prefix='Connection statistics:\n', format_str='    %25s: %i\n'):
        statistics = self.GetStatistics()
        ret = ""
        if len(statistics) > 0:
            ret += prefix
            for (key, val) in statistics.items():
                ret += format_str % (key, val)

        return ret


    ##
    #  Queries the VPN backend if the user needs to be queried for information
    #
    #  @return Returns a list of tuples of Queue types and groups which needs
    #          to be satisfied
    #
    def UserInputQueueGetTypeGroup(self):
        return self.__session_intf.UserInputQueueGetTypeGroup()


    ##
    #  Queries the VPN backend for query slots needing to be satisifed within
    #  a queue type and group.
    #
    #  @param  qtype   Queue type to check
    #  @param  qgroup  Queue group to check
    #
    #  @returns a list of unique ID references to slots needing to be satisfied
    #
    def UserInputQueueCheck(self, qtype, qgroup):
        return self.__session_intf.UserInputQueueCheck(qtype, qgroup)


    ##
    #  Retrieve information about a specific user input slot which needs to be
    #  satisfied.  This provides information what to query for and how to
    #  process the data
    #
    #  @param  qtype   Queue type of the user input slot
    #  @param  qgroup  Queue group of the user input slot
    #  @param  qid     Queue ID of the user inout slot to retrieve
    #
    #  @return Returns a list containing all the details needing to be
    #          satisfied
    #
    #  FIXME: Return an UserInput object instead
    #
    def UserInputQueueFetch(self, qtype, qgroup, qid):
        return self.__session_intf.UserInputQueueFetch(qtype, qgroup, qid)


    ##
    # Provide user's input to a specific user input slot
    #
    #  @param  qtype     Queue type of the user input slot
    #  @param  qgroup    Queue group of the user input slot
    #  @param  qid       Queue ID of the user inout slot
    #  @param  response  String containing the users response
    #
    #  FIXME:  Move into the UserInput object instead
    #
    def UserInputProvide(self, qtype, qgroup, qid, response):
        self.__session_intf.UserInputProvide(qtype, qgroup, qid, response)



##
#  The SessionManager object provides access to the main object in
#  the session manager D-Bus service.  This is primarily used to create
#  new VPN tunnel sessions, but can also be used to retrieve specific objects
#  when the session D-Bus object path is known.
#
class SessionManager(object):
    ##
    #  Initialize the SessionManager object
    #
    #  @param  dbuscon   D-Bus connection object to use
    #
    def __init__(self, dbuscon):
        self.__dbuscon = dbuscon

        # Retrieve the main sessoin manager object
        self.__manager_object = dbuscon.get_object('net.openvpn.v3.sessions',
                                                   '/net/openvpn/v3/sessions')

        # Retireve access to the session interface in the object
        self.__manager_intf = dbus.Interface(self.__manager_object,
                                          dbus_interface='net.openvpn.v3.sessions')


    ##
    #  Create a new VPN session
    #
    #  @param cfgobj      openvpn3.Configuration object to use for this new
    #                     session
    #
    #  @return Returns a Session object of the imported configuration
    #
    def NewTunnel(self, cfgobj):
            path = self.__manager_intf.NewTunnel(cfgobj.GetPath())
            return Session(self.__dbuscon, path)


    ##
    #  Retrieve a single Session object for a specific configuration path
    #
    #  @param objpath   D-Bus object path to the VPN session to retrieve
    #
    #  @return Returns a Session object of the requested VPN session
    #
    def Retrieve(self, objpath):
        return Session(self.__dbuscon, objpath)


    ##
    #  Retrieve a list of all available VPN sessions in the
    #  session manager
    #
    #  @return Returns a list of Session object, one for each session
    #
    def FetchAvailableSessions(self):
        ret = []
        for s in self.__manager_intf.FetchAvailableSessions():
            ret.append(Session(self.__dbuscon, s))
        return ret
