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

import collections
from datetime import datetime
from DateTime import DateTime
from plone.memoize import view
from senaite.archive import messageFactory as _
from senaite.archive import permissions
from senaite.archive.catalog import CATALOG_ARCHIVE
from senaite.archive.utils import is_archive_valid
from senaite.core.listing import ListingView

from bika.lims import api
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
            "sort_on": "item_created",
            "sort_order": "ascending",
        }

        self.context_actions = {}
        if is_archive_valid():
            self.context_actions = {
                _("Archive old records"): {
                    "permission": permissions.AddArchiveItem,
                    "url": "{}/do_archive".format(api.get_url(self.context)),
                    "icon": "++resource++bika.lims.images/add.png"}
            }

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

        # Add as many review states as years for archived records
        for year in self.get_years_range():
            self.review_states.append({
                "id": str(year),
                "title": str(year),
                "contentFilter": {"item_created": self.get_year_query(year)},
                "columns": self.columns.keys()
            })

    def get_year_query(self, year):
        first_day = DateTime(year, 1, 1).earliestTime()
        last_day = DateTime(year, 12, 31).latestTime()
        return {
            "query": [first_day, last_day],
            "range": "min:max",
        }

    @view.memoize
    def get_years_range(self):
        """Returns a tuple with the range of years for which there are archived
        records. Returns None if there are no records
        """
        def get_year(obj):
            if isinstance(obj, DateTime):
                return obj.year()
            return obj.year

        query = {
            "portal_type": "ArchiveItem",
            "sort_on": "item_created",
            "sort_order": "ascending",
            "sort_limit": 1,
        }
        brains = api.search(query, CATALOG_ARCHIVE)
        if not brains:
            return []

        # Oldest year
        min_year = get_year(brains[0].item_created)

        # Newest year
        query.update({"sort_order": "descending"})
        brains = api.search(query, CATALOG_ARCHIVE)
        max_year = get_year(brains[0].item_created)
        return range(min_year, max_year+1)

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
