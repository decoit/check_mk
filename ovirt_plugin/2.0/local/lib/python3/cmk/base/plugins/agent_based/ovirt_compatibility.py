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


def ovirt_compatibility_parse(string_table):
    if string_table[0][0] != '@ovirt_version_info':
        raise ValueError('Version Header required')
    return json.loads(string_table[1][0])


register.agent_section(
    name='ovirt_compatibility',
    parse_function=ovirt_compatibility_parse,
)


def discovery_ovirt_compatibility(section):
    yield Service()


def _ovirt_version_to_string(version_a: Dict) -> str:
    try:
        return "%s.%s" % (version_a["major"], version_a["minor"])
    except ValueError:
        return "Unknown"


def _ovirt_same_version(version_a: Dict, version_b: Dict) -> bool:
    try:
        return version_a["major"] == version_b["major"] and version_a["minor"] == version_b["minor"]
    except ValueError:
        return False


def _ovirt_version_greater_or_equal(version_a: Dict, version_b: Dict) -> bool:
    try:
        return (version_a["major"] == version_b["major"] and version_a["minor"] >= version_b["minor"]) or (version_a["major"] > version_b["major"])
    except ValueError:
        return False


def check_ovirt_compatibility(section):
    data = section

    data_center_dict = {d["id"]: d for d in data.get("datacenters", [])}
    clusters = data.get("cluster", [])

    engine = data.get("engine", {})
    engine_version = engine.get("version", {})

    yield Result(state=State.OK, summary=f"Checked {len(data_center_dict.keys())} datacenters and {len(clusters)} clusters")

    for cluster in clusters:
        if not "data_center" in cluster or "id" not in cluster["data_center"]:
            continue

        dc = data_center_dict.get(cluster["data_center"]["id"])
        if not dc:
            yield Result(state=State.UNKNOWN, summary=f"Could not find data center {cluster['data_center']['id']} in plugin output")
            continue

        cluster_version = cluster.get("version", {})

        if engine_version and cluster_version and not _ovirt_version_greater_or_equal(cluster_version, engine_version):
            yield Result(
                state=State.WARN,
                summary="Cluster %s version (%s) is lower then engine (%s)!" % (
                    cluster["name"],
                    _ovirt_version_to_string(cluster_version),
                    _ovirt_version_to_string(engine_version)
                )
            )

        if not any(
            _ovirt_same_version(cluster_version, data_center_compat_version)
            for data_center_compat_version in dc.get("supported_versions", {}).get("version", [])
        ):
            yield Result(
                state=State.WARN,
                summary="Cluster %s version (%s) not compatible to DataCenter!" % (
                    cluster["name"],
                    _ovirt_version_to_string(cluster_version)
                )
            )

    yield Result(state=State.OK, notice='Ovirt Engine')


register.check_plugin(
    name='ovirt_compatibility',
    service_name='oVirt Storage Compatibility',
    discovery_function=discovery_ovirt_compatibility,
    check_function=check_ovirt_compatibility,
)
