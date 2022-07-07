#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-

#
# (c) 2022 DECOIT GmbH
#          Timo Klecker <klecker@decoit.de>
# License: GNU General Public License v2
#

import pprint
import math
from typing import (
    Dict,
    List,
    Set,
)
from cmk.base.api.agent_based.checking_classes import CheckResult, DiscoveryResult, Result, Service, State
from cmk.base.plugins.agent_based.agent_based_api.v1.type_defs import (
    StringTable,
)
from cmk.base.plugins.agent_based.agent_based_api.v1 import (
    any_of,
    all_of,
    exists,
    contains,
    register,
    check_levels,
    render,
    OIDEnd,
    Result,
    Service,
    SNMPTree,
    State,
    OIDEnd
)


def parse_alarm_level(level: str, divisor: float = 1000.0) -> float:
    if not level:
        return None
    if level == "0":
        return None
    return float(level) / divisor


def parse_value(value: str, divisor: float = 1000.0) -> float:
    return float(value) / divisor


def _pad_interface_names(interfaces: List[str]) -> Dict[str, str]:
    interface_index_padded = {}
    max_index = max(int(interface[0]) for interface in interfaces)
    digits = len(str(max_index))
    for interface in interfaces:
        interface_index_padded[interface[0]] = ("%0" + str(digits) + "d") % int(interface[0])
    return interface_index_padded


def _dbm_to_uw(dbm):
    if dbm == "-99999999":
        return 0
    return pow(10, (float(dbm) - 30.0) / 10.0) * 1000000.0


def _uw_to_dbm(uw):
    return 10 * math.log10(uw / 1000000.0) + 30


def parse_hp_icf_xcvr_table(string_table):
    # pprint.pprint(string_table)
    interface_index_padded = _pad_interface_names(string_table[0])

    result = {}
    for line in string_table[1]:
        # The value of this object is valid when the value of the hpicfXcvrDiagnostics object is dom(1).
        if line[2] != "1":
            continue

        item = interface_index_padded[line[0]]
        values = {}
        values["Temperature"] = (
            parse_value(line[3]),
            (parse_alarm_level(line[11]), parse_alarm_level(line[9])),
            (parse_alarm_level(line[10]), parse_alarm_level(line[8])),
            lambda v: "%.2f °C" % v)
        values["SupplyVoltage"] = (
            parse_value(line[4], divisor=10000),
            (parse_alarm_level(line[15], divisor=10000), parse_alarm_level(line[13], divisor=10000)),
            (parse_alarm_level(line[14], divisor=10000), parse_alarm_level(line[12], divisor=10000)),
            lambda v: "%.3f V" % v)
        values["TxBiasCurrent"] = (
            parse_value(line[5]),
            (parse_alarm_level(line[19]), parse_alarm_level(line[17])),
            (parse_alarm_level(line[18]), parse_alarm_level(line[16])),
            lambda v: "%.3f mA" % v)
        values["TxOutputPower"] = (
            _dbm_to_uw(parse_value(line[6])),
            (parse_alarm_level(line[23], divisor=10.0), parse_alarm_level(line[21], divisor=10.0)),
            (parse_alarm_level(line[22], divisor=10.0), parse_alarm_level(line[20], divisor=10.0)),
            lambda v: "%.3f µW (%.3f dBm)" % (v, _uw_to_dbm(v)))
        values["RxOpticalPower"] = (
            _dbm_to_uw(parse_value(line[7])),
            (parse_alarm_level(line[27], divisor=10.0), parse_alarm_level(line[25], divisor=10.0)),
            (parse_alarm_level(line[26], divisor=10.0), parse_alarm_level(line[24], divisor=10.0)),
            lambda v: "%.3f µW (%.3f dBm)" % (v, _uw_to_dbm(v)))
        result[item] = values
    pprint.pprint(result)
    return result


register.snmp_section(
    name="hp_icf_xcvr_table",
    detect=all_of(
        contains(".1.3.6.1.2.1.1.1.0", "hp"),
        exists(".1.3.6.1.4.1.11.2.14.11.5.1.82.1.1.1.1.9.*"),
    ),
    parse_function=parse_hp_icf_xcvr_table,
    parsed_section_name="hp_icf_xcvr_table",
    fetch=[
        SNMPTree(
            base=".1.3.6.1.2.1.2.2.1",
            oids=[
                OIDEnd(),
                '1'
            ]
        ),
        SNMPTree(
            base=".1.3.6.1.4.1.11.2.14.11.5.1.82.1.1.1.1",
            oids=[
                '1',  # hpicfXcvrPortIndex
                '3',  # hpicfXcvrModel
                '9',  # hpicfXcvrDiagnostics
                '11',  # hpicfXcvrTemp
                '12',  # hpicfXcvrVoltage
                '13',  # hpicfXcvrBias
                '14',  # hpicfXcvrTxPower
                '15',  # hpicfXcvrRxPower
                '18',  # hpicfXcvrTempHiAlarm
                '19',  # hpicfXcvrTempLoAlarm
                '20',  # hpicfXcvrTempHiWarn
                '21',  # hpicfXcvrTempLoWarn
                '22',  # hpicfXcvrVccHiAlarm
                '23',  # hpicfXcvrVccLoAlarm
                '24',  # hpicfXcvrVccHiWarn
                '25',  # hpicfXcvrVccLoWarn
                '26',  # hpicfXcvrBiasHiAlarm
                '27',  # hpicfXcvrBiasLoAlarm
                '28',  # hpicfXcvrBiasHiWarn
                '29',  # hpicfXcvrBiasLoWarn
                '30',  # hpicfXcvrPwrOutHiAlarm
                '31',  # hpicfXcvrPwrOutLoAlarm
                '32',  # hpicfXcvrPwrOutHiWarn
                '33',  # hpicfXcvrPwrOutLoWarn
                '34',  # hpicfXcvrRcvPwrHiAlarm
                '35',  # hpicfXcvrRcvPwrLoAlarm
                '36',  # hpicfXcvrRcvPwrHiWarn
                '37',  # hpicfXcvrRcvPwrLoWarn
            ]
        ),
    ],
)


def discovery_hp_icf_xcvr_table(section):
    for item, _ in section.items():
        yield Service(item=item)


def check_hp_icf_xcvr_table(item, section):
    if item in section:
        data = section[item]
        for key in sorted(data):
            value, levels_lower, levels_upper, render_func = data[key]
            yield from check_levels(value=value, levels_upper=levels_upper, levels_lower=levels_lower, metric_name=key, render_func=render_func, label=key)
            if levels_lower:
                lower_warn = "never" if levels_lower[0] is None else render_func(levels_lower[0])
                lower_crit = "never" if levels_lower[1] is None else render_func(levels_lower[1])
                yield Result(state=State.OK, notice=f"{key}: (warn/crit below %s/%s)" % (lower_warn, lower_crit))
            if levels_upper:
                upper_warn = "never" if levels_upper[0] is None else render_func(levels_upper[0])
                upper_crit = "never" if levels_upper[1] is None else render_func(levels_upper[1])
                yield Result(state=State.OK, notice=f"{key}: (warn/crit at %s/%s)" % (upper_warn, upper_crit))


register.check_plugin(
    name="hp_icf_xcvr_table",
    service_name='SFP %s',
    check_function=check_hp_icf_xcvr_table,
    discovery_function=discovery_hp_icf_xcvr_table
)
