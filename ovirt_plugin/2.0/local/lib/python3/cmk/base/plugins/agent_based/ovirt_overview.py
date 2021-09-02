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


def ovirt_overview_parse(string_table):
    if string_table[0][0] != '@ovirt_version_info':
        raise ValueError('Version Header required')
    return json.loads(string_table[1][0])['api']


def ovirt_overview_host_label(section):
    yield HostLabel(u'cmk/ovirt_object', u'engine')


register.agent_section(
    name='ovirt_overview',
    parse_function=ovirt_overview_parse,
    host_label_function=ovirt_overview_host_label,
)


def discovery_ovirt_overview(section):
    yield Service()


def check_ovirt_overview(section):
    api = section
    try:
        yield Result(state=State.OK, summary=f"Ovirt Engine {api['product_info']['version']['full_version']}" )
    except KeyError:
        pass

    try:
        hosts = api['summary']['hosts']
        yield Result(state=State.OK, summary=f"{hosts.get('active', 0)} of {hosts.get('total', 0)} hosts active")
    except KeyError:
        pass

    try:
        storage_domains = api['summary']['storage_domains']
        yield Result(state=State.OK, summary=f"{storage_domains.get('active', 0)} of {storage_domains.get('total', 0)} storage domains active")
    except KeyError:
        pass

    try:
        vms = api['summary']['vms']
        yield Result(state=State.OK, summary=f"{vms.get('active', 0)} of {vms.get('total', 0)} vms active")
    except KeyError:
        pass

    try:
        if api['global_maintenance']:
            yield Result(state=State.CRITICAL, summary='Global maintenance active')
        else:
            yield Result(state=State.OK, summary='Global maintenance off')
    except KeyError:
        pass      

    yield Result(state=State.OK, notice='Ovirt Engine')


register.check_plugin(
    name='ovirt_overview',
    service_name='Ovirt Engine',
    discovery_function=discovery_ovirt_overview,
    check_function=check_ovirt_overview,
)
