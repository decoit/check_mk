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

from cmk.gui.i18n import _

from cmk.gui.plugins.wato import (
    HostRulespec,
    rulespec_registry,
)

from cmk.gui.cee.plugins.wato.agent_bakery.rulespecs.utils import RulespecGroupMonitoringAgentsAgentPlugins

from cmk.gui.valuespec import (
    DropdownChoice,
)


def _valuespec_agent_config_mk_puppet():
    return DropdownChoice(
        title=_("Puppet Execution State (Linux)"),
        help=_("Hosts configured via this rule get the <tt>mk_puppet</tt> plugin "
               "deployed."),
        choices=[
            (True, _("Deploy puppet plugin")),
            (None, _("Do not deploy puppet plugin")),
        ]
    )


rulespec_registry.register(
    HostRulespec(
        group=RulespecGroupMonitoringAgentsAgentPlugins,
        name="agent_config:mk_puppet",
        valuespec=_valuespec_agent_config_mk_puppet,
    )
)
