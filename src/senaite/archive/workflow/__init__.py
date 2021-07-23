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

from zope.interface import implementer

from bika.lims.interfaces import IGuardAdapter


def TransitionEventHandler(before_after, obj, mod, event): # noqa lowercase
    if not event.transition:
        return

    function_name = "{}_{}".format(before_after, event.transition.id)
    if hasattr(mod, function_name):
        # Call the function from events package
        getattr(mod, function_name)(obj)


@implementer(IGuardAdapter)
class BaseGuardAdapter(object):

    def __init__(self, context):
        self.context = context

    def get_module(self):
        raise NotImplementedError("To be implemented by child classes")

    def guard(self, action):
        func_name = "guard_{}".format(action)
        module = self.get_module()
        func = getattr(module, func_name, None)
        if func:
            return func(self.context)
        return True
