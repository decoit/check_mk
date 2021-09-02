#!/usr/bin/env python
# -*- encoding: utf-8; py-indent-offset: 4 -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

#
# Ovirt Plugin
# (c) 2021 DECOIT GmbH
#

#
# This is free software;  you can redistribute it and/or modify it
# under the  terms of the  GNU General Public License  as published by
# the Free Software Foundation in version 2.  Ovirt Plugin is  distributed
# in the hope that it will be useful, but WITHOUT ANY WARRANTY;  with-
# out even the implied warranty of  MERCHANTABILITY  or  FITNESS FOR A
# PARTICULAR PURPOSE. See the  GNU General Public License for more de-
# ails.  You should have  received  a copy of the  GNU  General Public
# License along with GNU Make; see the file  COPYING.  If  not,  write
# to the Free Software Foundation, Inc., 51 Franklin St,  Fifth Floor,
# Boston, MA 02110-1301 USA.

r"""Check_MK Agent Plugin: ovirt_plugin_2.py

This plugin is configured using an ini-style configuration file,
i.e. a file with lines of the form 'key: value'.
At 'agents/plugins/ovirt_plugin.cfg' (relative to the check_mk
source code directory ) you should find some example configuration
files.
The requests library must be installed on the system executing the
plugin ("pip install requests").

This plugin it will be called by the agent without any arguments.
"""
import logging
import json
import os
import socket
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
    sys.stdout.write("<<<ovirt_plugin_info>>>\n"
                     "Error: ovirt_plugin requires the requests library."
                     " Please install it on the monitored system.\n")
    sys.exit(1)


requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

MK_CONFDIR = os.getenv("MK_CONFDIR") or "/etc/check_mk"
DEFAULT_CFG_FILE = os.path.join(MK_CONFDIR, "ovirt_plugin.cfg")

DEFAULT_CFG_SECTION = {
    "username": "admin@internal",
    "password": "",
    "engine_fqdn": "",
    "engine_url": "",
    "certfile": "",
    "generate_piggyback": "true"
}

LOGGER = logging.getLogger(__name__)

VERSION = "1.0.6"

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
                        help='''Read config file (default: $MK_CONFDIR/ovirt_plugin.cfg)''')

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
    section_name = "OVIRT" if config.sections() else "DEFAULT"
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
            self.append('<<<ovirt_%s:sep(%d)>>>' % (name, separator))
            version_json = json.dumps(Section.version_info)
            self.append(self.sep.join(('@ovirt_version_info', version_json)))

    def write(self):
        if self[0].startswith('<<<<'):
            self.append('<<<<>>>>')
        with self._OUTPUT_LOCK:
            for line in self:
                sys.stdout.write("%s\n" % line)
            sys.stdout.flush()


class MKOvirtClient:

    HEADERS = {'Accept': 'application/json', 'Version': '4'}

    def __init__(self, config):
        # type: (dict)
        self._engine_url = config["engine_url"]
        self._auth = (config["username"], config["password"])
        self._engine_fqdn = config["engine_fqdn"]
        self._certfile = config["certfile"]

    def get_data(self, url):
        r = requests.get(self._engine_url+url,
                         auth=self._auth, verify=self._certfile if self._certfile else False, headers=self.HEADERS)
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


GLOBAL_HOSTS = []


def get_hosts(client):
    # type: (MKOvirtClient)
    global GLOBAL_HOSTS
    if not GLOBAL_HOSTS:
        GLOBAL_HOSTS = client.get_data("/api/hosts?all_content=true")
    return GLOBAL_HOSTS


def section_overview(client, generate_piggyback = True):
    # type: (MKOvirtClient, bool)
    api = client.get_data("/api")
    result = {}
    for key in ["product_info", "summary"]:
        if api and key in api:
            result.setdefault("api", {})[key] = api[key]
    if api and "product_info" in api:
        COMPATIBILITY_RESULT["engine"] = api["product_info"]
    # Global Maintainance only found in hosts
    result["global_maintenance"] = False
    hosts = get_hosts(client)
    if hosts and "host" in hosts:
        for host in hosts["host"]:
            if "hosted_engine" in host and host["hosted_engine"] and "global_maintenance" in host["hosted_engine"] and host["hosted_engine"]["global_maintenance"] == "true":
                result["global_maintenance"] = True
                break

    section = Section('overview')
    section.append(json.dumps(result))
    section.write()


def section_hosts(client, generate_piggyback = True):
    # type: (MKOvirtClient, bool)
    if not generate_piggyback:
        return
    hosts = get_hosts(client)
    if not hosts or not "host" in hosts:
        return
    for host in hosts["host"]:
        host_obj = {}
        for key in ["version", "status", "summary", "type", "name", "libvirt_version", "hosted_engine"]:
            if host and key in host:
                host_obj[key] = host[key]
        section = Section('hosts', piggytarget=host_obj["name"])
        section.append(json.dumps(host_obj))
        section.write()

def read_data_centers(client, generate_piggyback = True):
    # type: (MKOvirtClient, bool)
    datacenters = client.get_data("/api/datacenters?follow=storage_domains")
    data_center_result = {}
    storage_domain_result = {}
    if not datacenters or not "data_center" in datacenters:
        return
    for datacenter in datacenters["data_center"]:
        if not datacenter:
            continue
        datacenter_obj = {}
        for key in ["id", "version", "status", "description", "name", "supported_versions"]:
            if key in datacenter:
                datacenter_obj[key] = datacenter[key]
        data_center_result.setdefault("datacenters", []).append(datacenter_obj)
        for storage_domain in datacenter.get("storage_domains", {}).get("storage_domain", []):
            if not storage_domain:
                continue
            storage_domain_obj = {}
            storage_domain_obj.setdefault("data_center", {})["name"] = datacenter["name"]
            storage_domain_obj.setdefault("data_center", {})["id"] = datacenter["id"]
            for key in ["status", "name", "id", "external_status", "description", "committed", "available", "used", "warning_low_space_indicator"]:
                if key in storage_domain:
                    storage_domain_obj[key] = storage_domain[key]
            storage_domain_result.setdefault("storage_domains", []).append(storage_domain_obj)

    COMPATIBILITY_RESULT["datacenters"] = data_center_result.get("datacenters", [])

    section = Section('datacenters')
    section.append(json.dumps(data_center_result))
    section.write()
    section = Section('storage_domains')
    section.append(json.dumps(storage_domain_result))
    section.write()


def read_clusters(client, generate_piggyback = True):
    # type: (MKOvirtClient, bool)
    clusters = client.get_data("/api/clusters")
    cluster_result = {}

    if not clusters or not "cluster" in clusters:
        return
    for cluster in clusters["cluster"]:
        if not cluster:
            continue
        cluster_obj = {}
        for key in ["id", "version", "description", "name"]:
            if key in cluster:
                cluster_obj[key] = cluster[key]
        cluster_obj.setdefault("data_center", {})["id"] = cluster.get(
            "data_center", {}).get("id", None)
        cluster_result.setdefault("cluster", []).append(cluster_obj)

    COMPATIBILITY_RESULT["cluster"] = cluster_result.get("cluster", [])

    section = Section('clusters')
    section.append(json.dumps(cluster_result))
    section.write()


def section_vms_stats(client, generate_piggyback = True):
    # type: (MKOvirtClient, bool)
    if not generate_piggyback:
        return

    vms = client.get_data("/api/vms?follow=statistics")
    if not vms or not "vm" in vms:
        return
    for vm in vms['vm']:
        vm_obj = {}

        for key in ["name", "type"]:
            if vm and key in vm:
                vm_obj[key] = vm[key]

        if "statistics" in vm and "statistic" in vm["statistics"]:
            for stat in vm["statistics"]["statistic"]:
                if stat["name"] not in ["network.current.total", "cpu.current.total", "cpu.current.hypervisor", "cpu.current.guest", "memory.installed"]:
                    continue
                stat_obj = {k: v for k, v in stat.items() if k in [
                    "name", "type", "unit", "description"]}
                for _, value in stat["values"]["value"][0].items():
                    stat_obj["value"] = str(value)
                vm_obj.setdefault("statistics", []).append(stat_obj)
        section = Section('vmstats', piggytarget=vm_obj["name"])
        section.append(json.dumps(vm_obj))
        section.write()


def section_vms_snapshots(client, generate_piggyback = True):
    # type: (MKOvirtClient, bool)
    vms = client.get_data("/api/vms?follow=snapshots")
    if not vms or not "vm" in vms:
        return
    section = Section('snapshots_engine')
    for vm in vms['vm']:
        vm_obj = {}

        for key in ["name", "type"]:
            if vm and key in vm:
                vm_obj[key] = vm[key]

        if "snapshots" in vm and "snapshot" in vm["snapshots"]:
            for snap in vm["snapshots"]["snapshot"]:
                vm_obj.setdefault("snapshots", []).append({k: v for k, v in snap.items() if k in [
                    "snapshot_status", "snapshot_type", "description", "date", "id"]})

        section.append(json.dumps(vm_obj))
        if generate_piggyback:
            piggy_section = Section('snapshots', piggytarget=vm_obj["name"])
            piggy_section.append(json.dumps(vm_obj))
            piggy_section.write()

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
    # type: (str)
    return v is not None and v.lower() in ("yes", "true", "t", "1")


def report_exception_to_server(exc, location):
    LOGGER.info("handling exception: %s", exc)
    msg = "Plugin exception in %s: %s" % (location, exc)
    sec = Section('overview')
    sec.append(json.dumps({"Unknown": msg}))
    sec.write()


def main():

    args = parse_arguments()
    config = get_config(args.config_file)  # type: dict

    if not config["engine_url"]:
        report_exception_to_server("Config could not be read", "main")
        sys.exit(1)

    try:  # first calls by docker-daemon: report failure
        client = MKOvirtClient(config)
    except () if DEBUG else Exception as exc:
        report_exception_to_server(exc, "main")
        sys.exit(1)

    _generate_piggyback = str2bool(config["generate_piggyback"])

    try:
        section_overview(client, generate_piggyback=_generate_piggyback)
        read_data_centers(client, generate_piggyback=_generate_piggyback)
        read_clusters(client, generate_piggyback=_generate_piggyback)
        section_hosts(client, generate_piggyback=_generate_piggyback)
        section_vms_stats(client, generate_piggyback=_generate_piggyback)
        section_vms_snapshots(client, generate_piggyback=_generate_piggyback)
        write_section_compatibility()
    except () if DEBUG else Exception as exc:
        report_exception_to_server(exc, "get data")
        sys.exit(1)


if __name__ == "__main__":
    main()
