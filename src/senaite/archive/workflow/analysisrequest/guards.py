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

from senaite.archive import is_installed
from senaite.archive.utils import get_archiving_dependents
from senaite.archive.utils import is_outside_retention_period

from bika.lims.interfaces import IAnalysisRequest
from bika.lims.workflow import isTransitionAllowed


def guard_archive(sample):
    """Returns true if current sample can be archived based on the date the
    sample was registered and the retention period (in years) defined in the
    Archive settings
    """
    # Check if senaite.archive is properly installed
    if not is_installed():
        return False

    # Check if the object is outside the retention period
    if not is_outside_retention_period(sample):
        return False

    # All back references have to be archive-able too
    for ref in get_archiving_dependents(sample):
        if IAnalysisRequest.providedBy(ref):
            if not isTransitionAllowed(ref, "archive"):
                return False

    return True
