#!/usr/bin/env python
# -*- encoding: utf-8; py-indent-offset: 4 -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

#
# Sesam Plugin
# (c) 2022 DECOIT GmbH
#

#
# This is free software;  you can redistribute it and/or modify it
# under the  terms of the  GNU General Public License  as published by
# the Free Software Foundation in version 2.  Sesam Plugin is  distributed
# in the hope that it will be useful, but WITHOUT ANY WARRANTY;  with-
# out even the implied warranty of  MERCHANTABILITY  or  FITNESS FOR A
# PARTICULAR PURPOSE. See the  GNU General Public License for more de-
# ails.  You should have  received  a copy of the  GNU  General Public
# License along with GNU Make; see the file  COPYING.  If  not,  write
# to the Free Software Foundation, Inc., 51 Franklin St,  Fifth Floor,
# Boston, MA 02110-1301 USA.

r"""Check_MK Agent Plugin: sesam_backup_state.py

This plugin is configured using an ini-style configuration file,
i.e. a file with lines of the form 'key: value'.
At 'agents/plugins/sesam_plugin.cfg' (relative to the check_mk
source code directory ) you should find some example configuration
files.
The requests library must be installed on the system executing the
plugin ("pip install requests").

This plugin it will be called by the agent without any arguments.
"""
import logging
import json
import os
import sys
import argparse
import functools
import time
import multiprocessing
from pprint import pprint
import ConfigParser as configparser

try:
    import requests
    from requests.packages.urllib3.exceptions import InsecureRequestWarning
except ImportError:
    sys.stdout.write("<<<sesam_plugin_info>>>\n"
                     "Error: sesam_backup_state requires the requests library."
                     " Please install it on the monitored system.\n")
    sys.exit(1)


requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

MK_CONFDIR = os.getenv("MK_CONFDIR") or "/etc/check_mk"
DEFAULT_CFG_FILE = os.path.join(MK_CONFDIR, "sesam_backup_state.cfg")

DEFAULT_CFG_SECTION = {
    "username": "monitoring",
    "password": "",
    "sesam_url": "https://localhost:11401",
}

LOGGER = logging.getLogger(__name__)

VERSION = "1.0.0"

DEBUG = False


def parse_arguments(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    prog, descr, epilog = __doc__.split('\n\n')
    parser = argparse.ArgumentParser(
        prog=prog, description=descr, epilog=epilog)
    parser.add_argument("--debug",
                        action="store_true",
                        help='''Debug mode: raise Python exceptions''')
    parser.add_argument("-v",
                        "--verbose",
                        action="count",
                        default=0,
                        help='''Verbose mode (for even more output use -vvv)''')
    parser.add_argument("-c",
                        "--config-file",
                        default=DEFAULT_CFG_FILE,
                        help='''Read config file (default: $MK_CONFDIR/sesam_plugin.cfg)''')

    args = parser.parse_args(argv)

    fmt = "%%(levelname)5s: %s%%(message)s"
    if args.verbose == 0:
        LOGGER.disabled = True
    elif args.verbose == 1:
        logging.basicConfig(level=logging.INFO, format=fmt % "")
    else:
        logging.basicConfig(level=logging.DEBUG, format=fmt %
                            "(line %(lineno)3d) ")
    if args.verbose < 3:
        logging.getLogger('urllib3').setLevel(logging.WARNING)

    LOGGER.debug("parsed args: %r", args)
    return args


def get_config(cfg_file):
    config = configparser.ConfigParser(DEFAULT_CFG_SECTION)
    LOGGER.debug("trying to read %r", cfg_file)
    files_read = config.read(cfg_file)
    LOGGER.info("read configration file(s): %r", files_read)
    section_name = "SESAM" if config.sections() else "DEFAULT"
    conf_dict = dict(config.items(section_name))

    return conf_dict


class Section(list):
    '''a very basic agent section class'''
    _OUTPUT_LOCK = multiprocessing.Lock()

    version_info = {
        'PluginVersion': VERSION
    }

    # Should we need to parallelize one day, change this to be
    # more like the Section class in agent_azure, for instance
    def __init__(self, name=None, separator=0, piggytarget=None):
        super(Section, self).__init__()
        self.sep = chr(separator)
        if piggytarget is not None:
            self.append('<<<<%s>>>>' % piggytarget)
        if name is not None:
            self.append('<<<sesam_%s:sep(%d)>>>' % (name, separator))
            version_json = json.dumps(Section.version_info)
            self.append(self.sep.join(('@sesam_version_info', version_json)))

    def write(self):
        if self[0].startswith('<<<<'):
            self.append('<<<<>>>>')
        with self._OUTPUT_LOCK:
            for line in self:
                sys.stdout.write("%s\n" % line)
            sys.stdout.flush()


class MKSesamClient:

    def __init__(self, config):
        self.sesam_url = config["sesam_url"]
        self._auth = (config["username"], config["password"])
        self._certfile = None

    def get_data(self, url):
        r = requests.get(self.sesam_url + "/sep/api/v2/" + url,
                         auth=self._auth, verify=self._certfile if self._certfile else False)
        return r.json()


def time_it(func):
    '''Decorator to time the function'''
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        before = time.time()
        try:
            return func(*args, **kwargs)
        finally:
            LOGGER.info("%r took %ss", func.func_name, time.time() - before)

    return wrapped


COMPATIBILITY_RESULT = {}


def write_section_compatibility():
    section = Section('compatibility')
    section.append(json.dumps(COMPATIBILITY_RESULT))
    section.write()


GLOBAL_BACKUPGROUPS = []


def get_backupgroups(client):
    global GLOBAL_BACKUPGROUPS
    if not GLOBAL_BACKUPGROUPS:
        GLOBAL_BACKUPGROUPS = client.get_data("backupgroups")
    return GLOBAL_BACKUPGROUPS


def section_backup_state(client):
    backupgroups = get_backupgroups(client)
    section = Section('backup_state')
    result = []
    for group in backupgroups:
        group["tasks"] = client.get_data("backupgroups/%s/tasks" % group["name"])
        result.append(group)
    section.append(json.dumps(result))
    section.write()


# .
#   .--Main----------------------------------------------------------------.
#   |                        __  __       _                                |
#   |                       |  \/  | __ _(_)_ __                           |
#   |                       | |\/| |/ _` | | '_ \                          |
#   |                       | |  | | (_| | | | | |                         |
#   |                       |_|  |_|\__,_|_|_| |_|                         |
#   |                                                                      |
#   +----------------------------------------------------------------------+
#   |                                                                      |
#   '----------------------------------------------------------------------'


def str2bool(v):
    return v is not None and v.lower() in ("yes", "true", "t", "1")


def report_exception_to_server(exc, location):
    LOGGER.info("handling exception: %s", exc)
    msg = "Plugin exception in %s: %s" % (location, exc)
    sec = Section('overview')
    sec.append(json.dumps({"Unknown": msg}))
    sec.write()


def main():

    args = parse_arguments()
    config = get_config(args.config_file)

    if not config["sesam_url"]:
        report_exception_to_server("Config could not be read", "main")
        sys.exit(1)

    try:  # first calls by docker-daemon: report failure
        client = MKSesamClient(config)
    except () if DEBUG else Exception as exc:
        report_exception_to_server(exc, "main")
        sys.exit(1)

    try:
        section_backup_state(client)
    except () if DEBUG else Exception as exc:
        report_exception_to_server(exc, "get data")
        sys.exit(1)


if __name__ == "__main__":
    main()
