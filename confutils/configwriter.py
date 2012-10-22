# -*- coding: utf-8 -*-
# This code is distributed under the LGPLv3+ license.
# Copyright (c) 2012 Raphaël Barrois

from __future__ import absolute_import, unicode_literals

import re


class Lexer(object):
    """Lex file lines into ConfigLine objects."""
    re_section_header = re.compile(r'^\[([\w._-]+)\]\s*(#.*)?$')
    re_blank_line = re.compile(r'^\s*(#.*)?$')
    re_data_line = re.compile(r'^([^:=]+)[:=](.*)$')

    def parse(self, lines):
        for rank, line in enumerate(lines):
            yield self.parse_line(line, rank=rank)

    def parse_line(self, line, rank=0):
        header_match = self.re_section_header.match(line)
        if header_match:
            header = header_match.groups()[0]
            return ConfigLine(ConfigLine.KIND_HEADER, header=header, text=line)

        data_match = self.re_data_line.match(line)
        if data_match:
            key, value = data_match.groups()
            return ConfigLine(ConfigLine.KIND_DATA, key=key.strip(),
                    value=value.strip(), text=line)

        blank_match = self.re_blank_line.match(line)
        if blank_match:
            return ConfigLine(ConfigLine.KIND_BLANK, text=line)

        raise ValueError("Invalid line %s at %s" % (line, rank))


class ConfigLine(object):
    """A simple config line."""
    KIND_BLANK = 0
    KIND_HEADER = 1
    KIND_DATA = 2

    def __init__(self, kind, text='', key=None, value=None, header=None):
        self.kind = kind
        self.key = key
        self.value = value
        self.header = header
        self.text = text
        if not self.text:
            self.text = str(self)

    def match(self, other):
        if other.kind != self.kind:
            return False
        if self.kind == self.KIND_DATA:
            return self.key == other.key and (other.value is None or other.value == self.value)
        elif self.kind == self.KIND_HEADER:
            return self.header == other.header
        else:
            return self.text.strip() == other.text.strip()

    def __str__(self):
        if self.kind == self.KIND_DATA:
            return '%s: %s' % (self.key, self.value)
        elif self.kind == self.KIND_HEADER:
            return '[%s]' % self.header
        else:
            return self.text

    def __repr__(self):
        return 'ConfigLine(%r, %r, key=%r, value=%r, header=%r)' % (self.kind,
                self.text, self.key, self.value, self.header)

    def __eq__(self, other):
        if not isinstance(other, ConfigLine):
            return NotImplemented

        return ((self.kind, self.text, self.key, self.value, self.header)
            == (other.kind, other.text, other.key, other.value, other.header))

    def __hash__(self):
        return hash((self.kind, self.text, self.key, self.value, self.header))


class ConfigLineList(object):
    """A list of ConfigLine."""
    def __init__(self, *lines):
        self.lines = list(lines)

    def append(self, line):
        self.lines.append(line)

    def find_lines(self, line):
        """Find all lines matching a given line."""
        for other_line in self.lines:
            if other_line.match(line):
                yield other_line

    def remove(self, line):
        old_len = len(self.lines)
        self.lines = [l for l in self.lines if not l.match(line)]
        return old_len - len(self.lines)

    def update(self, old_line, new_line, once=False):
        """Replace all lines matching `old_line` with `new_line`.

        If ``once`` is set to True, remove only the first instance.
        """
        nb = 0
        for i, line in enumerate(self.lines):
            if line.match(old_line):
                self.lines[i] = new_line
                nb += 1
                if once:
                    return nb
        return nb

    def __contains__(self, line):
        return any(self.find_lines(line))

    def __bool__(self):
        return bool(self.lines)

    __nonzero__ = __bool__

    def __len__(self):
        return len(self.lines)

    def __iter__(self):
        return iter(self.lines)

    def __eq__(self, other):
        if not isinstance(other, ConfigLineList):
            return NotImplemented
        return self.lines == other.lines

    def __hash__(self):
        return hash((self.__class__, tuple(self.lines)))

    def __repr__(self):
        return 'ConfigLineList(%r)' % self.lines


class SectionBlock(ConfigLineList):
    """A section block.

    A section's content may be spread across many such blocks in the file.
    """
    def __init__(self, name, *args):
        self.name = name
        super(SectionBlock, self).__init__(*args)

    def header_line(self):
        return ConfigLine(ConfigLine.KIND_HEADER, header=self.name,
                text='[%s]' % self.name)

    def __repr__(self):
        return 'SectionBlock(%r, %r)' % (self.name, self.lines)


class Section(object):
    """A section.

    A section has a ``name`` and lines spread around the file.
    """
    def __init__(self, name):
        self.name = name
        self.blocks = []
        self.extra_block = None

    def new_block(self, **kwargs):
        block = SectionBlock(self.name, **kwargs)
        self.blocks.append(block)
        return block

    def find_block(self, line):
        """Find the first block containing a line."""
        for block in self.blocks:
            if line in block:
                return block

    def find_lines(self, line):
        for block in self.blocks:
            for block_line in block:
                if block_line.match(line):
                    yield block_line

    def insert(self, line):
        block = self.find_block(line)
        if not block:
            if self.blocks:
                block = self.blocks[-1]
            else:
                block = self.extra_block = self.new_block()
        block.append(line)
        return block

    def update(self, old_line, new_line, once=False):
        """Replace all lines matching `old_line` with `new_line`.

        If ``once`` is set to True, remove only the first instance.
        """
        nb = 0
        for block in self.blocks:
            nb += block.update(old_line, new_line, once=once)
            if nb and once:
                return nb
        return nb

    def remove(self, line):
        """Delete all lines matching the given line."""
        nb = 0
        for block in self.blocks:
            nb += block.remove(line)

        return nb

    def __iter__(self):
        return iter(self.blocks)

    def __repr__(self):
        return '<Section: %s>' % self.name


class ConfigFile(object):
    """A (hopefully writable) config file.

    Attributes:
        sections (dict(name => Section)): sections of the file
        blocks (SectionBlock list): blocks from the file
        header (ConfigLineList): list of lines before the first section
        current_block (SectionBlock): current block being read
    """

    def __init__(self):
        self.sections = dict()
        self.blocks = []
        self.header = ConfigLineList()
        self.current_block = None

    def _get_section(self, name, create=True):
        """Retrieve a section by name. Create it on first access."""
        try:
            return self.sections[name]
        except KeyError:
            if not create:
                raise

            section = Section(name)
            self.sections[name] = section
            return section

    # Accessing values
    # ================

    def get_line(self, section, line):
        """Retrieve all lines compatible with a given line."""
        try:
            section = self._get_section(section, create=False)
        except KeyError:
            return []
        return section.find_lines(line)

    # Filling from lines
    # ==================

    def enter_block(self, name):
        """Mark 'entering a block'."""
        section = self._get_section(name)
        block = self.current_block = section.new_block()
        self.blocks.append(block)
        return block

    def insert_line(self, line):
        """Insert a new line"""
        if self.current_block is not None:
            self.current_block.append(line)
        else:
            self.header.append(line)

    def handle_line(self, line):
        """Read one line."""
        if line.kind == ConfigLine.KIND_HEADER:
            self.enter_block(line.header)
        else:
            self.insert_line(line)

    # Updating config content
    # =======================

    def add_line(self, section, line):
        """Insert a new line within a section.

        Returns the SectionBlock containing that new line.
        """
        return self._get_section(section).insert(line)

    def update_line(self, section, old_line, new_line, once=False):
        """Replace all lines matching `old_line` with `new_line`.

        If ``once`` is set to True, remove only the first instance.

        Returns:
            int: the number of updates performed
        """
        try:
            s = self._get_section(section, create=False)
        except KeyError:
            return 0
        return s.update(old_line, new_line, once=once)

    def remove_line(self, section, line):
        """Remove all instances of a line.

        Returns:
            int: the number of lines removed
        """
        try:
            s = self._get_section(section, create=False)
        except KeyError:
            # No such section, skip.
            return 0

        return s.remove(line)

    # High-level API
    # ==============

    def _make_line(self, key, value=None):
        return ConfigLine(ConfigLine.KIND_DATA, key=key, value=value)

    def get(self, section, key):
        line = self._make_line(key)
        return self.get_line(section, line)

    def add(self, section, key, value):
        line = self._make_line(key, value)
        return self.add_line(section, line)

    def add_or_update(self, section, key, value):
        """Update the key or, if no previous value existed, add it.

        Returns:
            int: Number of updated lines.
        """
        updates = self.update(section, key, value)
        if updates == 0:
            self.add(section, key, value)
        return updates

    def update(self, section, key, new_value, old_value=None, once=False):
        old_line = self._make_line(key, old_value)
        new_line = self._make_line(key, new_value)
        return self.update_line(section, old_line, new_line, once=once)

    def remove(self, section, key, value=None):
        line = self._make_line(key, value)
        return self.remove_line(section, line)

    # Regenerating file
    # =================

    def __iter__(self):
        for line in self.header:
            yield line
        for block in self.blocks:
            yield block.header_line()
            for line in block:
                yield line

        for section in self.sections.values():
            if section.extra_block:
                yield section.extra_block.header_line()
                for line in section.extra_block:
                    yield line
