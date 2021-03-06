# -*- coding: utf-8 -*-
#
# This file is part of SENAITE.ARCHIVE.
#
# SENAITE.ARCHIVE is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright 2021 by it's authors.
# Some rights reserved, see README and LICENSE.

from senaite.archive.workflow import BaseGuardAdapter
from senaite.archive.workflow import TransitionEventHandler
from senaite.archive.workflow.worksheet import events
from senaite.archive.workflow.worksheet import guards


def AfterTransitionEventHandler(worksheet, event): # noqa lowercase
    """Actions to be done just after a transition for a worksheet takes place
    """
    TransitionEventHandler("after", worksheet, events, event)


class GuardAdapter(BaseGuardAdapter):
    """Adapter for Worksheet guards
    """
    def get_module(self):
        return guards
