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

import time
import transaction
from plone import api as ploneapi
from Products.DCWorkflow.Guard import Guard
from senaite.archive import logger
from senaite.archive import messageFactory as _
from senaite.archive import permissions
from senaite.archive.catalog import CATALOG_ARCHIVE
from senaite.archive.config import PRODUCT_NAME
from senaite.archive.config import PROFILE_ID
from senaite.archive.config import UNINSTALL_ID

from bika.lims import api

# Tuples of (folder_id, folder_name, type)
PORTAL_FOLDERS = [
    ("archive", "Archive", "ArchiveFolder"),
]

INDEXES = [
    # Tuples of (catalog, id, indexed attribute, type)
    (CATALOG_ARCHIVE, "item_id", "FieldIndex"),
    (CATALOG_ARCHIVE, "item_type", "FieldIndex"),
    (CATALOG_ARCHIVE, "item_created", "DateIndex"),
    (CATALOG_ARCHIVE, "item_modified", "DateIndex"),
]

COLUMNS = [
    # Tuples of (catalog, column name)
    (CATALOG_ARCHIVE, "item_id"),
    (CATALOG_ARCHIVE, "item_type"),
    (CATALOG_ARCHIVE, "item_created"),
    (CATALOG_ARCHIVE, "item_modified"),
    (CATALOG_ARCHIVE, "item_path"),
]

CATALOGS_BY_TYPE = [
    # Tuples of (type, [catalog]) Additive behavior only
    ("ArchiveItem", [CATALOG_ARCHIVE, ])
]

WORKFLOWS_TO_UPDATE = {
    "bika_ar_workflow": {
        "permissions": (),
        "states": {
            "published": {
                "transitions": ["archive"]
            },
            "rejected": {
                "transitions": ["archive"]
            },
            "cancelled": {
                "transitions": ["archive"]
            },
            "invalid": {
                "transitions": ["archive"]
            },
        },
        "transitions": {
            "archive": {
                "title": _("Archive"),
                "new_state": "",
                "guard": {
                    "guard_permissions": permissions.TransitionArchive,
                    "guard_roles": "",
                    "guard_expr": "python:here.guard_handler('archive')",
                }
            },
        }
    }
}


def setup_handler(context):
    """Generic setup handler
    """
    if context.readDataFile('senaite.archive.install.txt') is None:
        return

    logger.info("setup handler [BEGIN]".format(PRODUCT_NAME.upper()))
    portal = context.getSite() # noqa

    # Setup workflows
    setup_workflows()

    # Portal folders
    add_portal_folders(portal)

    # Setup catalogs
    setup_catalogs(portal)

    logger.info("{} setup handler [DONE]".format(PRODUCT_NAME.upper()))


def pre_install(portal_setup):
    """Runs before the first import step of the *default* profile
    This handler is registered as a *pre_handler* in the generic setup profile
    :param portal_setup: SetupTool
    """
    logger.info("{} pre-install handler [BEGIN]".format(PRODUCT_NAME.upper()))
    context = portal_setup._getImportContext(PROFILE_ID)  # noqa
    portal = context.getSite()

    # Only install senaite.lims once!
    qi = portal.portal_quickinstaller
    if not qi.isProductInstalled("senaite.lims"):
        profile_name = "profile-senaite.lims:default"
        portal_setup.runAllImportStepsFromProfile(profile_name)

    logger.info("{} pre-install handler [DONE]".format(PRODUCT_NAME.upper()))


def post_install(portal_setup):
    """Runs after the last import step of the *default* profile
    This handler is registered as a *post_handler* in the generic setup profile
    :param portal_setup: SetupTool
    """
    logger.info("{} install handler [BEGIN]".format(PRODUCT_NAME.upper()))
    context = portal_setup._getImportContext(PROFILE_ID)  # noqa
    portal = context.getSite()  # noqa

    logger.info("{} install handler [DONE]".format(PRODUCT_NAME.upper()))


def post_uninstall(portal_setup):
    """Runs after the last import step of the *uninstall* profile
    This handler is registered as a *post_handler* in the generic setup profile
    :param portal_setup: SetupTool
    """
    logger.info("{} uninstall handler [BEGIN]".format(PRODUCT_NAME.upper()))
    context = portal_setup._getImportContext(UNINSTALL_ID)  # noqa
    portal = context.getSite()  # noqa

    # Remove entries from configuration registry
    registry_id = "{}.archive_base_path".format(PRODUCT_NAME)
    ploneapi.portal.set_registry_record(registry_id, u"")

    # Remove portal folders
    del_portal_folders(portal)

    logger.info("{} uninstall handler [DONE]".format(PRODUCT_NAME.upper()))


def setup_workflows():
    """Setup workflow customizations for this add-on
    """
    logger.info("Setting up workflows ...")
    for wf_id, settings in WORKFLOWS_TO_UPDATE.items():
        update_workflow(wf_id, settings)
    logger.info("Setting up workflows [DONE]")


def update_workflow(workflow_id, settings):
    """Updates an existing workflow with the workflow_id passed-in with the
    provided settings
    """
    logger.info("Updating workflow '{}' ...".format(workflow_id))
    wf_tool = api.get_tool("portal_workflow")
    workflow = wf_tool.getWorkflowById(workflow_id)
    if not workflow:
        logger.warn("Workflow '{}' not found [SKIP]".format(workflow_id))
    states = settings.get("states", {})
    for state_id, values in states.items():
        update_workflow_state(workflow, state_id, values)

    transitions = settings.get("transitions", {})
    for transition_id, values in transitions.items():
        update_workflow_transition(workflow, transition_id, values)


def update_workflow_state(workflow, status_id, settings):
    logger.info("Updating workflow '{}', status: '{}' ..."
                .format(workflow.id, status_id))

    # Create the status (if does not exist yet)
    new_status = workflow.states.get(status_id)
    if not new_status:
        workflow.states.addState(status_id)
        new_status = workflow.states.get(status_id)

    # Set basic info (title, description, etc.)
    new_status.title = settings.get("title", new_status.title)
    new_status.description = settings.get("description", new_status.description)

    # Set transitions
    trans = settings.get("transitions", [])
    if isinstance(trans, tuple):
        # Overwrite transitions
        new_status.transitions = trans
    elif isinstance(trans, list):
        # Keep existing transitions
        trans.extend(new_status.transitions)
        new_status.transitions = tuple(set(trans))

    # Set permissions
    update_workflow_state_permissions(workflow, new_status, settings)


def update_workflow_state_permissions(workflow, status, settings):
    # Copy permissions from another state?
    permissions_copy_from = settings.get("permissions_copy_from", None)
    if permissions_copy_from:
        logger.info("Copying permissions from '{}' to '{}' ..."
                    .format(permissions_copy_from, status.id))
        copy_from_state = workflow.states.get(permissions_copy_from)
        if not copy_from_state:
            logger.info("State '{}' not found [SKIP]".format(copy_from_state))
        else:
            for perm_id in copy_from_state.permissions:
                perm_info = copy_from_state.getPermissionInfo(perm_id)
                acquired = perm_info.get("acquired", 1)
                roles = perm_info.get("roles", acquired and [] or ())
                logger.info("Setting permission '{}' (acquired={}): '{}'"
                            .format(perm_id, repr(acquired), ', '.join(roles)))
                status.setPermission(perm_id, acquired, roles)

    # Override permissions
    logger.info("Overriding permissions for '{}' ...".format(status.id))
    state_permissions = settings.get('permissions', {})
    if not state_permissions:
        logger.info("No permissions set for '{}' [SKIP]".format(status.id))
        return
    for permission_id, roles in state_permissions.items():
        state_roles = roles and roles or ()
        if isinstance(state_roles, tuple):
            acq = 0
        else:
            acq = 1
        logger.info("Setting permission '{}' (acquired={}): '{}'"
                    .format(permission_id, repr(acq), ', '.join(state_roles)))
        status.setPermission(permission_id, acq, state_roles)


def update_workflow_transition(workflow, transition_id, settings):
    logger.info("Updating workflow '{}', transition: '{}'"
                .format(workflow.id, transition_id))
    if transition_id not in workflow.transitions:
        workflow.transitions.addTransition(transition_id)
    transition = workflow.transitions.get(transition_id)
    transition.setProperties(
        title=settings.get("title"),
        new_state_id=settings.get("new_state"),
        after_script_name=settings.get("after_script", ""),
        actbox_name=settings.get("action", settings.get("title"))
    )
    guard = transition.guard or Guard()
    guard_props = {"guard_permissions": "",
                   "guard_roles": "",
                   "guard_expr": ""}
    guard_props = settings.get("guard", guard_props)
    guard.changeFromProperties(guard_props)
    transition.guard = guard


def add_portal_folders(portal):
    """Adds the archive-specific portal folders
    """
    logger.info("Adding portal folders ...")
    for folder_id, folder_name, portal_type in PORTAL_FOLDERS:
        add_obj(portal, folder_id, folder_name, portal_type)
    logger.info("Adding portal folders [DONE]")


def del_portal_folders(portal):
    """Remove archive-specific portal folders
    """
    logger.info("Removing portal folders ...")
    portal_path = api.get_path(portal)
    for folder_id, folder_name, portal_type in PORTAL_FOLDERS:
        if portal.get(folder_id):
            logger.info("Removing: {}/{}".format(portal_path, folder_id))
            portal._delObject(folder_id)

    logger.info("Removing portal folders [DONE]")


def add_obj(container, obj_id, obj_name, obj_type):
    """Adds an object into the given container
    """
    pt = api.get_tool("portal_types")
    ti = pt.getTypeInfo(container)

    # get the current allowed types for the object
    allowed_types = ti.allowed_content_types

    def show_in_nav(obj):
        if hasattr(obj, "setExpirationDate"):
            obj.setExpirationDate(None)
        if hasattr(obj, "setExcludeFromNav"):
            obj.setExcludeFromNav(False)

    if container.get(obj_id):
        # Object already exists
        obj = container.get(obj_id)
        show_in_nav(obj)
        return

    path = api.get_path(container)
    logger.info("Adding: {}/{}".format(path, obj_id))

    # append the allowed type
    ti.allowed_content_types = allowed_types + (obj_type, )

    # Create the object
    obj = container.invokeFactory(obj_type, obj_id, title=obj_name)
    show_in_nav(obj)

    # reset the allowed content types
    ti.allowed_content_types = allowed_types


def setup_catalogs(portal):
    """Setup Plone catalogs
    """
    logger.info("Setup Catalogs ...")
    to_catalog = {}
    to_reindex = {}

    # Assign catalogs by type (additive only)
    at = api.get_tool("archetype_tool")
    for portal_type, catalogs in CATALOGS_BY_TYPE:
        existing = at.getCatalogsByType(portal_type)
        existing = map(lambda cat: cat.id, existing)
        missing = filter(lambda cat: cat not in existing, catalogs)
        if missing:
            # Assign the type to the catalogs while preserving the order
            existing.extend(missing)
            at.setCatalogsByType(portal_type, existing)
            # Keep track of the types that need to be catalogued
            for cat_id in missing:
                types = list(set(to_catalog.get(cat_id, [])+[portal_type, ]))
                to_catalog[cat_id] = types

    # Setup catalog indexes
    logger.info("Setup indexes ...")
    for catalog_id, name, meta_type in INDEXES:
        catalog = api.get_tool(catalog_id)
        if name in catalog.indexes():
            logger.info("Index '{}' already in '{}'".format(name, catalog_id))
            continue

        logger.info("Adding index '{}' to '{}'".format(name, catalog_id))
        catalog.addIndex(name, meta_type)

        # Add the indexes to be re-indexed for this catalog
        to_reindex.setdefault(catalog_id, []).append(name)

    # Setup catalog metadata columns
    logger.info("Setup metadata columns ...")
    for catalog_id, name in COLUMNS:
        catalog = api.get_tool(catalog_id)
        if name in catalog.schema():
            logger.info("Column '{}' already in '{}'".format(name, catalog_id))
            continue

        logger.info("Adding column '{}' to '{}'".format(name, catalog_id))
        catalog.addColumn(name)

        # We need to re-catalog whole objects, not only some indexes
        to_reindex.update({catalog_id: []})

    # Catalog objects to newly-assigned catalogs
    for catalog_id, portal_types in to_catalog.items():
        if not portal_types:
            continue
        types = ", ".join(portal_types)
        logger.info("Cataloguing {}: {} ...".format(catalog_id, types))
        query = {"portal_type": portal_types}
        brains = api.search(query, "uid_catalog")
        re_catalog(brains, catalog_id)

    # Re-index objects in already-assigned catalogs
    for catalog_id, indexes in to_reindex.items():
        if indexes:
            # We only need to re-index
            brains = api.search({}, catalog_id)
            re_catalog(brains, catalog_id, idxs=indexes, update_meta=0)
        else:
            # We need to re-catalog the whole object
            brains = api.search({}, catalog_id)
            re_catalog(brains, catalog_id)

    logger.info("Setup Catalogs [DONE]")


def re_catalog(brains, catalog_id, idxs=None, update_meta=1):
    cat = api.get_tool(catalog_id)
    total = len(brains)
    for num, brain in enumerate(brains):
        if num % 1000 == 0:
            logger.info(
                "Cataloguing {}: {}/{}".format(catalog_id, num, total))

        if num > 0 and num % 10000 == 0:
            portal = api.get_portal()
            commit_transaction(portal)

        # Catalog the object
        obj = api.get_object(brain)
        obj_url = api.get_path(obj)
        cat.catalog_object(obj, obj_url, idxs=idxs, update_metadata=update_meta)

        # Flush the object from memory
        obj._p_deactivate()


def commit_transaction(portal):
    start = time.time()
    logger.info("Commit transaction ...")
    transaction.commit()
    end = time.time()
    logger.info("Commit transaction ... Took {:.2f}s [DONE]"
                .format(end - start))
