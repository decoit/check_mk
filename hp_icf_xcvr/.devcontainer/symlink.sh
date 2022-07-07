#!/bin/bash

declare -a DIRS=(
    "local/share/check_mk/agents"
    "local/share/check_mk/checkman"
    "local/share/check_mk/checks"
    "local/share/check_mk/doc"
    "local/share/check_mk/inventory"
    "local/share/check_mk/notifications"
    "local/share/check_mk/pnp-templates"
    "local/share/check_mk/web"
    "local/lib/check_mk/base/plugins/agent_based"
    "local/lib/nagios/plugins"
)

for DIR in "${DIRS[@]}"; do
    if [ -e $WORKSPACE/$DIR ]; then
        rm -rfv $OMD_ROOT/$DIR
        ln -sv $WORKSPACE/$DIR $OMD_ROOT/$DIR
    fi
done;
