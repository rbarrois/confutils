# -*- coding: utf-8 -*-
# This code is distributed under the LGPLv3+ license.
# Copyright (c) 2012 Raphaël Barrois

from __future__ import unicode_literals

__author__ = "Raphaël Barrois <raphael.barrois+confutils@polytechnique.org>"
__version__ = '0.1.0'

from .configreader import ConfigReader
from .merged_config import Default, NoDefault
from .merged_config import NormalizedDict, DictNamespace, MergedConfig
