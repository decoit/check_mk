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
from cmk.gui.valuespec import (
    Dictionary,
    Tuple,
    Age,
    Integer,
)

from cmk.gui.plugins.wato import (
    CheckParameterRulespecWithoutItem,
    rulespec_registry,
    RulespecGroupCheckParametersApplications,
)


def _parameter_puppet_events():
    return Dictionary(
        elements=[
            (
                'levels',
                Tuple(
                    title=_('Events Failure'),
                    elements=[
                        Integer(
                            title=_("Warning at or above"),
                            default_value=2
                        ),
                        Integer(
                            title=_("Critical at or above"),
                            default_value=5
                        ),
                    ],
                )
            ),
        ],
        optional_keys=False,
    )


rulespec_registry.register(
    CheckParameterRulespecWithoutItem(
        group=RulespecGroupCheckParametersApplications,
        check_group_name="puppet_agent_events",
        title=lambda: _("Puppet Events Failure"),
        parameter_valuespec=_parameter_puppet_events,
        match_type="dict",
    )
)


def _parameter_puppet_lastrun():
    return Dictionary(
        elements=[
            (
                'levels',
                Tuple(
                    title=_('Last run of puppet'),
                    elements=[
                        Age(
                            title=_("Warning at or above"),
                            default_value=86400,
                        ),
                        Age(
                            title=_("Critical at or above"),
                            default_value=604800,
                        ),
                    ],
                )
            ),
        ],
        optional_keys=False,
    )


rulespec_registry.register(
    CheckParameterRulespecWithoutItem(
        group=RulespecGroupCheckParametersApplications,
        check_group_name="puppet_agent_lastrun",
        title=lambda: _("Puppet Lastrun"),
        parameter_valuespec=_parameter_puppet_lastrun,
        match_type="dict",
    )
)
