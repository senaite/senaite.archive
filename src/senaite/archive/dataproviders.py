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

import copy

from plone.dexterity.interfaces import IDexterityContent
from Products.ATContentTypes.interfaces import IATContentType
from senaite.archive.interfaces import IArchiveDataProvider
from senaite.jsonapi.api import to_iso_date
from zope.component import adapter
from zope.interface import implementer

from bika.lims import api
from bika.lims.interfaces import IAnalysisRequest
from bika.lims.interfaces import IBatch
from bika.lims.interfaces import IWorksheet


@implementer(IArchiveDataProvider)
class ArchiveBaseDataProvider(object):
    """Base data provider
    """

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        return self.to_dict()

    def to_dict(self):
        """Returns the dict representation of the object to be stored in the
         archived item
        """
        created = api.get_creation_date(self.context)
        modified = api.get_modification_date(self.context)
        creator = api.safe_getattr(self.context, "Creator", default="")
        creator = self.get_user_fullname(creator)

        return {
            "id": api.get_id(self.context),
            "uid": api.get_uid(self.context),
            "path": api.get_path(self.context),
            "Date created": to_iso_date(created, default=""),
            "Date modified": to_iso_date(modified, default=""),
            "Status": api.get_review_status(self.context),
            "portal_type": api.get_portal_type(self.context),
            "Created by": creator,
        }

    def searchable_text(self):
        """Returns a text with the words the item can be searched by
        """
        exclude = ["uid", "modified", "path"]
        obj_info = self.to_dict()
        keys = filter(lambda key: key not in exclude, obj_info.keys())
        values = map(lambda key: obj_info.get(key, ""), keys)
        values = filter(None, values)
        return " ".join(values)

    def get_iso_date(self, field_name, obj=None):
        obj = obj or self.context
        date_val = api.safe_getattr(obj, field_name, default=None)
        date_val = to_iso_date(date_val, default="")
        return date_val

    def get_user_fullname(self, user_id):
        """Returns a text with the format 'user_id (user_fullname)'
        """
        props = self.get_user_data(user_id)
        if not props:
            return user_id
        fullname = props.get("fullname", None)
        if fullname:
            user_id = "{} ({})".format(user_id, fullname)
        return user_id

    def get_user_data(self, user_id):
        """Returns a dict with the properties of the user with the given user id
        """
        user = api.get_user(user_id)
        if not user:
            return None
        properties = api.get_user_properties(user)
        properties.update({
            "userid": user.getId(),
            "username": user.getUserName() or user_id,
            "roles": user.getRoles(),
            "email": user.getProperty("email"),
            "fullname": user.getProperty("fullname"),
        })
        # Override with the properties from the associated Lab Contact, if any
        contact = api.get_user_contact(user)
        if contact:
            properties.update({
                "fullname": contact.getFullname() or properties["fullname"],
                "email": contact.getEmailAddress() or properties["email"]
            })
        return properties


@adapter(IATContentType)
class ArchiveArchetypesDataProvider(ArchiveBaseDataProvider):
    """Adapter for Archetypes
    """
    pass


@adapter(IDexterityContent)
class ArchiveDexterityDataProvider(ArchiveBaseDataProvider):
    """Adapter for Dexterity"""
    pass


@adapter(IAnalysisRequest)
class ArchiveAnalysisRequestDataProvider(ArchiveBaseDataProvider):

    _data_dict = None

    def to_dict(self):
        if not self._data_dict:
            data = super(ArchiveAnalysisRequestDataProvider, self).to_dict()
            sample_type = self.context.getSampleType()
            client = self.context.getClient()
            contact = self.context.getContact()
            date_sampled = self.get_iso_date("getDateSampled")
            date_published = self.get_iso_date("getDatePublished")
            verifiers = self.get_verifiers()
            submitters = self.get_submitters()
            analyses = self.get_analyses()
            batch_id = self.context.getBatchID()
            worksheets = self.get_worksheets()
            data.update({
                "Sample type": sample_type and api.get_title(sample_type) or "",
                "Client": client and api.get_title(client) or "",
                "Contact": contact and contact.getFullname() or "",
                "Date sampled": date_sampled,
                "Date published": date_published,
                "Verified by": verifiers,
                "Submitted by": submitters,
                "Analyses": analyses,
                "Batch": batch_id or "",
                "Worksheets": worksheets,
            })
            self._data_dict = data
        return copy.deepcopy(self._data_dict)

    def get_analyses(self):
        output = []
        skip = ["retracted", "rejected", "cancelled"]
        for analysis in self.context.getAnalyses(full_objects=True):
            if analysis.getHidden():
                continue
            state = api.get_review_status(analysis)
            if state in skip:
                continue
            result = analysis.getFormattedResult()
            if not result:
                continue

            keyword = analysis.getKeyword()
            unit = analysis.getUnit() or ""
            output.append("{}: {} {}".format(keyword, result, unit))
        return "; ".join(output)

    def get_worksheets(self):
        output = []
        for analysis in self.context.getAnalyses(full_objects=True):
            worksheet = analysis.getWorksheet()
            if worksheet:
                output.append(api.get_id(worksheet))
        return " ".join(output)

    def get_verifiers(self):
        verifiers = self.context.getVerifiersIDs() or []
        verifiers = filter(None, verifiers)
        verifiers = map(self.get_user_fullname, verifiers)
        return ", ".join(verifiers)

    def get_submitters(self):
        analyses = self.context.getAnalyses(full_objects=True)
        submitted_by = map(lambda an: an.getSubmittedBy(), analyses)
        submitted_by = filter(None, list(set(submitted_by)))
        submitted_by = map(self.get_user_fullname, submitted_by)
        return ", ".join(submitted_by)

    def searchable_text(self):
        """Returns a text with the words the item can be searched by
        """
        exclude = ["uid", "modified", "path", "Analyses"]
        obj_info = self.to_dict()
        keys = filter(lambda key: key not in exclude, obj_info.keys())
        values = map(lambda key: obj_info.get(key, ""), keys)
        values = filter(None, values)
        return " ".join(values)


@adapter(IBatch)
class ArchiveBatchDataProvider(ArchiveBaseDataProvider):

    _data_dict = None

    def to_dict(self):
        """Returns the dict representation of the object
        """
        if not self._data_dict:
            data = super(ArchiveBatchDataProvider, self).to_dict()
            client = self.context.getClient()
            client_batch_id = self.context.getClientBatchID() or ""
            batch_date = self.get_iso_date("BatchDate")

            data.update({
                "Client": client and api.get_title(client) or "",
                "Client Batch ID": client_batch_id,
                "Batch date": batch_date,
            })
            self._data_dict = data
        return copy.deepcopy(self._data_dict)


@adapter(IWorksheet)
class ArchiveWorksheetDataProvider(ArchiveBaseDataProvider):

    _data_dict = None

    def to_dict(self):
        """Returns the dict representation of the object
        """
        if not self._data_dict:
            data = super(ArchiveWorksheetDataProvider, self).to_dict()
            analyst = self.context.getAnalyst() or ""
            if analyst:
                analyst = self.get_user_fullname(analyst)

            data.update({
                "Analyst": analyst
            })
            self._data_dict = data
        return copy.deepcopy(self._data_dict)
