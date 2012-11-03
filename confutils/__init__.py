# -*- coding: utf-8 -*-
# This code is distributed under the two-clause BSD license.
# Copyright (c) 2012 Raphaël Barrois

from __future__ import unicode_literals

__author__ = "Raphaël Barrois <raphael.barrois+confutils@polytechnique.org>"
__version__ = '0.3.6'

from .configfile import ConfigFile, ConfigLine, Parser
from .configfile import ConfigError, ConfigReadingError, ConfigWritingError
from .merged_config import Default, NoDefault
from .merged_config import NormalizedDict, DictNamespace, MergedConfig
