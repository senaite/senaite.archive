# -*- coding: utf-8 -*-
from bika.lims import api
from senaite.archive import logger
from senaite.archive.config import PRODUCT_NAME
from senaite.archive.config import PROFILE_ID
from bika.lims.upgrade import upgradestep
from bika.lims.upgrade.utils import UpgradeUtils

version = "1.0.1"


@upgradestep(PRODUCT_NAME, version)
def upgrade(tool):
    portal = tool.aq_inner.aq_parent
    setup = portal.portal_setup
    ut = UpgradeUtils(portal)
    ver_from = ut.getInstalledVersion(PRODUCT_NAME)

    if ut.isOlderVersion(PRODUCT_NAME, version):
        logger.info("Skipping upgrade of {0}: {1} > {2}".format(
            PRODUCT_NAME, ver_from, version))
        return True

    logger.info("Upgrading {0}: {1} -> {2}".format(PRODUCT_NAME, ver_from, version))

    logger.info("{0} upgraded to version {1}".format(PRODUCT_NAME, version))


def setup_archive_workflow(tool):
    """Updates archive folder permissions, so access is granted to lab
    personnel only
    """
    logger.info("Setup archive workflow ...")
    portal = tool.aq_inner.aq_parent
    setup = portal.portal_setup

    # import worklow
    setup.runImportStepFromProfile(PROFILE_ID, "workflow")

    # update role mappings
    wf_tool = api.get_tool("portal_workflow")
    wf = wf_tool.getWorkflowById("senaite_archive_workflow")
    portal = api.get_portal()
    archive = portal.get("archive")
    wf.updateRoleMappingsFor(archive)

    logger.info("Setup archive workflow [DONE]")
