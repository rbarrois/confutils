# -*- coding: utf-8 -*-
# This code is distributed under the LGPLv3+ license.
# Copyright (c) 2012 Raphaël Barrois

import sys


Py3 = (sys.version_info[0] == 3)

if Py3:  # pragma: no cover
    def iteritems(d):
        return d.items()

else:  # pragma: no cover
    def iteritems(d):
        return d.iteritems()
