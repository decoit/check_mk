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

def ovirt_vmstats_parse(string_table):
    if string_table[0][0] != '@ovirt_version_info':
        raise ValueError("Version Header required")
    vm = json.loads(string_table[1][0])
    section = {}

    try:
        for stat in vm["statistics"]:
            section[stat["description"]] = stat
    except KeyError:
        pass
    return section


register.agent_section(
    name="ovirt_vmstats",
    parse_function=ovirt_vmstats_parse,
)


def discovery_ovirt_vmstats(section):
    for item in section:
        yield Service(item=item)


def check_ovirt_vmstats(item, section):
    data = section[item]
    yield Result(state=State.OK, summary="%s %s" % (data["value"], data["unit"]))
    yield Metric(data["name"], float(data["value"]))


register.check_plugin(
    name="ovirt_vmstats",
    service_name="Ovirt %s",
    discovery_function=discovery_ovirt_vmstats,
    check_function=check_ovirt_vmstats,
)
