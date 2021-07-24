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

from datetime import datetime
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from senaite.archive import messageFactory as _
from senaite.archive.utils import archive_old_objects
from senaite.archive.utils import get_retention_date_criteria
from senaite.archive.utils import get_retention_period

from bika.lims import api
from bika.lims.browser import BrowserView


class DoArchiveView(BrowserView):
    """Form that allows the user to archive old items of the system
    at once, without having to archive them individually
    """
    template = ViewPageTemplateFile("templates/do_archive.pt")

    def __call__(self):
        # Don't allow any context actions
        self.request.set("disable_border", 1)

        form = self.request.form

        # Form submit toggle
        form_submitted = form.get("submitted", False)

        # Buttons
        form_confirm = form.get("button_confirm", False)
        form_cancel = form.get("button_cancel", False)

        # Handle cancel
        if form_submitted and form_cancel:
            return self.redirect(message=_("Archiving of records cancelled"))

        # Handle confirm
        if form_submitted and form_confirm:
            # Do the action here
            archive_old_objects()
            message = _("Archiving of records has finished successfully")
            return self.redirect(message=message)

        return self.template()

    def get_earliest_year(self):
        """Returns the earliest year that is within the retention period
        """
        return datetime.now().year - get_retention_period() + 1

    def get_date_criteria(self):
        """Returns the date criteria for the search of records that are outside
        of the retention period
        """
        return get_retention_date_criteria()

    @property
    def back_url(self):
        """Returns the back url
        """
        return api.get_url(self.context)

    def redirect(self, redirect_url=None, message=None, level="info"):
        """Redirect with a message
        """
        if redirect_url is None:
            redirect_url = self.back_url
        if message is not None:
            self.add_status_message(message, level)
        return self.request.response.redirect(redirect_url)

    def add_status_message(self, message, level="info"):
        """Set a portal status message
        """
        return self.context.plone_utils.addPortalMessage(message, level)
