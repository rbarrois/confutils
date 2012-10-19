# -*- coding: utf-8 -*-
# This code is distributed under the LGPLv3+ license.
# Copyright (c) 2012 Raphaël Barrois


from __future__ import unicode_literals


"""Handle reading a configuration file in our manner.

This is a slight deviation from the 'configparser' module, since we have
unusual keys: "foo and bar: baz".
"""


import os
import re


class ConfigLine(object):
    """Description of a configuration line.

    Provides (key, value) based comparison, hash.

    Attributes:
        key (str): the key
        value (object): the value
    """

    def __init__(self, key, value):
        self.key = key
        self.value = value

    def __eq__(self, other):
        if not isinstance(other, ConfigLine):
            return NotImplemented
        return self.key == other.key and self.value == other.value

    def same_key(self, other):
        return self.key == other.key

    def __hash__(self):
        return hash((self.key, self.value))

    def __str__(self):
        return '%s: %r' % (self.key, self.value)

    def __repr__(self):
        return 'ConfigLine(%r, %r)' % (self.key, self.value)


class ConfigReadingError(Exception):
    pass


class BaseSection(object):
    def __init__(self, name):
        self.name = name
        self.entries = dict()
        self.lines = []

    def _add_line(self, key, value):
        self.lines.append(ConfigLine(key, value))

    def _add_entry(self, key, value):
        raise NotImplementedError()

    def __setitem__(self, key, value):
        self._add_line(key, value)
        self._add_entry(key, value)

    def __iter__(self):
        return iter(self.items())

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.name)


class MultiValuedSection(BaseSection):
    """A section where each key may appear more than once."""

    def _add_entry(self, key, value):
        self.entries.setdefault(key, []).append(value)

    def items(self):
        for key, values in self.entries.items():
            for value in values:
                yield key, value


class SingleValuedSection(BaseSection):
    def _add_entry(self, key, value):
        self.entries[key] = value

    def items(self):
        return self.entries.items()


class ConfigReader(object):
    re_section_header = re.compile(r'^\[[\w._-]+\]$')
    re_blank_line = re.compile(r'^(#.*)?$')
    re_normal_line = re.compile(r'^([^:=]+)[:=](.*)$')

    def __init__(self, multi_valued_sections=()):
        self.sections = {}
        self.multi_valued_sections = multi_valued_sections
        self.current_section = self['core']

    def __getitem__(self, section_name):
        try:
            return self.sections[section_name]
        except KeyError:
            if section_name in self.multi_valued_sections:
                section = MultiValuedSection(section_name)
            else:
                section = SingleValuedSection(section_name)
            self.sections[section_name] = section
            return section

    def __iter__(self):
        return iter(self.sections)

    def enter_section(self, name):
        self.current_section = self[name]
        return self.current_section

    def parse_file(self, filename, skip_unreadable=False):
        """Parse a file from its name (instead of fds).

        If skip_unreadable is False and the file can't be read, will raise a
        ConfigReadingError.
        """
        if not os.access(filename, os.R_OK):
            if skip_unreadable:
                return
            raise ConfigReadingError("Unable to open file %s." % filename)
        with open(filename, 'rt') as f:
            return self.parse(f, name_hint=filename)


    def parse(self, f, name_hint=''):
        self.enter_section('core')

        for lineno, line in enumerate(f):
            line = line.strip()
            if self.re_section_header.match(line):
                section_name = line[1:-1]
                self.enter_section(section_name)
            elif self.re_blank_line.match(line):
                continue
            else:
                match = self.re_normal_line.match(line)
                if not match:
                    raise ConfigSyntaxError("Invalid line %r at %s:%d" % (
                        line, name_hint or f, lineno))

                key, value = match.groups()
                self.current_section[key.strip()] = value.strip()

    def __repr__(self):
        return '<%s: %r>' % (self.__class__.__name__, self.sections)
