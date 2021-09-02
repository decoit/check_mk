#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

#
# Based on work by
# Writed by Allan GooD: allan.cassaro@gmail.com
# https://github.com/allangood/check_mk/tree/master/plugins/puppet
#

#
# mk_puppet Plugin
# (c) 2021 DECOIT GmbH
# written by Timo Klecker: klecker@decoit.de
#

#
# This is free software;  you can redistribute it and/or modify it
# under the  terms of the  GNU General Public License  as published by
# the Free Software Foundation in version 2.  mk_puppet Plugin is  distributed
# in the hope that it will be useful, but WITHOUT ANY WARRANTY;  with-
# out even the implied warranty of  MERCHANTABILITY  or  FITNESS FOR A
# PARTICULAR PURPOSE. See the  GNU General Public License for more de-
# ails.  You should have  received  a copy of the  GNU  General Public
# License along with GNU Make; see the file  COPYING.  If  not,  write
# to the Free Software Foundation, Inc., 51 Franklin St,  Fifth Floor,
# Boston, MA 02110-1301 USA.
#


'''
Example of output:
<<<puppet_agent>>>
last_run: 1439475966
resources_resources:
resources_changed: 3
resources_failed: 0
resources_failed_to_restart: 0
resources_out_of_sync: 3
resources_restarted: 0
resources_scheduled: 0
resources_skipped: 0
resources_total: 77
events_events:
events_failure: 0
events_success: 3
events_total: 3
'''

from cmk.gui.i18n import _

from typing import Dict, List, Tuple

import time

from cmk.base.plugins.agent_based.agent_based_api.v1 import (
    register,
    Result,
    Service,
    State,
    check_levels,
    render,
)


def puppet_agent_parse(string_table: List[List[str]]) -> Dict[str, str]:
    section: Dict[str, str] = dict()
    for items in string_table:
        # get rid of the colon
        section[items[0][:-1]] = items[1] if len(items) > 1 else ""
    return section


register.agent_section(
    name='puppet_agent',
    parse_function=puppet_agent_parse,
)


def discovery_puppet_agent_events(section: Dict[str, str]):
    if "events_failure" in section:
        yield Service()

def check_puppet_agent_events(params: Dict[str, Tuple[int, int]], section: Dict[str, str]):
    if "events_failure" not in section:
        yield Result(state=State.UNKNOWN, summary=_("Item not found in agent output"))
        return
    
    yield from check_levels(
        int(section.get("events_failure", "0")),
        levels_upper=params["levels"],
        metric_name="puppet_agent_failure",
        boundaries=params["levels"],
        render_func=lambda x: str(int(x)),
        label=_("Events Failure"),
    )


register.check_plugin(
    name='puppet_agent_events',
    service_name=_('Puppet Agent Events Failure'),
    discovery_function=discovery_puppet_agent_events,
    check_function=check_puppet_agent_events,
    sections=["puppet_agent"],
    check_ruleset_name="puppet_agent_events",
    check_default_parameters={"levels": (2, 5)},
)


def discovery_puppet_agent_lastrun(section: Dict[str, str]):
    if "last_run" in section:
        yield Service()

def check_puppet_agent_lastrun(params: Dict[str, Tuple[int, int]], section: Dict[str, str]):
    if "last_run" not in section:
        yield Result(state=State.UNKNOWN, summary=_("Item not found in agent output"))
        return
    
    now = time.time()
    diff_seconds: float = now - int(section.get("last_run", "0"))
    yield from check_levels(
        diff_seconds,
        levels_upper=params["levels"],
        metric_name="puppet_agent_lastrun",
        boundaries=params["levels"],
        render_func=lambda seconds: f"{render.timespan(seconds)} ago",
        label=_("Last Execution"),
    )


register.check_plugin(
    name='puppet_agent_lastrun',
    service_name=_('Puppet Agent Last Run'),
    discovery_function=discovery_puppet_agent_lastrun,
    check_function=check_puppet_agent_lastrun,
    sections=["puppet_agent"],
    check_ruleset_name="puppet_agent_lastrun",
    check_default_parameters={"levels": (86400, 604800)},
)


# Has to have uniqe keys and values!
_resources_name_table: Dict[str,str] = {
       'resources_changed': _('Resource Changed'),
       'resources_failed': _('Resource Failed'),
       'resources_failed_to_restart': _('Resource Failed to Restart'),
       'resources_out_of_sync': _('Resources Out Of Sync'),
       'resources_restarted': _('Resources Restarted'),
       'resources_scheduled': _('Resources Scheduled'),
       'resources_skipped': _('Resources Skipped'),
       'resources_total': _('Resources Total'),
}

def discovery_puppet_agent_resources(section: Dict[str,str]):
    for key,value in _resources_name_table.items():
        if key in section:
            yield Service(item = value)

def check_puppet_agent_resources(item: str, section: Dict[str, str]):
    item_key = list(_resources_name_table.keys())[list(_resources_name_table.values()).index(item)]
    if item_key not in section:
        yield Result(state=State.UNKNOWN, summary=_("Item not found in agent output"))
        return
    
    yield Result(state=State.OK, summary=f"{item}: {section.get(item_key, '0')}")

register.check_plugin(
    name='puppet_agent_resources',
    service_name=_('Puppet Agent %s'),
    discovery_function=discovery_puppet_agent_resources,
    check_function=check_puppet_agent_resources,
    sections=["puppet_agent"],
)

