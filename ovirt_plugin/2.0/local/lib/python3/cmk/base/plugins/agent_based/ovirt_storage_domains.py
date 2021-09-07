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

from cmk.base.plugins.agent_based.agent_based_api.v1.type_defs import (
    CheckResult,
    DiscoveryResult,
)

from cmk.base.plugins.agent_based.agent_based_api.v1 import (
    get_value_store,
    register,
    Result,
    Service,
    State,
)

from cmk.base.plugins.agent_based.utils import df


def ovirt_storage_domains_parse(string_table):
    if string_table[0][0] != '@ovirt_version_info':
        raise ValueError('Version Header required')
    return json.loads(string_table[1][0])['storage_domains']


register.agent_section(
    name='ovirt_storage_domains',
    parse_function=ovirt_storage_domains_parse,
)


def discovery_ovirt_storage_domains(section) -> DiscoveryResult:
    for domain in section:
        if domain.get("status", "") == "inactive":
            continue
        yield Service(item = f"{domain['name']} id {domain['id']}")


def check_ovirt_storage_domains(item, params, section) -> CheckResult:
    value_store = get_value_store()

    for domain in section:
        if f"{domain['name']} id {domain['id']}" != item:
            continue

        if domain["status"] == "inactive":
            yield Result(state=State.UNKOWN, summary="Storage Domain inactive")
            return

        mib = 1024.0**2
        committed_bytes = float(domain.get("committed", 0))
        available_bytes = float(domain.get("available", 0))
        size_bytes = available_bytes + float(domain.get("used", 0))

        if size_bytes is None or size_bytes == 0 or available_bytes is None:
            yield Result(state=State.UNKOWN, summary="Size of Storage Domain not available")
            return

        yield from df.df_check_filesystem_single(
            value_store,
            item,
            size_bytes / mib,
            available_bytes / mib,
            0,
            None,
            None,
            params=params
        )


register.check_plugin(
    name='ovirt_storage_domains',
    service_name='oVirt Storage Domain %s',
    discovery_function=discovery_ovirt_storage_domains,
    check_function=check_ovirt_storage_domains,
    check_ruleset_name="ovirt_storage_domains",
    check_default_parameters=df.FILESYSTEM_DEFAULT_LEVELS,
)
