#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

#
# Sesam Plugin
# (c) 2022 DECOIT GmbH
#

#
# This is free software;  you can redistribute it and/or modify it
# under the  terms of the  GNU General Public License  as published by
# the Free Software Foundation in version 2.  Sesam Plugin is  distributed
# in the hope that it will be useful, but WITHOUT ANY WARRANTY;  with-
# out even the implied warranty of  MERCHANTABILITY  or  FITNESS FOR A
# PARTICULAR PURPOSE. See the  GNU General Public License for more de-
# ails.  You should have  received  a copy of the  GNU  General Public
# License along with GNU Make; see the file  COPYING.  If  not,  write
# to the Free Software Foundation, Inc., 51 Franklin St,  Fifth Floor,
# Boston, MA 02110-1301 USA.

from cmk.gui.i18n import _

from cmk.gui.plugins.wato import (
    HostRulespec,
    rulespec_registry,
)

from cmk.gui.cee.plugins.wato.agent_bakery.rulespecs.utils import RulespecGroupMonitoringAgentsAgentPlugins

from cmk.gui.valuespec import (
    Alternative,
    Dictionary,
    Password,
    TextUnicode,
    Age,
    TextAscii,
    Tuple,
    FixedValue,
)


def _valuespec_agent_config_sesam_backup_state_plugin():
    return Alternative(
        title=_("Sesam Backup State (DECOIT)"),
        help=_("This will deploy the agent plugin <tt>sesam_backup_state</tt> on linux systems "
               "for monitoring of ovirt infrastructure."),
        style="dropdown",
        elements=[
            Dictionary(
                title=_("Deploy the Sesam Backup State plugin"),
                elements=[
                    ("interval",
                     Age(
                         title=_("Run asynchronously"),
                         label=_("Interval for collecting data"),
                         default_value=3600,
                     )),
                    ("credentials", Tuple(
                        title=_("Credentials to access the API"),
                        elements=[
                            TextAscii(
                                title=_("Engine Username"),
                                default_value="monitoring",
                            ),

                            Password(
                                title=_("Engine Password")
                            ),
                        ]
                    )),
                    ("sesam_url",
                     TextUnicode(
                         title=_("Sesam URL"),
                         allow_empty=False,
                         default_value="https://localhost:11401"
                     )),
                    
                ],
                optional_keys=False,
            ),
            FixedValue(None, title=_("Do not deploy the Sesam Backup State plugin"), totext=_("(disabled)")),
        ],
    )


rulespec_registry.register(
    HostRulespec(
        group=RulespecGroupMonitoringAgentsAgentPlugins,
        name="agent_config:sesam_backup_state",
        valuespec=_valuespec_agent_config_sesam_backup_state_plugin,
    )
)
