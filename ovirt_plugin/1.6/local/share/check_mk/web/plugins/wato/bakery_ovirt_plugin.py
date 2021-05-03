#!/usr/bin/env python
# -*- encoding: utf-8; py-indent-offset: 4 -*-

register_rule('agents/agent_plugins',
              "agent_config:ovirt_plugin",
              Alternative(
                  title=_("oVirt Plugin (Linux)"),
                  help=_("This will deploy the agent plugin <tt>ovirt_plugin</tt> on linux systems "
                         "for monitoring of oVirt infrastructure."),
                  style="dropdown",
                  elements=[
                      Dictionary(
                          title=_("Deploy the oVirt plugin"),
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
                                          title=_("Engine password")
                                      ),
                                  ]
                              )),
                              ("engine_fqdn",
                               TextUnicode(
                                   title=_("Engine FQDN"),
                                   allow_empty=False,
                               )),
                              ("engine_url",
                               TextUnicode(
                                   title=_("Engine URL"),
                                   allow_empty=False,
                               )),
                              ("generate_piggyback",
                               DropdownChoice(
                                   title=_("Generate piggyback data"),
                                   choices=[
                                       (True, _("Generate piggyback data")),
                                       (False, _("Do not generate piggyback data")),
                                   ]
                               )),
                              ("python_version",
                               DropdownChoice(
                                   title=_("Use Python Version"),
                                   choices=[
                                       ("3", _("use Python 3 (/usr/bin/env python3)")),
                                       ("2", _("use Python 2 (/usr/bin/env python)")),
                                   ],
                               )),
                          ],
                          optional_keys=False,
                      ),
                      FixedValue(None, title=_(
                          "Do not deploy the oVirt plugin"), totext=_("(disabled)")),
                  ],
              )
              )
