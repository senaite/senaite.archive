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

from senaite.lims.interfaces import ISenaiteLIMS
from zope.interface import Interface

from bika.lims.interfaces import IBikaLIMS
from bika.lims.interfaces import IDoNotSupportSnapshots
from bika.lims.interfaces import IHideActionsMenu


class ISenaiteArchiveLayer(IBikaLIMS, ISenaiteLIMS):
    """Zope 3 browser Layer interface specific for senaite.queue
    This interface is referred in profiles/default/browserlayer.xml.
    All views and viewlets register against this layer will appear in the site
    only when the add-on installer has been run.
    """


class IForArchiving(Interface):
    """Marker interface for objects that are being archived
    """


class IArchiveFolder(IHideActionsMenu, IDoNotSupportSnapshots):
    """Marker interface for ArchiveFolder content
    """


class IArchiveItem(IHideActionsMenu, IDoNotSupportSnapshots):
    """Marker interface for ArchiveItem content
    """


class IArchiveCatalog(Interface):
    """Archive catalog interface
    """


class IArchiveDataProvider(Interface):
    """Interface for items to be archived
    """

    def to_dict(self):
        """Returns the dict representation of the object
        """

    def searchable_text(self):
        """Returns a text with the words the item can be searched by
        """

    def __call__(self):
        """Returns the dict representation of the object
        """
