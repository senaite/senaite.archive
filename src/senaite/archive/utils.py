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
import six
from Acquisition import aq_base
from datetime import datetime
from DateTime import DateTime
from plone.app.textfield import RichTextValue
from Products.Archetypes.config import UID_CATALOG
from Products.GenericSetup.context import DirectoryExportContext
from senaite.archive import logger
from senaite.archive.config import PRODUCT_NAME
from senaite.archive.interfaces import IArchiveDataProvider
from senaite.archive.interfaces import IForArchiving
from zope.component import getMultiAdapter
from zope.interface import alsoProvides
from zope.interface import noLongerProvides

from bika.lims import api
from bika.lims.catalog import BIKA_CATALOG
from bika.lims.catalog import CATALOG_ANALYSIS_REQUEST_LISTING
from bika.lims.catalog import CATALOG_WORKSHEET_LISTING
from bika.lims.exportimport.genericsetup.structure import exportObjects
from bika.lims.interfaces import IAnalysisRequest
from bika.lims.interfaces import IAuditable
from bika.lims.interfaces import IBatch
from bika.lims.interfaces import IWorksheet
from bika.lims.workflow import doActionFor as do_action_for
from bika.lims.workflow import isTransitionAllowed

try:
    from senaite.queue.api import is_queue_ready
    from senaite.queue.api import add_action_task
except:
    # Queue is not installed
    is_queue_ready = None
    add_action_task = None


def can_archive(obj):
    """Returns whether the object can be archived
    """
    if not api.is_object(obj):
        return False

    if api.is_portal(obj):
        return False

    # The object itself or its parent has the transition "archive" permitted
    if not isTransitionAllowed(obj, "archive"):
        parent = api.get_parent(obj)
        return can_archive(parent)

    return True


def is_archive_valid():
    """Returns whether the configuration of the archive is valid
    """
    # A valid base directory must be set (this field is required, but comes
    # empty the first time the add-on is installed)
    base_path = get_archive_base_path()
    if not base_path:
        return False
    return True


def archive_old_objects(context=None):  # noqa context is required by genericsetup
    """Archives (and deletes) all archive-able objects from the system that are
    older than the retention period. This function is used by the generic setup
    """
    for obj in archivable_objects():
        do_action_for(obj, "archive")


def search(portal_type):
    """Search items from the given portal type
    """
    mappings = {
        "AnalysisRequest": CATALOG_ANALYSIS_REQUEST_LISTING,
        "Worksheet": CATALOG_WORKSHEET_LISTING,
        "Batch": BIKA_CATALOG,
    }
    query = {"portal_type": portal_type}
    catalog = mappings.get(portal_type, UID_CATALOG)
    if portal_type in mappings:
        query.update({
            "sort_on": "created",
            "sort_order": "ascending",
        })
    return api.search(query, catalog)


def archivable_objects(limit=-1):
    """Returns an enumerator with objects their type is suitable for archival
    and they are outside of the retention period
    """
    # We sort by portal type so we are sure that Samples are processed first
    num_objs = 0
    portal_types = ["AnalysisRequest", "Batch", "Worksheet"]
    for portal_type in portal_types:
        if 0 < limit <= num_objs:
            break
        for obj in search(portal_type):
            if 0 < limit <= num_objs:
                break
            obj = api.get_object(obj)
            if can_archive(obj):
                num_objs += 1
                yield obj


def do_archive():
    """Archives (and deletes) all archivable objects from the system that are
    older than the retention period, but may use the queue if active. If the
    queue is not active or not installed, all objects are archived in a single
    transaction
    """
    def is_queue_ok():
        try:
            return is_queue_ready()
        except:
            return False

    if is_queue_ok():
        # Archive all objects by means of the queue
        queue_do_archive()
    else:
        # Archive all objects in a single shot
        archive_old_objects()


def queue_do_archive():
    """Adds a queued task (if senaite.queue installed and active) in charge of
    archiving the non-active records that are outside of the retention period
    """
    kwargs = {
        "priority": 50,
        "chunk_size": 1,
        "unique": True,
        "ghost": True,
    }
    uids = map(api.get_uid, archivable_objects(limit=10000))
    archive_folder = api.get_portal().archive
    add_action_task(uids, "archive", archive_folder, **kwargs)


def archive_object(obj):
    """Archives an deletes an object, while creating a new lightweight object
    representing the former and only used for historical searches
    """
    # Archive object dependents (back references) first. Won't be possible to
    # delete the object otherwise
    for dep in get_archiving_dependents(obj):
        do_action_for(dep, "archive")

    # Mark the object and its children with IForArchiving interface, so the
    # generic setup export machinery does not dismiss them when exporting the
    # contents into XML files. See monkeys/genericsetup/can_export
    # Also, remove the IAuditable so no record in auditlog catalog is created
    for ob in extract(obj):
        if can_archive(ob):
            alsoProvides(ob, IForArchiving)
            noLongerProvides(ob, IAuditable)

    # Do a transaction savepoint
    #transaction.savepoint(optimistic=True)

    # Export object to the Archive's path in filesystem
    archive_path = get_archive_relative_path(obj)
    export_context = get_export_context()
    exportObjects(obj, archive_path, export_context)

    # Create the ArchiveItem object, a DT lightweight object with it's own
    # catalog , used for historical searches
    create_archive_item(obj, "/{}".format(archive_path))

    # Definitely remove (and uncatalog) the object
    delete(obj)


def create_archive_item(obj, archive_path):
    """Creates an archive item that represents the object passed-in
    """
    # Extract the data from the object with the proper adapter
    request = api.get_request()
    provider = getMultiAdapter((obj, request), IArchiveDataProvider)
    item_data = provider.to_dict()

    # Exclude those key-values that are directly added to the item
    exclude = ["id", "uid", "path", "portal_type"]

    # Transform item_data to HTML-like
    html = []
    keys = sorted(item_data.keys())
    keys = filter(lambda k: k not in exclude, keys)
    for key in keys:
        val = item_data.get(key)
        html.append("<li><strong>{}</strong>: {}</li>".format(key, val))
    html = "".join(html)
    html = "<ul>{}</ul>".format(html)
    html = RichTextValue(html, "text/html", "text/html")

    # Extract the text to allow searches by
    search_text = provider.searchable_text()

    # Giving the field values on creation saves a reindex after edition
    field_values = dict(
        title=api.get_title(obj),
        item_id=api.get_id(obj),
        item_path=api.get_path(obj),
        item_type=api.get_portal_type(obj),
        item_created=api.get_creation_date(obj),
        item_modified=get_last_modification_date(obj),
        item_data=html,
        archive_path=archive_path,
        search_text=search_text,
        exclude_from_nav=True
    )
    archive = api.get_portal().archive
    return api.create(archive, "ArchiveItem", **field_values)


def get_archiving_dependents(obj):
    """Returns a list of objects that need to be archived before the obj
    """
    refs = []
    if IAnalysisRequest.providedBy(obj):
        # Retests
        refs.append(obj.get_retest())

        # Secondaries
        secondaries = obj.getSecondaryAnalysisRequests() or []
        refs.extend(secondaries)

        # Descendants
        descendants = obj.getDescendants() or []
        refs.extend(descendants)

    else:
        # Extract the samples from Worksheet, Batch
        refs = get_samples(obj)

    return filter(None, refs)


def get_retention_period():
    """Returns the retention period in years set in the configuration panel
    """
    key = "{}.retention_period".format(PRODUCT_NAME)
    return api.get_registry_record(key)


def get_retention_date_criteria():
    """Returns the retention date criteria set in the configuration panel
    """
    key = "{}.date_criteria".format(PRODUCT_NAME)
    return api.get_registry_record(key)


def is_outside_retention_period(obj):
    """Returns whether the given object is outside the retention period based on
    the date criteria and retention period set in the configuration panel.
    """
    retention_period = get_retention_period()
    if retention_period is None:
        # If no retention period is set, retain the object
        return False

    # Assume object's creation date as default threshold criteria
    obj_date = api.get_creation_date(obj)
    criteria = get_retention_date_criteria()
    if criteria == "modified":
        obj_date = get_last_modification_date(obj)

    # Check if the object is old enough
    threshold_year = datetime.now().year - retention_period
    return obj_date.year() <= threshold_year


def get_last_modification_date(obj):
    """Returns the last modification date of the object passed-in,
    transitions dates included
    """
    review_history = api.get_review_history(obj)
    dates = map(lambda rh: rh.get("time", None), review_history)
    dates.extend([
        api.get_creation_date(obj),
        api.get_modification_date(obj)
    ])
    return max(filter(None, dates))


def get_archive_base_path():
    """Returns the base path where the archive lives
    """
    key = "{}.archive_base_path".format(PRODUCT_NAME)
    return api.get_registry_record(key)


def get_archive_relative_path(obj):
    """Returns the relative path where the current obj will be archived
    """
    parent = api.get_parent(obj)
    parent_path = api.get_path(parent)

    # Prefix with year/week number
    created = api.get_creation_date(obj)
    created = created.strftime("%Y/%W")
    return "{}{}/".format(created, parent_path)


def get_export_context():
    """Returns the export context to use for archiving
    """
    portal = api.get_portal()
    base_path = get_archive_base_path()
    return ArchiveDirectoryExportContext(portal.portal_setup, base_path)


def delete(obj):
    """Deletes and un-catalog the object passed-in, as well as all the objects
    it contains within its hierarchy
    """
    # Un-catalog all objects from the hierarchy first
    for ob in extract(obj):
        ob_path = api.get_path(ob)
        catalogs = api.get_catalogs_for(ob)
        map(lambda cat: cat.uncatalog_object(ob_path), catalogs)

    # Remove the object
    obj_id = api.get_id(obj)
    parent = api.get_parent(obj)
    parent._delObject(obj_id) # Noqa


def extract(obj):
    """Extracts the objects contained within the hierarchy of the obj passed-in,
    sorted from deepest to shallowest
    """
    objects = []
    if hasattr(aq_base(obj), "objectValues"):
        for child_obj in obj.objectValues():
            children = extract(child_obj)
            objects.extend(children)
    objects.append(obj)
    return objects


def to_field_datetime(value):
    """Converts the value to a valid datetime instance, suitable for the value
    assignment to schema.Datetime fields
    """
    if isinstance(value, DateTime):
        value = value.asdatetime()
    elif isinstance(value, six.string_types):
        # convert string to datetime
        dt = api.to_date(value)
        if dt is not None:
            value = dt.asdatetime()

    # Ensure the datetime object has no timezone set
    # TypeError: can't compare offset-naive and offset-aware datetimes
    if isinstance(value, datetime):
        value = value.replace(tzinfo=None)
    else:
        value = None

    return value


def get_samples(obj):
    """Returns the samples assigned to the obj passed-in
    """
    samples = []
    if IBatch.providedBy(obj):
        # Contained Samples
        query = {"getBatchUID": api.get_uid(obj)}
        samples = api.search(query, CATALOG_ANALYSIS_REQUEST_LISTING)
        samples = map(api.get_object, samples)

    elif IWorksheet.providedBy(obj):
        # Samples assigned to this worksheet through its analyses
        uids = map(lambda l: l.get("container_uid"), obj.getLayout())
        uids = filter(None, uids)
        if uids:
            query = {"UID": uids}
            samples = api.search(query, CATALOG_ANALYSIS_REQUEST_LISTING)
            samples = map(api.get_object, samples)

    return samples


class ArchiveDirectoryExportContext(DirectoryExportContext):

    def get_file_path(self, filename, subdir=None):
        """Returns the full file path for the filename passed in
        """
        if subdir is None:
            prefix = self._profile_path
        else:
            prefix = os.path.join(self._profile_path, subdir)

        return os.path.join(prefix, filename)

    def writeDataFile(self, filename, text, content_type, subdir=None):
        # Create the directory if it does not exist yet
        file_path = self.get_file_path(filename, subdir=subdir)
        logger.info("Archiving file ({}): {}".format(content_type, file_path))
        dir_path = os.path.dirname(file_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        # Delegate to superclass
        base = super(ArchiveDirectoryExportContext, self)
        base.writeDataFile(filename, text, content_type, subdir=subdir)
