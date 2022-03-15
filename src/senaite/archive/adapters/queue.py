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

from senaite.archive.interfaces import IArchiveFolder
from senaite.archive.utils import can_archive
from senaite.archive.utils import queue_do_archive
from zope.component import adapter
from zope.interface import implementer

from bika.lims import api
from bika.lims.workflow import doActionFor

try:
    from senaite.queue.interfaces import IQueuedTaskAdapter
except:
    # senaite.queue is not installed
    from zope.interface import Interface as IQueuedTaskAdapter


@implementer(IQueuedTaskAdapter)
@adapter(IArchiveFolder)
class QueuedDoArchiveTaskAdapter(object):
    """Adapter for the archival of objects
    """

    def __init__(self, context):
        self.context = context

    def process(self, task):
        """Transition the objects from the task
        """
        # Extract and process the objects
        for uid in task.uids:
            obj = api.get_object_by_uid(uid, default=None)
            if can_archive(obj):
                doActionFor(obj, "archive")

        # Add next chunk of objects to the queue
        chunk_size = task.get("chunk_size", 10)
        priority = task.get("priority", 50)
        queue_do_archive(chunk_size=chunk_size, priority=priority)
