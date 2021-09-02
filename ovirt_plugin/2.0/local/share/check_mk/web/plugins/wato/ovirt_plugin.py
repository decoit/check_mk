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


from cmk.gui.i18n import _
from cmk.gui.valuespec import (
    Dictionary,
    Percentage,
    TextAscii,
    Tuple,
    MonitoringState,
    ListOfStrings,
)

from cmk.gui.plugins.wato import (
    CheckParameterRulespecWithItem,
    CheckParameterRulespecWithoutItem,
    rulespec_registry,
    RulespecGroupCheckParametersStorage,
    RulespecGroupCheckParametersApplications,
)
from cmk.gui.plugins.wato.check_parameters.utils import filesystem_elements


def _parameter_ovirt_snapshots():
    return Dictionary(
        elements = [
            ('state', 
             MonitoringState(
                             title=_("State if snapshots are found"),
                             default_value=1,
                         )
            ),
            ('allow',
             ListOfStrings(
                 title = _('Reqular expressions for snapshots to allow even if ignored (see below).'),
                 )
            ),
            ('ignore',
             ListOfStrings(
                 title = _('Reqular expressions for snapshots to ignore'),
                 )
            ),
        ],
    )

rulespec_registry.register(
    CheckParameterRulespecWithoutItem(
    group=RulespecGroupCheckParametersApplications,
    check_group_name = "ovirt_snapshots",
    title =lambda: _("Parameters for oVirt snapshots"),
    parameter_valuespec = _parameter_ovirt_snapshots,
    match_type = "dict",
))

def _parameter_ovirt_storage_domains():
    return Dictionary(
        elements=filesystem_elements + [
        ],
        hidden_keys=["flex_levels", 
                     "show_reserved", "subtract_reserved",
                     "inodes_levels", "show_inodes"],
    )


rulespec_registry.register(
    CheckParameterRulespecWithItem(
        check_group_name="ovirt_storage_domains",
        group=RulespecGroupCheckParametersStorage,
        item_spec=lambda: TextAscii(title=_("Name of the storage domain"), allow_empty=False),
        match_type="dict",
        parameter_valuespec=_parameter_ovirt_storage_domains,
        title=lambda: _("oVirt storage domain capacity"),
    )
)