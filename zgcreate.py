#!/usr/bin/env python3
#
# import needed modules.
# pyzabbix is needed, see https://github.com/lukecyca/pyzabbix
#
import argparse
import configparser
import os
import os.path
import distutils.util
import cmd
import traceback
import sys
from pyzabbix import ZabbixAPI


# define config helper function
def config_section_map(section):
    dict1 = {}
    options = Config.options(section)
    for option in options:
        try:
            dict1[option] = Config.get(section, option)
            if dict1[option] == -1:
                DebugPrint("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1


# set default vars
defconf = os.getenv("HOME") + "/.zbx.conf"
username = ""
password = ""
api = ""
noverify = ""

# Define commandline arguments
parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                 description='Creates new Zabbix hostgroups.', epilog="""
This program can use .ini style configuration files to retrieve the needed API connection information.
To use this type of storage, create a conf file (the default is $HOME/.zbx.conf) that contains at least the [Zabbix API] section and any of the other parameters:
       
 [Zabbix API]
 username=johndoe
 password=verysecretpassword
 api=https://zabbix.mycompany.com/path/to/zabbix/frontend/
 no_verify=true

""")
parser.add_argument('hostgroup', help='list of hostgroups to create', nargs='+')
parser.add_argument('-s', '--silent', help='Silently ignore already existing hostgroups', action='store_true')
parser.add_argument('-u', '--username', help='User for the Zabbix api')
parser.add_argument('-p', '--password', help='Password for the Zabbix api user')
parser.add_argument('-a', '--api', help='Zabbix API URL')
parser.add_argument('--no-verify', help='Disables certificate validation when using a secure connection',
                    action='store_true')
parser.add_argument('-c', '--config', help='Config file location (defaults to $HOME/.zbx.conf)')
args = parser.parse_args()

# load config module
Config = configparser.ConfigParser()

# if configuration argument is set, test the config file
if args.config:
    if os.path.isfile(args.config) and os.access(args.config, os.R_OK):
        Config.read(args.config)

# if not set, try default config file
else:
    if os.path.isfile(defconf) and os.access(defconf, os.R_OK):
        Config.read(defconf)

# try to load available settings from config file
try:
    username = config_section_map("Zabbix API")['username']
    password = config_section_map("Zabbix API")['password']
    api = config_section_map("Zabbix API")['api']
    noverify = bool(distutils.util.strtobool(config_section_map("Zabbix API")["no_verify"]))
except:
    pass

# override settings if they are provided as arguments
if args.username:
    username = args.username

if args.password:
    password = args.password

if args.api:
    api = args.api

if args.no_verify:
    noverify = args.no_verify

# test for needed params
if not username:
    print("Error: API User not set")
    exit()

if not password:
    print("Error: API Password not set")
    exit()

if not api:
    print("Error: API URL is not set")
    exit()

# Setup Zabbix API connection
zapi = ZabbixAPI(url=api, user=username, password=password)

if noverify is True:
    zapi.session.verify = False

# Login to the Zabbix API
print("Logging in on '" + api + "' with user '" + username + "'.")
# zapi.login(username, password)

##################################
# Start actual API logic
##################################

groups = []

# If we silently need to ignore the existing groups, we create a list of only the new groups
if args.silent:
    for group in args.hostgroup:
        test = zapi.hostgroup.exists(name=group)   #TODO This method is deprecated and will be removed in the future. Please use hostgroup.get instead.
        if test == False:
            groups.append(group)
# If not, we just pass the whole list as is
else:
    groups = args.hostgroup

# Create hostgroups one by one
for group in groups:
    zapi.hostgroup.create(name=group)

# And we're done...
