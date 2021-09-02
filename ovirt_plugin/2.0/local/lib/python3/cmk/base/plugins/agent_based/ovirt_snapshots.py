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


def ovirt_snapshots_parse(string_table):
    if string_table[0][0] != '@ovirt_version_info':
        raise ValueError("Version Header required")
    return json.loads(string_table[1][0]).get("snapshots", [])


register.agent_section(
    name="ovirt_snapshots",
    parse_function=ovirt_snapshots_parse,
)


def discovery_ovirt_snapshots(section):
    yield Service()


def check_ovirt_snapshots(params, section):
    if not section:
        yield Result(state=State.OK, summary="No Snapshots found.")
        return

    ignore = []
    try:
        ignore.extend([regex(item) for item in params["ignore"]])
    except KeyError:
        pass
    
    allow = []
    try:
        allow.extend([regex(item) for item in params["allow"]])
    except KeyError:
        pass

    if bool(allow) != bool(ignore):  # XOR (Only one of both lists has elements)
        # If only allow has elements, then ignore everything else
        if not ignore:
            ignore.append(regex('.*'))

    result = ''
    found = False
    for snapshot in section:
        if "description" in snapshot \
            and any( skip.match(snapshot["description"]) for skip in ignore) \
            and not any( take.match(snapshot["description"]) for take in allow ):
            continue
        if "snapshot_type" in snapshot and snapshot["snapshot_type"] == "active":
            continue
        found = True
        result += ", " + snapshot["description"]

    if found:
        yield Result(state=State(params.get("state", 1)), summary=f"Found Snapshots: {result[2:]}")
    else:
        yield Result(state=State.OK, summary="No Snapshots found")


register.check_plugin(
    name="ovirt_snapshots",
    service_name="Ovirt Snapshots",
    discovery_function=discovery_ovirt_snapshots,
    check_function=check_ovirt_snapshots,
    check_default_parameters={},
    check_ruleset_name="ovirt_snapshots",
)
