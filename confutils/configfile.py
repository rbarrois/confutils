# -*- coding: utf-8 -*-
# This code is distributed under the LGPLv3+ license.
# Copyright (c) 2012 Raphaël Barrois

from __future__ import absolute_import, unicode_literals

import os
import re

from . import compat
from . import helpers


class ConfigError(Exception):
    """Base exception for ConfigFile-related errors."""


class ConfigReadingError(ConfigError):
    """Errors encountered when reading a file."""


class ConfigWritingError(ConfigError):
    """Errors encountered when writing a config file."""


class Parser(object):
    """Lex file lines into ConfigLine objects."""
    re_section_header = re.compile(r'^\[([\w._-]+)\]\s*(#.*)?$')
    re_blank_line = re.compile(r'^\s*(#.*)?$')
    re_data_line = re.compile(r'^([^:=]+)[:=](.*)$')

    def parse(self, lines, name_hint=''):
        for rank, line in enumerate(lines):
            yield self.parse_line(line.rstrip('\n'), rank=rank, name_hint=name_hint)

    def parse_line(self, line, rank=0, name_hint=''):
        blank_match = self.re_blank_line.match(line)
        if blank_match:
            return ConfigLine(ConfigLine.KIND_BLANK, text=line)

        header_match = self.re_section_header.match(line)
        if header_match:
            header = header_match.groups()[0]
            return ConfigLine(ConfigLine.KIND_HEADER, header=header, text=line)

        data_match = self.re_data_line.match(line)
        if data_match:
            key, value = data_match.groups()
            return ConfigLine(ConfigLine.KIND_DATA, key=key.strip(),
                    value=value.strip(), text=line)

        raise ValueError("Invalid line %s at %s:%d" % (line, name_hint, rank))


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


class BaseSectionView(helpers.DictMixin):
    """Expose a section as a dict.

    Attributes:
        configfile (ConfigFile): the underlying configfile
        name (str): the name of the section
    """
    def __init__(self, configfile, name):
        self.configfile = configfile
        self.name = name

    def add(self, key, value):
        """Add a new value for a key."""
        self[key] = value

    def __repr__(self):
        return '<%s: %r->%s>' % (self.__class__.__name__,
            self.configfile, self.name)


class SingleValuedSectionView(BaseSectionView):

    def __getitem__(self, key):
        return self.configfile.get_one(self.name, key)

    def __setitem__(self, key, value):
        self.configfile.add_or_update(self.name, key, value)

    def __delitem__(self, key):
        removed = self.configfile.remove(self.name, key)
        if not removed:
            raise KeyError("No line matching %r in %r" % (key, self))

    def iteritems(self):
        d = dict(self.configfile.items(self.name))
        return d.items()


class MultiValuedSectionView(BaseSectionView):
    """A SectionView where each key may have multiple values.

    Always provide the list of expected values when setting.
    """
    def __getitem__(self, key):
        entries = list(self.configfile.get(self.name, key))
        if not entries:
            raise KeyError("No value defined for key %r in %r" % (key, self))
        return entries

    def __setitem__(self, key, values):
        old_values = frozenset(self.get(key, []))
        new_values = frozenset(values)
        for removed in old_values - new_values:
            self.configfile.remove(self.name, key, removed)
        for added in new_values - old_values:
            self.configfile.add(self.name, key, added)

    def add(self, key, value):
        """Add a new value for a key.

        This differs from __setitem__ in adding a new value instead of updating
        the list of values, thus avoiding the need to fetch the previous list of
        values.
        """
        self.configfile.add(self.name, key, value)

    def __delitem__(self, key):
        removed = self.configfile.remove(self.name, key)
        if not removed:
            raise KeyError("No value defined for key %r in %r" % (key, self))

    def iteritems(self):
        d = dict()
        for k, v in self.configfile.items(self.name):
            d.setdefault(k, []).append(v)
        return compat.iteritems(d)


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

    def __contains__(self, name):
        """Check whether a given name is a known section."""
        return name in self.sections

    # Accessing values
    # ================

    def get_line(self, section, line):
        """Retrieve all lines compatible with a given line."""
        try:
            section = self._get_section(section, create=False)
        except KeyError:
            return []
        return section.find_lines(line)

    def iter_lines(self, section):
        """Iterate over all lines in a section.

        This will skip 'header' lines.
        """
        try:
            section = self._get_section(section, create=False)
        except KeyError:
            return

        for block in section:
            for line in block:
                yield line

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

    def parse(self, fileobj, name_hint='', parser=None):
        """Fill from a file-like object."""
        self.current_block = None  # Reset current block
        parser = parser or Parser()
        for line in parser.parse(fileobj, name_hint=name_hint):
            self.handle_line(line)

    def parse_file(self, filename, skip_unreadable=False, **kwargs):
        """Parse a file from its name (instead of fds).

        If skip_unreadable is False and the file can't be read, will raise a
        ConfigReadingError.
        """
        if not os.access(filename, os.R_OK):
            if skip_unreadable:
                return
            raise ConfigReadingError("Unable to open file %s." % filename)
        with open(filename, 'rt') as f:
            return self.parse(f, name_hint=filename, **kwargs)

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

    def items(self, section):
        """Retrieve all key/value pairs for a given section."""
        for line in self.iter_lines(section):
            if line.kind == ConfigLine.KIND_DATA:
                yield line.key, line.value

    def get(self, section, key):
        """Return the 'value' of all lines matching the section/key.

        Yields:
            values for matching lines.
        """
        line = self._make_line(key)
        for line in self.get_line(section, line):
            yield line.value

    def get_one(self, section, key):
        """Retrieve the first value for a section/key.

        Raises:
            KeyError: If no line match the given section/key.
        """
        lines = iter(self.get(section, key))
        try:
            return next(lines)
        except StopIteration:
            raise KeyError("Key %s not found in %s" % (key, section))

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

    # Views
    # =====

    def section_view(self, section, multi_value=False):
        view_class = MultiValuedSectionView if multi_value else SingleValuedSectionView
        return view_class(self, section)

    # Regenerating file
    # =================

    def __iter__(self):
        # First, the header
        for line in self.header:
            yield line

        # Then the content of blocks
        for block in self.blocks:
            if not block:
                # Empty, skip
                continue

            yield block.header_line()
            for line in block:
                yield line

        # Finally, extra block lines
        for section in self.sections.values():
            if section.extra_block:
                yield section.extra_block.header_line()
                for line in section.extra_block:
                    yield line

    def write(self, fd):
        """Write to an open file-like object."""
        for line in self:
            fd.write('%s\n' % line.text)
