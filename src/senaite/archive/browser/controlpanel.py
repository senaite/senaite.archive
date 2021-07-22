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

import os
from datetime import datetime
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.z3cform import layout
from senaite.archive import messageFactory as _
from zope import schema
from zope.interface import Interface
from zope.interface import Invalid
from zope.schema.vocabulary import SimpleVocabulary


def validate_directory(path):
    """Return true if the value is a directory that exists locally and for
    which writing privileges are granted
    """
    if not os.path.isdir(path):
        raise Invalid(_("Not a directory or does not exist"))

    # Check if current user has write privileges
    tmp_file_name = "{}.tmp".format(datetime.now().microsecond)
    try:
        file_path = os.path.join(path, tmp_file_name)
        with open(file_path, 'w') as fp:
            pass
        os.remove(file_path)
    except IOError as e:
        # Cannot write
        raise Invalid(e.strerror)

    return True


class IArchiveControlPanel(Interface):
    """Control panel Settings for the Archive module
    """

    retention_period = schema.Int(
        title=_(u"Retention period"),
        description=_(
            "Number of years you want to retain data for. Default: 2 (years)"
        ),
        min=0,
        max=20,
        default=2,
        required=True,
    )

    date_criteria = schema.Choice(
        title=_(u"Date criteria"),
        description=_(
            "Date used to check whether an electronic record is outside of the "
            "retention period. Default: 'created'",
        ),
        vocabulary=SimpleVocabulary.fromValues([u'created', u'modified']),
        default=u'created',
        required=True,
    )

    archive_base_path = schema.TextLine(
        title=_(u"Archive path"),
        description=_(
            "Full path of the local directory where archived objects will be "
            "stored. User that runs the instance must have write access."
        ),
        constraint=validate_directory,
        required=True,
    )


class ArchiveControlPanelForm(RegistryEditForm):
    schema = IArchiveControlPanel
    schema_prefix = "senaite.archive"
    label = _("Archive Settings")


ArchiveControlPanelView = layout.wrap_form(ArchiveControlPanelForm,
                                           ControlPanelFormWrapper)
