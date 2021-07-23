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

from senaite.archive.catalog import CATALOG_ARCHIVE
from senaite.core.listing import ListingView
from bika.lims import api
from senaite.archive import messageFactory as _
import collections
from plone.memoize import view

from bika.lims.utils import get_link


class ArchiveFolderView(ListingView):
    """View that lists the Archive Items
    """

    def __init__(self, context, request):
        super(ArchiveFolderView, self).__init__(context, request)

        self.title = api.get_title(self.context)
        self.description = api.get_description(self.context)
        self.icon = api.get_icon(self.context, html_tag=False)
        self.icon = self.icon.replace("archive.png", "archive_big.png")
        self.show_select_row = False
        self.show_select_column = False

        self.catalog = CATALOG_ARCHIVE

        self.contentFilter = {
            "portal_type": "ArchiveItem",
            "sort_on": "item_modified",
            "sort_order": "descending",
        }

        self.context_actions = {}

        self.columns = collections.OrderedDict((
            ("item_id", {
                "title": _("ID"),
                "index": "item_id",
            }),
            ("item_type", {
                "title": _("Type"),
                "index": "item_type",
            }),
            ("item_created", {
                "title": _("Created"),
                "index": "item_created",
            }),
            ("item_modified", {
                "title": _("Modified"),
                "index": "item_modified",
            }),
            ("item_path", {
                "title": _("Path"),
                "toggle": False,
            }),
        ))

        self.review_states = [
            {
                "id": "default",
                "title": _("All"),
                "contentFilter": {},
                "columns": self.columns.keys(),
            },
        ]

    def before_render(self):
        """Before template render hook
        """
        # Don't allow any context actions
        self.request.set("disable_border", 1)

    @view.memoize
    def get_archive_url(self):
        """Returns the url of the Archive folder
        """
        portal = api.get_portal()
        return api.get_url(portal.archive)

    def folderitem(self, obj, item, index):
        """Service triggered each time an item is iterated in folderitems.
        The use of this service prevents the extra-loops in child objects.
        :obj: the instance of the class to be foldered
        :item: dict containing the properties of the object to be used by
            the template
        :index: current index of the item
        """
        archive_url = self.get_archive_url()
        url = "{}/{}".format(archive_url, api.get_id(obj))
        item["replace"]["item_id"] = get_link(url, value=obj.item_id)
        utime = self.ulocalized_time
        item.update({
            "item_created": utime(obj.item_created, long_format=False),
            "item_modified": utime(obj.item_modified, long_format=False),
        })
        return item
