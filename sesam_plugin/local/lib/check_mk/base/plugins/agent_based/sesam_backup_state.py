#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-

#
# (c) 2022 DECOIT GmbH
#          Timo Klecker <klecker@decoit.de>
# License: GNU General Public License v2
#

import json
from typing import (
    Dict,
    Any,
)
from cmk.base.api.agent_based.checking_classes import CheckResult, DiscoveryResult, Result, Service, State
from cmk.base.plugins.agent_based.agent_based_api.v1.type_defs import (
    StringTable,
)
from cmk.base.plugins.agent_based.agent_based_api.v1 import (
    register,
)


def parse_sesam_backup_state(string_table: StringTable):
    if string_table[0][0] != '@sesam_version_info':
        raise ValueError('Version Header required')
    group_list = json.loads(string_table[1][0])
    return {group["name"]: group for group in group_list}


register.agent_section(
    name="sesam_backup_state",
    parse_function=parse_sesam_backup_state,
)

# the discovery function


def discovery_sesam_backup_state(section: Dict[str, Dict[str, Any]]) -> DiscoveryResult:
    for group in section:
        yield Service(item=group)


def check_results_sts(value: Dict, key = None) -> CheckResult:
    if "resultsSts" not in value:
        return Result(state=State.UNKNOWN, notice="%s: Unknown last Execution Result" % key)
    results_sts = value["resultsSts"]

    if results_sts in ["ERROR", "2"]:
        return Result(state=State.CRIT, notice="%s: %s" % (key, results_sts))
    if results_sts in ["INFO"]:
        return Result(state=State.WARN, notice="%s: %s" % (key, results_sts))
    return Result(state=State.OK, notice="%s: %s" % (key, results_sts))


# the check function
def check_sesam_backup_state(item, section: Dict[str, Dict[str, Any]]) -> CheckResult:
    if item in section:
        group = section[item]
        yield check_results_sts(group, "Total State")
        if "tasks" in group and group["tasks"]:
            tasks = {task["name"]: task for task in group["tasks"]}
            for task_name in sorted(tasks):
                task = tasks[task_name]
                yield check_results_sts(task, key=task_name)


register.check_plugin(
    name="sesam_backup_state",
    service_name='Sesam Backup Group %s',
    check_function=check_sesam_backup_state,
    discovery_function=discovery_sesam_backup_state,
)
