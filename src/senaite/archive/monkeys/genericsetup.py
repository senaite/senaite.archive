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

from senaite.archive.interfaces import IForArchiving

from bika.lims import api
from bika.lims.exportimport.genericsetup.structure import SKIP_TYPES


def can_export(obj):
    """Decides if the object can be exported or not
    """
    if not api.is_object(obj):
        return False
    if IForArchiving.providedBy(obj):
        return True
    if api.get_portal_type(obj) in SKIP_TYPES:
        return False
    return True
