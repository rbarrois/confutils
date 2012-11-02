# -*- coding: utf-8 -*-
# This code is distributed under the two-clause BSD license.
# Copyright (c) 2012 Raphaël Barrois

import sys

from confutils.compat import *

if sys.version_info[0] <= 2 and sys.version_info[1] < 7:  # pragma: no cover
    import unittest2 as unittest
    import StringIO as io
else:  # pragma: no cover
    import unittest
    import io

