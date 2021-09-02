#!/usr/bin/env python3
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

import json
from typing import Dict, List
from cmk.base.plugins.agent_based.agent_based_api.v1 import (
    Metric,
    register,
    Result,
    Service,
    State,
    HostLabel,
    regex,
)


def ovirt_hosts_parse(string_table):
    if string_table[0][0] != '@ovirt_version_info':
        raise ValueError("Version Header required")
    return json.loads(string_table[1][0])


register.agent_section(
    name="ovirt_hosts",
    parse_function=ovirt_hosts_parse,
)


def discovery_ovirt_hosts(section):
    yield Service()


def check_ovirt_hosts(section):
    api = section
    try:
        yield Result(state=State.OK, summary=f"Status: {api['status']}")
    except KeyError:
        pass
    try:
        yield Result(state=State.OK, summary=f"Type: {api['type']}")
    except KeyError:
        pass
    try:
        yield Result(state=State.OK, summary=f"Version: {api['version']['full_version']}")
    except KeyError:
        pass

    try:
        if api["hosted_engine"]["local_maintenance"] == "true":
            yield Result(state=State.WARN, summary='Local maintenance active')
        else:
            yield Result(state=State.OK, summary='Local maintenance off')
    except KeyError:
        pass      

    yield Result(state=State.OK, notice='Ovirt Host')


register.check_plugin(
    name="ovirt_hosts",
    service_name="Ovirt Host",
    discovery_function=discovery_ovirt_hosts,
    check_function=check_ovirt_hosts,
)
