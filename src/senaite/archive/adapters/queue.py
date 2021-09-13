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
from senaite.archive.config import QUEUE_TASK_ID
from senaite.archive.interfaces import IArchiveFolder
from senaite.archive.utils import queue_do_archive
from senaite.queue.api import add_task
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
        priority = task.get("priority", 50)

        # Process the objects, but one by one
        uids = copy.deepcopy(task.uids) or []
        if uids:
            obj = api.get_object_by_uid(uids[0])
            doActionFor(obj, "archive")

        # Create new task with the remaining uids
        next_uids = uids[1:]
        if next_uids:
            kwargs = {
                "uids": next_uids,
                "priority": priority,
                "chunk_size": len(next_uids),
            }
            archive_folder = api.get_portal().archive
            add_task(QUEUE_TASK_ID, archive_folder, **kwargs)

        else:
            # Queue a new set of objects for archiving
            queue_do_archive(priority=priority)
