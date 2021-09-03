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

from plone.app.textfield import RichText
from plone.autoform import directives
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.interfaces import IDexterityContent
from plone.supermodel import model
from senaite.archive import messageFactory as _
from senaite.archive.utils import to_field_datetime
from zope import schema
from zope.component import adapter
from zope.interface import implementer
from zope.interface import provider


@provider(IFormFieldProvider)
class IArchiveItemBehavior(model.Schema):

    item_type = schema.TextLine(
        title=_(u"Item type"),
        required=True,
    )

    item_id = schema.TextLine(
        title=_(u"Item ID"),
        required=True,
    )

    item_path = schema.TextLine(
        title=_(u"Item path"),
        required=True,
    )

    archive_path = schema.TextLine(
        title=_(u"Archive relative path"),
        required=True,
    )

    directives.omitted("item_created")
    item_created = schema.Datetime(
        title=_(u"Item creation date"),
        required=True,
    )

    directives.omitted("item_modified")
    item_modified = schema.Datetime(
        title=_(u"Item modification date"),
        required=True,
    )

    directives.omitted("search_text")
    search_text = schema.Text(
        title=_(u"Searchable text"),
        required=False,
    )

    item_data = RichText(
        title=_(u"Item summary"),
        required=False,
    )


@implementer(IArchiveItemBehavior)
@adapter(IDexterityContent)
class ArchiveItem(object):

    def __init__(self, context):
        self.context = context
        self.exclude_from_nav = True

    def _get_item_type(self):
        return getattr(self.context, "item_type")

    def _set_item_type(self, value):
        self.context.item_type = value

    item_type = property(_get_item_type, _set_item_type)

    def _get_item_id(self):
        return getattr(self.context, "item_id")

    def _set_item_id(self, value):
        self.context.item_id = value

    item_id = property(_get_item_id, _set_item_id)

    def _get_item_path(self):
        return getattr(self.context, "item_path")

    def _set_item_path(self, value):
        self.context.item_path = value

    item_path = property(_get_item_path, _set_item_path)

    def _get_archive_path(self):
        return getattr(self.context, "archive_path")

    def _set_archive_path(self, value):
        self.context.archive_path = value

    archive_path = property(_get_archive_path, _set_archive_path)

    def _get_item_created(self):
        return getattr(self.context, "item_created")

    def _set_item_created(self, value):
        dt = to_field_datetime(value)
        self.context.item_created = dt

    item_created = property(_get_item_created, _set_item_created)

    def _get_item_modified(self):
        return getattr(self.context, "item_modified")

    def _set_item_modified(self, value):
        dt = to_field_datetime(value)
        self.context.item_modified = dt

    item_modified = property(_get_item_modified, _set_item_modified)

    def _get_search_text(self):
        return getattr(self.context, "search_text")

    def _set_search_text(self, value):
        self.context.search_text = value

    search_text = property(_get_search_text, _set_search_text)

    def _get_item_data(self):
        return getattr(self.context, "item_data")

    def _set_item_data(self, value):
        self.context.item_data = value

    item_data = property(_get_item_data, _set_item_data)
