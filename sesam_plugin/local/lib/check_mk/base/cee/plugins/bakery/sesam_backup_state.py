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
# the Free Software Foundation in version 2.  Ovirt Plugin is  distributed
# in the hope that it will be useful, but WITHOUT ANY WARRANTY;  with-
# out even the implied warranty of  MERCHANTABILITY  or  FITNESS FOR A
# PARTICULAR PURPOSE. See the  GNU General Public License for more de-
# ails.  You should have  received  a copy of the  GNU  General Public
# License along with GNU Make; see the file  COPYING.  If  not,  write
# to the Free Software Foundation, Inc., 51 Franklin St,  Fifth Floor,
# Boston, MA 02110-1301 USA.

from pathlib import Path
from typing import Any, Dict, Iterable

from .bakery_api.v1 import FileGenerator, OS, Plugin, PluginConfig, register


def get_sesam_backup_state_files(conf: Dict[str, Any]) -> FileGenerator:
    yield Plugin(
        base_os=OS.LINUX,
        source=Path("sesam_backup_state.py"),
        interval=conf.get("interval")
    )

    yield PluginConfig(
        base_os=OS.LINUX,
        lines=list(_get_sesam_backup_state_config(conf)),
        target=Path("sesam_backup_state.cfg"),
        include_header=True,
    )


def _get_sesam_backup_state_config(conf: Dict[str, Any]) -> Iterable[str]:
    yield "[SESAM]"
    if "credentials" in conf:
        yield "username=%s" % conf['credentials'][0]
        yield "password=%s" % conf['credentials'][1]
    if "sesam_url" in conf:
        yield "sesam_url=%s" % conf['sesam_url']


register.bakery_plugin(
    name="sesam_backup_state",
    files_function=get_sesam_backup_state_files,
)
