# -*- coding: utf-8 -*-
# This code is distributed under the two-clause BSD license.
# Copyright (c) 2012 Raphaël Barrois

from __future__ import unicode_literals

import tempfile

from .compat import io
from .compat import unittest

from confutils import configfile


class LineTestCase(unittest.TestCase):
    def test_compare_other(self):
        l = configfile.ConfigLine(configfile.ConfigLine.KIND_BLANK, '# x')
        self.assertFalse(l == '# x')
        self.assertFalse('# x' == l)

    def test_blank(self):
        """Test 'blank' lines."""
        l = configfile.ConfigLine(configfile.ConfigLine.KIND_BLANK, '# foo')
        self.assertEqual('# foo', str(l))
        self.assertTrue(l.match(l))

        l2 = configfile.ConfigLine(configfile.ConfigLine.KIND_BLANK,
                ' # foo ')
        self.assertTrue(l.match(l2))
        self.assertTrue(l2.match(l))
        self.assertNotEqual(l, l2)
        self.assertNotEqual(hash(l), hash(l2))

        l3 = configfile.ConfigLine(configfile.ConfigLine.KIND_BLANK,
                '# foo')
        self.assertEqual(l, l3)
        self.assertTrue(l.match(l3))
        self.assertTrue(l3.match(l))
        self.assertEqual(hash(l), hash(l3))

    def test_blank_notext(self):
        """Test 'blank' lines without provided text."""
        l = configfile.ConfigLine(configfile.ConfigLine.KIND_BLANK)
        self.assertEqual('', l.text)

    def test_header(self):
        """Test 'header' lines."""
        l1 = configfile.ConfigLine(configfile.ConfigLine.KIND_HEADER,
                '[foo]', header='foo')
        l2 = configfile.ConfigLine(configfile.ConfigLine.KIND_HEADER,
                '[foo] # Blah', header='foo')
        l3 = configfile.ConfigLine(configfile.ConfigLine.KIND_HEADER,
                '[foo]', header='foo')

        self.assertEqual('[foo]', str(l1))
        self.assertEqual('[foo]', str(l2))

        self.assertTrue(l1.match(l2))
        self.assertTrue(l2.match(l1))
        self.assertNotEqual(l1, l2)
        self.assertNotEqual(hash(l1), hash(l2))

        self.assertEqual(l1, l3)
        self.assertTrue(l1.match(l3))
        self.assertTrue(l3.match(l1))
        self.assertEqual(hash(l1), hash(l3))

    def test_header_notext(self):
        """Test 'header' lines without provided text."""
        l = configfile.ConfigLine(configfile.ConfigLine.KIND_HEADER,
                header='foo')
        self.assertEqual('[foo]', l.text)

    def test_data(self):
        """Test 'data' lines."""
        l1 = configfile.ConfigLine(configfile.ConfigLine.KIND_DATA,
                'foo = bar', key='foo', value='bar')
        l2 = configfile.ConfigLine(configfile.ConfigLine.KIND_DATA,
                '  foo = bar', key='foo', value='bar')
        l3 = configfile.ConfigLine(configfile.ConfigLine.KIND_DATA,
                'foo = bar', key='foo', value='bar')

        self.assertEqual("foo: bar", str(l1))
        self.assertEqual("foo: bar", str(l2))

        self.assertTrue(l1.match(l2))
        self.assertTrue(l2.match(l1))
        self.assertNotEqual(l1, l2)
        self.assertNotEqual(hash(l1), hash(l2))

        self.assertEqual(l1, l3)
        self.assertTrue(l1.match(l3))
        self.assertTrue(l3.match(l1))
        self.assertEqual(hash(l1), hash(l3))

    def test_data_notext(self):
        """Test 'data' lines without provided text."""
        l = configfile.ConfigLine(configfile.ConfigLine.KIND_DATA,
                key='foo', value='bar')
        self.assertEqual('foo: bar', l.text)

    def test_cross_compare(self):
        """Test comparisions between different kinds."""
        l1 = configfile.ConfigLine(configfile.ConfigLine.KIND_BLANK,
                '# foo')
        l2 = configfile.ConfigLine(configfile.ConfigLine.KIND_HEADER,
                '[foo]', header='foo')
        l3 = configfile.ConfigLine(configfile.ConfigLine.KIND_DATA,
                'foo = bar', key='foo', value='bar')

        self.assertEqual(3, len(set([l1, l2, l3])))

        self.assertNotEqual(l1, l2)
        self.assertNotEqual(l2, l3)
        self.assertNotEqual(l1, l3)

        self.assertNotEqual(hash(l1), hash(l2))
        self.assertNotEqual(hash(l2), hash(l3))
        self.assertNotEqual(hash(l1), hash(l3))

        self.assertFalse(l1.match(l2))
        self.assertFalse(l1.match(l3))
        self.assertFalse(l2.match(l1))
        self.assertFalse(l2.match(l3))
        self.assertFalse(l3.match(l1))
        self.assertFalse(l3.match(l2))

    def test_repr(self):
        l1 = configfile.ConfigLine(configfile.ConfigLine.KIND_BLANK,
                '# foo')
        self.assertIn('foo', repr(l1))

        l2 = configfile.ConfigLine(configfile.ConfigLine.KIND_HEADER,
                '[foo]', header='foo')
        self.assertIn('[foo]', repr(l2))

        l3 = configfile.ConfigLine(configfile.ConfigLine.KIND_DATA,
                'foo = bar', key='foo', value='bar')
        self.assertIn('foo', repr(l3))
        self.assertIn('bar', repr(l3))


class ParserTestCase(unittest.TestCase):
    def test_parse_empty_line(self):
        lexer = configfile.Parser()
        l = lexer.parse_line('')
        self.assertEqual(l.KIND_BLANK, l.kind)
        self.assertEqual('', l.text)
        self.assertIsNone(l.key)
        self.assertIsNone(l.value)
        self.assertIsNone(l.header)

    def test_parse_space_line(self):
        lexer = configfile.Parser()
        l = lexer.parse_line('  ')
        self.assertEqual(l.KIND_BLANK, l.kind)
        self.assertEqual('  ', l.text)
        self.assertIsNone(l.key)
        self.assertIsNone(l.value)
        self.assertIsNone(l.header)

    def test_parse_commented_line(self):
        lexer = configfile.Parser()
        l = lexer.parse_line(' # foo')
        self.assertEqual(l.KIND_BLANK, l.kind)
        self.assertEqual(' # foo', l.text)
        self.assertIsNone(l.key)
        self.assertIsNone(l.value)
        self.assertIsNone(l.header)

    def test_parse_alt_commented_line(self):
        lexer = configfile.Parser()
        l = lexer.parse_line('# foo: bar')
        self.assertEqual(l.KIND_BLANK, l.kind)
        self.assertEqual('# foo: bar', l.text)
        self.assertIsNone(l.key)
        self.assertIsNone(l.value)
        self.assertIsNone(l.header)

    def test_parse_data_line(self):
        lexer = configfile.Parser()
        l = lexer.parse_line('foo: bar')
        self.assertEqual(l.KIND_DATA, l.kind)
        self.assertEqual('foo: bar', l.text)
        self.assertEqual('foo', l.key)
        self.assertEqual('bar', l.value)
        self.assertIsNone(l.header)

    def test_parse_data_line_with_space(self):
        lexer = configfile.Parser()
        l = lexer.parse_line('  foo= bar')
        self.assertEqual(l.KIND_DATA, l.kind)
        self.assertEqual('  foo= bar', l.text)
        self.assertEqual('foo', l.key)
        self.assertEqual('bar', l.value)
        self.assertIsNone(l.header)

    def test_parse_data_line_with_comment(self):
        lexer = configfile.Parser()
        l = lexer.parse_line('foo: bar  # baz')
        self.assertEqual(l.KIND_DATA, l.kind)
        self.assertEqual('foo: bar  # baz', l.text)
        self.assertEqual('foo', l.key)
        self.assertEqual('bar  # baz', l.value)
        self.assertIsNone(l.header)

    def test_section_line(self):
        lexer = configfile.Parser()
        l = lexer.parse_line('[foo]')
        self.assertEqual(l.KIND_HEADER, l.kind)
        self.assertEqual('[foo]', l.text)
        self.assertIsNone(l.key)
        self.assertIsNone(l.value)
        self.assertEqual('foo', l.header)

    def test_section_line_with_space(self):
        lexer = configfile.Parser()
        l = lexer.parse_line('[foo]   ')
        self.assertEqual(l.KIND_HEADER, l.kind)
        self.assertEqual('[foo]   ', l.text)
        self.assertIsNone(l.key)
        self.assertIsNone(l.value)
        self.assertEqual('foo', l.header)

    def test_section_line_with_comment(self):
        lexer = configfile.Parser()
        l = lexer.parse_line('[foo]#bar')
        self.assertEqual(l.KIND_HEADER, l.kind)
        self.assertEqual('[foo]#bar', l.text)
        self.assertIsNone(l.key)
        self.assertIsNone(l.value)
        self.assertEqual('foo', l.header)

    def test_parse_invalid_line(self):
        lexer = configfile.Parser()
        self.assertRaises(ValueError, lexer.parse_line, ' foo')

    def test_parse_lines(self):
        lexer = configfile.Parser()
        lines = list(lexer.parse([
            '  # Initial comment',
            '[foo]  # First section',
            'x = 42',
            'y: 13',
        ]))

        self.assertEqual(lines, [
            configfile.ConfigLine(configfile.ConfigLine.KIND_BLANK,
                '  # Initial comment'),
            configfile.ConfigLine(configfile.ConfigLine.KIND_HEADER,
                '[foo]  # First section', header='foo'),
            configfile.ConfigLine(configfile.ConfigLine.KIND_DATA,
                'x = 42', key='x', value='42'),
            configfile.ConfigLine(configfile.ConfigLine.KIND_DATA,
                'y: 13', key='y', value='13'),
        ])


class ConfigLineList(unittest.TestCase):
    def setUp(self):
        self.l1 = configfile.ConfigLine(configfile.ConfigLine.KIND_HEADER,
                '[foo]', header='foo')
        self.l2 = configfile.ConfigLine(configfile.ConfigLine.KIND_DATA,
                'foo: bar', key='foo', value='bar')
        self.l3 = configfile.ConfigLine(configfile.ConfigLine.KIND_DATA,
                'baz: 42', key='baz', value='42')

    def test_init(self):
        l = configfile.ConfigLineList()
        self.assertEqual([], l.lines)

        l = configfile.ConfigLineList(self.l1, self.l2, self.l3)
        self.assertEqual([self.l1, self.l2, self.l3], l.lines)

    def test_len(self):
        l = configfile.ConfigLineList(self.l1, self.l2, self.l3)
        self.assertEqual(3, len(l))

    def test_bool(self):
        l = configfile.ConfigLineList()
        self.assertFalse(l)

        l = configfile.ConfigLineList(self.l1)
        self.assertTrue(l)

    def test_iter(self):
        l = configfile.ConfigLineList(self.l1, self.l2, self.l3)
        self.assertEqual([self.l1, self.l2, self.l3], list(l))

    def test_contains(self):
        l = configfile.ConfigLineList(self.l1, self.l2, self.l3)
        self.assertIn(self.l1, l)
        self.assertIn(self.l2, l)
        self.assertIn(self.l3, l)

        line = configfile.ConfigLine(configfile.ConfigLine.KIND_DATA,
            'foo =', key='foo')
        self.assertIn(line, l)

    def test_empty_list(self):
        l = configfile.ConfigLineList()
        self.assertEqual(0, len(l))
        self.assertNotIn(self.l1, l)

    def test_eq(self):
        l = configfile.ConfigLineList(self.l1, self.l2, self.l3)
        ll = configfile.ConfigLineList(self.l1, self.l2, self.l3)
        self.assertEqual(l, ll)

        lll = configfile.ConfigLineList(self.l1, self.l2)
        self.assertNotEqual(l, lll)

        self.assertFalse(l == [self.l1, self.l2, self.l3])

    def test_hash(self):
        l = configfile.ConfigLineList(self.l1, self.l2, self.l3)
        self.assertNotEqual(hash((self.l1, self.l2, self.l3)), hash(l))

        ll = configfile.ConfigLineList(self.l1, self.l2, self.l3)
        self.assertEqual(hash(l), hash(ll))

    def test_repr(self):
        l = configfile.ConfigLineList(self.l1, self.l2, self.l3)
        self.assertIn(repr(self.l1), repr(l))
        self.assertIn(repr(self.l2), repr(l))
        self.assertIn(repr(self.l3), repr(l))

    def test_append(self):
        l = configfile.ConfigLineList(self.l1, self.l2, self.l3)
        l.append(self.l3)
        self.assertEqual([self.l1, self.l2, self.l3, self.l3], l.lines)

    def test_remove(self):
        l = configfile.ConfigLineList(self.l1, self.l2, self.l3)
        removed = l.remove(self.l3)
        self.assertEqual(1, removed)
        self.assertEqual([self.l1, self.l2], l.lines)

    def test_remove_duplicated(self):
        l = configfile.ConfigLineList(self.l3, self.l3, self.l1, self.l3,
                self.l2, self.l3)
        removed = l.remove(self.l3)

        self.assertEqual(4, removed)
        self.assertEqual([self.l1, self.l2], l.lines)

    def test_remove_empty(self):
        l = configfile.ConfigLineList()
        self.assertEqual(0, l.remove(self.l1))
        self.assertEqual([], l.lines)

    def test_update(self):
        l = configfile.ConfigLineList(self.l1, self.l2, self.l3)
        nb_updates = l.update(self.l1, self.l2)

        self.assertEqual(1, nb_updates)
        self.assertEqual([self.l2, self.l2, self.l3], l.lines)

    def test_update_duplicated(self):
        l = configfile.ConfigLineList(self.l1, self.l3, self.l1, self.l3)
        nb_updates = l.update(self.l1, self.l2)

        self.assertEqual(2, nb_updates)
        self.assertEqual([self.l2, self.l3, self.l2, self.l3], l.lines)

    def test_update_duplicated_once(self):
        l = configfile.ConfigLineList(self.l1, self.l3, self.l1, self.l3)
        nb_updates = l.update(self.l1, self.l2, once=True)

        self.assertEqual(1, nb_updates)
        self.assertEqual([self.l2, self.l3, self.l1, self.l3], l.lines)

    def test_update_empty(self):
        l = configfile.ConfigLineList()
        nb_updates = l.update(self.l1, self.l2)

        self.assertEqual(0, nb_updates)
        self.assertEqual([], l.lines)


class SectionBlockTestCase(unittest.TestCase):
    def setUp(self):
        self.l1 = configfile.ConfigLine(configfile.ConfigLine.KIND_HEADER,
                '[foo]', header='foo')
        self.l2 = configfile.ConfigLine(configfile.ConfigLine.KIND_DATA,
                'foo: bar', key='foo', value='bar')
        self.l3 = configfile.ConfigLine(configfile.ConfigLine.KIND_DATA,
                'baz: 42', key='baz', value='42')

    def test_init(self):
        sb = configfile.SectionBlock('foo', self.l1, self.l2, self.l3)
        self.assertEqual('foo', sb.name)
        self.assertEqual([self.l1, self.l2, self.l3], list(sb))

    def test_repr(self):
        sb = configfile.SectionBlock('blah', self.l1, self.l2, self.l3)
        self.assertIn('blah', repr(sb))
        self.assertIn(repr(self.l1), repr(sb))
        self.assertIn(repr(self.l2), repr(sb))
        self.assertIn(repr(self.l3), repr(sb))

    def test_header_line(self):
        sb = configfile.SectionBlock('blah', self.l1, self.l2, self.l3)
        header = sb.header_line()
        self.assertEqual(configfile.ConfigLine.KIND_HEADER, header.kind)
        self.assertEqual('[blah]', header.text)
        self.assertEqual('blah', header.header)
        self.assertIsNone(header.key)
        self.assertIsNone(header.value)


class SectionTestCase(unittest.TestCase):
    def setUp(self):
        self.l1 = configfile.ConfigLine(configfile.ConfigLine.KIND_HEADER,
                '[foo]', header='foo')
        self.l2 = configfile.ConfigLine(configfile.ConfigLine.KIND_DATA,
                'foo: bar', key='foo', value='bar')
        self.l3 = configfile.ConfigLine(configfile.ConfigLine.KIND_DATA,
                'baz: 42', key='baz', value='42')

    def test_init(self):
        s = configfile.Section('foo')
        self.assertEqual('foo', s.name)
        self.assertEqual([], s.blocks)
        self.assertIsNone(s.extra_block)

    def test_repr(self):
        s = configfile.Section('foo')
        self.assertIn('foo', repr(s))

    def test_new_block(self):
        s = configfile.Section('foo')
        block = s.new_block()

        self.assertEqual([block], s.blocks)
        self.assertIsNone(s.extra_block)
        self.assertEqual([block], list(s))

        self.assertEqual('foo', block.name)
        self.assertEqual(0, len(block))

    def test_new_block_chain(self):
        s = configfile.Section('foo')
        block1 = s.new_block()
        block2 = s.new_block()

        self.assertEqual([block1, block2], s.blocks)
        self.assertIsNone(s.extra_block)
        self.assertEqual([block1, block2], list(s))

        self.assertEqual('foo', block1.name)
        self.assertEqual(0, len(block1))

        self.assertEqual('foo', block2.name)
        self.assertEqual(0, len(block2))

    def test_find_block_noline(self):
        s = configfile.Section('foo')
        self.assertIsNone(s.find_block(self.l1))

        block1 = s.new_block()
        self.assertIsNone(s.find_block(self.l1))

        block2 = s.new_block()
        self.assertIsNone(s.find_block(self.l1))

    def test_find_block(self):
        s = configfile.Section('foo')
        block = s.new_block()
        block.append(self.l1)
        block.append(self.l2)

        self.assertEqual(block, s.find_block(self.l2))

    def test_find_block_duplicated(self):
        s = configfile.Section('foo')
        block1 = s.new_block()
        block1.append(self.l1)

        block2 = s.new_block()
        block2.append(self.l1)
        block2.append(self.l2)
        block2.append(self.l2)

        block3 = s.new_block()
        block3.append(self.l2)

        self.assertEqual(block2, s.find_block(self.l2))

    def test_find_lines(self):
        s = configfile.Section('foo')
        block1 = s.new_block()
        block1.append(self.l1)

        block2 = s.new_block()
        block2.append(self.l1)
        block2.append(self.l2)
        block2.append(self.l2)

        block3 = s.new_block()
        block3.append(self.l2)

        lines = list(s.find_lines(self.l1))
        self.assertEqual([self.l1, self.l1], lines)

        lines = list(s.find_lines(self.l2))
        self.assertEqual([self.l2, self.l2, self.l2], lines)

        lines = list(s.find_lines(self.l3))
        self.assertEqual([], lines)

    def test_insert(self):
        s = configfile.Section('foo')
        block = s.new_block()

        target_block = s.insert(self.l1)

        self.assertEqual(block, target_block)
        self.assertEqual([block], s.blocks)
        self.assertIsNone(s.extra_block)
        self.assertEqual([self.l1], block.lines)

    def test_insert_close(self):
        """Ensure similar lines are inserted nearby."""
        s = configfile.Section('foo')
        block1 = s.new_block()
        block1.append(self.l1)

        block2 = s.new_block()
        block2.append(self.l1)
        block2.append(self.l2)

        target_block = s.insert(self.l2)

        self.assertEqual(block2, target_block)
        self.assertEqual([block1, block2], s.blocks)
        self.assertIsNone(s.extra_block)
        self.assertEqual([self.l1], block1.lines)
        self.assertEqual([self.l1, self.l2, self.l2], block2.lines)

    def test_insert_empty(self):
        s = configfile.Section('foo')
        block = s.insert(self.l1)

        self.assertEqual(block, s.extra_block)
        self.assertEqual([block], s.blocks)
        self.assertEqual([self.l1], block.lines)

    def test_update(self):
        s = configfile.Section('foo')
        block1 = s.new_block()
        block1.append(self.l1)

        block2 = s.new_block()
        block2.append(self.l1)
        block2.append(self.l2)

        nb_updates = s.update(self.l2, self.l3)

        self.assertEqual(1, nb_updates)
        self.assertEqual([block1, block2], s.blocks)
        self.assertEqual([self.l1], block1.lines)
        self.assertEqual([self.l1, self.l3], block2.lines)

    def test_update_many(self):
        s = configfile.Section('foo')
        block1 = s.new_block()
        block1.append(self.l1)

        block2 = s.new_block()
        block2.append(self.l1)
        block2.append(self.l2)

        nb_updates = s.update(self.l1, self.l3)  # once=False, default

        self.assertEqual(2, nb_updates)
        self.assertEqual([block1, block2], s.blocks)
        self.assertEqual([self.l3], block1.lines)
        self.assertEqual([self.l3, self.l2], block2.lines)

    def test_update_once(self):
        s = configfile.Section('foo')
        block1 = s.new_block()
        block1.append(self.l1)

        block2 = s.new_block()
        block2.append(self.l1)
        block2.append(self.l2)

        nb_updates = s.update(self.l1, self.l3, once=True)

        self.assertEqual(1, nb_updates)
        self.assertEqual([block1, block2], s.blocks)
        self.assertEqual([self.l3], block1.lines)
        self.assertEqual([self.l1, self.l2], block2.lines)

    def test_update_empty(self):
        s = configfile.Section('foo')
        block1 = s.new_block()
        block2 = s.new_block()

        nb_updates = s.update(self.l2, self.l3)

        self.assertEqual(0, nb_updates)
        self.assertEqual([block1, block2], s.blocks)
        self.assertEqual([], block1.lines)
        self.assertEqual([], block2.lines)

    def test_update_noblocks(self):
        s = configfile.Section('foo')

        nb_updates = s.update(self.l2, self.l3)

        self.assertEqual(0, nb_updates)
        self.assertEqual([], s.blocks)
        self.assertIsNone(s.extra_block)

    def test_remove(self):
        s = configfile.Section('foo')
        block1 = s.new_block()
        block1.append(self.l1)

        block2 = s.new_block()
        block2.append(self.l1)
        block2.append(self.l2)

        self.assertEqual(2, s.remove(self.l1))

        self.assertEqual([block1, block2], s.blocks)
        self.assertEqual([], block1.lines)
        self.assertEqual([self.l2], block2.lines)

    def test_remove_nonexistant(self):
        """Test removing an absent line."""
        s = configfile.Section('foo')
        block1 = s.new_block()
        block1.append(self.l1)

        block2 = s.new_block()
        block2.append(self.l1)
        block2.append(self.l2)

        self.assertEqual(0, s.remove(self.l3))

        self.assertEqual([block1, block2], s.blocks)
        self.assertEqual([self.l1], block1.lines)
        self.assertEqual([self.l1, self.l2], block2.lines)

    def test_remove_empty(self):
        """Test removing from an empty section."""
        s = configfile.Section('foo')
        self.assertEqual(0, s.remove(self.l1))

        self.assertIsNone(s.extra_block)
        self.assertEqual([], s.blocks)


class ConfigFileTestCase(unittest.TestCase):
    def setUp(self):
        self.l1 = configfile.ConfigLine(configfile.ConfigLine.KIND_DATA,
                key='x', value='42')
        self.l2 = configfile.ConfigLine(configfile.ConfigLine.KIND_HEADER,
                header='bar')
        self.l3 = configfile.ConfigLine(configfile.ConfigLine.KIND_DATA,
                key='x', value='13')
        self.l4 = configfile.ConfigLine(configfile.ConfigLine.KIND_DATA,
                key='x', value=None)
        self.h_foo = configfile.ConfigLine(configfile.ConfigLine.KIND_HEADER,
                header='foo')
        self.h_bar = configfile.ConfigLine(configfile.ConfigLine.KIND_HEADER,
                header='bar')

    def test_enter_block(self):
        c = configfile.ConfigFile()
        self.assertEqual([], c.blocks)
        self.assertIsNone(c.current_block)

        block = c.enter_block('foo')
        self.assertEqual([block], c.blocks)
        self.assertEqual(block, c.current_block)
        self.assertIn('foo', c.sections)
        self.assertEqual([block], c.sections['foo'].blocks)

    def test_enter_block_twice(self):
        c = configfile.ConfigFile()
        self.assertEqual([], c.blocks)
        self.assertIsNone(c.current_block)

        block1 = c.enter_block('foo')
        self.assertEqual([block1], c.blocks)
        self.assertEqual(block1, c.current_block)
        self.assertIn('foo', c.sections)
        self.assertEqual([block1], c.sections['foo'].blocks)

        block2 = c.enter_block('foo')
        self.assertEqual([block1, block2], c.blocks)
        self.assertEqual(block2, c.current_block)
        self.assertEqual([block1, block2], c.sections['foo'].blocks)

    def test_enter_block_alternate(self):
        c = configfile.ConfigFile()
        self.assertEqual([], c.blocks)
        self.assertIsNone(c.current_block)

        block1 = c.enter_block('foo')
        self.assertEqual([block1], c.blocks)
        self.assertEqual(block1, c.current_block)
        self.assertIn('foo', c.sections)
        self.assertEqual([block1], c.sections['foo'].blocks)

        block2 = c.enter_block('bar')
        self.assertEqual([block1, block2], c.blocks)
        self.assertEqual(block2, c.current_block)
        self.assertEqual([block1], c.sections['foo'].blocks)
        self.assertIn('bar', c.sections)
        self.assertEqual([block2], c.sections['bar'].blocks)

        block3 = c.enter_block('foo')
        self.assertEqual([block1, block2, block3], c.blocks)
        self.assertEqual(block3, c.current_block)
        self.assertEqual([block1, block3], c.sections['foo'].blocks)
        self.assertEqual([block2], c.sections['bar'].blocks)

    def test_insert_line_header(self):
        c = configfile.ConfigFile()
        c.insert_line(self.l1)

        self.assertEqual([], c.blocks)
        self.assertIsNone(c.current_block)
        self.assertEqual([self.l1], list(c.header))

    def test_insert_line(self):
        c = configfile.ConfigFile()
        block = c.enter_block('foo')

        c.insert_line(self.l1)

        self.assertEqual([self.l1], list(block))
        self.assertEqual([self.l1], list(c.current_block))
        self.assertEqual([], list(c.header))

    def test_handle_line_data_header(self):
        c = configfile.ConfigFile()
        c.handle_line(self.l1)

        self.assertEqual([], c.blocks)
        self.assertIsNone(c.current_block)
        self.assertEqual([self.l1], list(c.header))

    def test_handle_line_data_block(self):
        c = configfile.ConfigFile()
        block = c.enter_block('foo')

        c.handle_line(self.l1)

        self.assertEqual([self.l1], list(block))
        self.assertEqual([self.l1], list(c.current_block))
        self.assertEqual([], list(c.header))

    def test_handle_line_section_header(self):
        c = configfile.ConfigFile()
        block = c.enter_block('foo')

        c.handle_line(self.l2)

        self.assertEqual(2, len(c.blocks))
        self.assertEqual('bar', c.current_block.name)
        self.assertIn('bar', c.sections)

    def test_parse_empty(self):
        c = configfile.ConfigFile()
        c.parse([])
        self.assertEqual([], c.blocks)
        self.assertEqual({}, c.sections)
        self.assertIsNone(c.current_block)

    def test_parse_usual(self):
        c = configfile.ConfigFile()
        c.parse([
            '[foo]',
            'x: 13',
            'x: 42',
        ])
        self.assertIn('foo', c.sections)
        self.assertEqual([c.current_block], c.blocks)
        self.assertEqual([self.l3, self.l1], list(c.current_block))

    def test_parse_alternate_lexer(self):
        class MyParser(object):
            def parse(p, lines, name_hint=''):
                for line in lines:
                    yield self.l1

        c = configfile.ConfigFile()
        c.parse([
            '[foo]',
            'x: 13',
            'x: 42',
        ], parser=MyParser())
        self.assertEqual({}, c.sections)
        self.assertEqual([self.l1, self.l1, self.l1], list(c.header))

    def test_parse_file_nonexistent(self):
        c = configfile.ConfigFile()

        tmp = tempfile.NamedTemporaryFile()
        name = tmp.name
        tmp.close()

        with self.assertRaises(configfile.ConfigReadingError):
            c.parse_file(name)

    def test_parse_file_nonexistent_skip_unreadable(self):
        c = configfile.ConfigFile()

        tmp = tempfile.NamedTemporaryFile()
        name = tmp.name
        tmp.close()

        c.parse_file(name, skip_unreadable=True)
        self.assertEqual({}, c.sections)
        self.assertEqual([], c.blocks)

    def test_parse_file_existent(self):
        c = configfile.ConfigFile()
        with tempfile.NamedTemporaryFile(mode='wt') as tmp:
            tmp.write("[foo]\nx: 13\nx: 42\n")
            tmp.flush()
            c.parse_file(tmp.name)

        self.assertIn('foo', c.sections)
        self.assertEqual([c.current_block], c.blocks)
        self.assertEqual([self.l3, self.l1], list(c.current_block))

    def test_parse_files(self):
        c = configfile.ConfigFile()
        with tempfile.NamedTemporaryFile(mode='wt') as tmp1:
            tmp1.write("# Blah\n[foo]\nx: 13\nx: 42\n")
            tmp1.flush()
            c.parse_file(tmp1.name)

        with tempfile.NamedTemporaryFile(mode='wt') as tmp2:
            tmp2.write("# Bar\n[bar]\nx: 42\nx: 13\n")
            tmp2.flush()
            c.parse_file(tmp2.name)

        self.assertIn('foo', c.sections)
        self.assertIn('bar', c.sections)
        self.assertEqual(2, len(c.header))
        self.assertEqual(2, len(c.blocks))
        self.assertEqual([self.l3, self.l1], list(c.blocks[0]))
        self.assertEqual([self.l1, self.l3], list(c.blocks[1]))

    def test_get_line_undefined(self):
        c = configfile.ConfigFile()
        c.enter_block('foo')
        lines = list(c.get_line('foo', self.l1))
        self.assertEqual([], lines)

    def test_get_line_invalid_section(self):
        c = configfile.ConfigFile()
        self.assertEqual([], c.get_line('foo', self.l1))

    def test_get_line(self):
        c = configfile.ConfigFile()
        c.enter_block('foo')
        c.insert_line(self.l1)
        c.enter_block('bar')
        c.insert_line(self.l3)

        lines = list(c.get_line('foo', self.l1))
        self.assertEqual([self.l1], lines)

        lines = list(c.get_line('foo', self.l4))
        self.assertEqual([self.l1], lines)

    def test_iter_lines_empty(self):
        c = configfile.ConfigFile()
        self.assertEqual([], list(c.iter_lines('foo')))

    def test_iter_lines(self):
        c = configfile.ConfigFile()
        c.enter_block('foo')
        c.insert_line(self.l1)
        c.enter_block('bar')
        c.insert_line(self.l3)

        lines = list(c.iter_lines('foo'))
        self.assertEqual([self.l1], lines)

        lines = list(c.iter_lines('bar'))
        self.assertEqual([self.l3], lines)

    def test_iter_lines_repeated(self):
        c = configfile.ConfigFile()
        c.enter_block('foo')
        c.insert_line(self.l1)
        c.enter_block('bar')
        c.insert_line(self.l3)

        lines = list(c.iter_lines('foo'))
        self.assertEqual([self.l1], lines)

        lines = list(c.iter_lines('foo'))
        self.assertEqual([self.l1], lines)

    def test_contains_empty(self):
        c = configfile.ConfigFile()
        self.assertNotIn('foo', c)
        self.assertEqual({}, c.sections)

    def test_contains(self):
        c = configfile.ConfigFile()
        c.enter_block('foo')
        self.assertNotIn('bar', c)
        self.assertIn('foo', c)

    def test_add_line_empty(self):
        c = configfile.ConfigFile()
        block = c.add_line('foo', self.l1)
        self.assertEqual('foo', block.name)
        self.assertIn('foo', c.sections)
        self.assertEqual(block, c.sections['foo'].extra_block)
        self.assertEqual([self.l1], list(block))

    def test_add_line_existing_block(self):
        c = configfile.ConfigFile()
        c.enter_block('foo')

        block = c.add_line('foo', self.l1)
        self.assertEqual('foo', block.name)
        self.assertEqual(block, c.current_block)
        self.assertEqual([block], c.blocks)
        self.assertIn('foo', c.sections)
        self.assertEqual(block, c.sections['foo'].blocks[0])
        self.assertEqual([self.l1], list(block))

    def test_update_line_empty(self):
        c = configfile.ConfigFile()
        updates = c.update_line('foo', self.l1, self.l3)

        self.assertEqual(0, updates)
        self.assertEqual([], c.blocks)

    def test_update_line_absent(self):
        c = configfile.ConfigFile()
        block = c.enter_block('foo')
        c.insert_line(self.l2)
        updates = c.update_line('foo', self.l1, self.l3)

        self.assertEqual(0, updates)
        self.assertEqual([block], c.blocks)

    def test_update_line_once(self):
        c = configfile.ConfigFile()
        block = c.enter_block('foo')
        c.insert_line(self.l1)
        c.insert_line(self.l3)
        c.insert_line(self.l1)

        updates = c.update_line('foo', self.l1, self.l3, once=True)

        self.assertEqual(1, updates)
        self.assertEqual([block], c.blocks)
        self.assertEqual([self.l3, self.l3, self.l1], list(block.lines))

    def test_update_line_many(self):
        c = configfile.ConfigFile()
        block = c.enter_block('foo')
        c.insert_line(self.l1)
        c.insert_line(self.l3)
        c.insert_line(self.l1)

        updates = c.update_line('foo', self.l4, self.l3)

        self.assertEqual(3, updates)
        self.assertEqual([block], c.blocks)
        self.assertEqual([self.l3, self.l3, self.l3], list(block.lines))

    def test_remove_line_empty(self):
        c = configfile.ConfigFile()

        removed = c.remove_line('foo', self.l1)

        self.assertEqual(0, removed)
        self.assertEqual([], c.blocks)

    def test_remove_line(self):
        c = configfile.ConfigFile()
        block = c.enter_block('foo')
        c.insert_line(self.l1)
        c.insert_line(self.l3)
        c.insert_line(self.l1)

        removed = c.remove_line('foo', self.l3)

        self.assertEqual(1, removed)
        self.assertEqual([block], c.blocks)
        self.assertEqual([self.l1, self.l1], list(block))

    def test_remove_line_many(self):
        c = configfile.ConfigFile()
        block = c.enter_block('foo')
        c.insert_line(self.l1)
        c.insert_line(self.l3)
        c.insert_line(self.l1)

        removed = c.remove_line('foo', self.l4)

        self.assertEqual(3, removed)
        self.assertEqual([block], c.blocks)
        self.assertEqual([], list(block))

    def test_get_empty(self):
        c = configfile.ConfigFile()

        self.assertEqual([], list(c.get('foo', 'bar')))

        c.enter_block('foo')
        self.assertEqual([], list(c.get('foo', 'bar')))
        self.assertEqual([], list(c.get('bar', 'foo')))

    def test_get(self):
        c = configfile.ConfigFile()
        c.enter_block('foo')
        c.insert_line(self.l1)
        c.insert_line(self.l3)
        c.insert_line(self.l1)

        c.enter_block('bar')
        c.insert_line(self.l3)
        c.insert_line(self.l3)

        lines = list(c.get('foo', 'x'))
        self.assertEqual(['42', '13', '42'], lines)

    def test_get_one_empty(self):
        c = configfile.ConfigFile()

        self.assertRaises(KeyError, c.get_one, 'foo', 'x')

    def test_get_one_notfound(self):
        c = configfile.ConfigFile()
        c.enter_block('foo')
        c.insert_line(self.l1)

        self.assertRaises(KeyError, c.get_one, 'foo', 'y')

    def test_get_one(self):
        c = configfile.ConfigFile()
        c.enter_block('foo')
        c.insert_line(self.l1)
        c.insert_line(self.l3)
        c.insert_line(self.l1)

        v = c.get_one('foo', 'x')
        self.assertEqual('42', v)

    def test_add_empty(self):
        c = configfile.ConfigFile()
        block = c.add('foo', 'x', '42')

        self.assertEqual([], c.blocks)
        self.assertEqual('foo', c.sections['foo'].name)
        self.assertEqual([block], c.sections['foo'].blocks)
        self.assertEqual(block, c.sections['foo'].extra_block)
        self.assertEqual([self.l1], block.lines)

    def test_add(self):
        c = configfile.ConfigFile()
        orig_block = c.enter_block('foo')
        c.insert_line(self.l1)

        block = c.add('foo', 'y', '13')
        self.assertEqual(block, orig_block)
        self.assertEqual([block], c.blocks)
        self.assertEqual([block], c.sections['foo'].blocks)
        self.assertIsNone(c.sections['foo'].extra_block)
        self.assertEqual(self.l1, block.lines[0])
        self.assertEqual('y', block.lines[1].key)

    def test_add_duplicate(self):
        c = configfile.ConfigFile()
        orig_block = c.enter_block('foo')
        c.insert_line(self.l1)

        block = c.add('foo', 'x', '42')
        self.assertEqual(block, orig_block)
        self.assertEqual([block], c.blocks)
        self.assertEqual([block], c.sections['foo'].blocks)
        self.assertIsNone(c.sections['foo'].extra_block)
        self.assertEqual([self.l1, self.l1], block.lines)

    def test_add_or_update_empty(self):
        c = configfile.ConfigFile()
        updated = c.add_or_update('foo', 'x', '42')

        self.assertEqual(0, updated)
        self.assertEqual([], c.blocks)
        self.assertIsNone(c.current_block)
        self.assertIn('foo', c.sections)
        self.assertEqual(1, len(c.sections['foo'].blocks))
        self.assertEqual([self.l1], c.sections['foo'].extra_block.lines)

    def test_add_or_update(self):
        c = configfile.ConfigFile()
        block = c.enter_block('foo')
        c.insert_line(self.l1)

        updated = c.add_or_update('foo', 'x', '13')

        self.assertEqual(1, updated)
        self.assertEqual([block], c.blocks)
        self.assertEqual(block, c.current_block)
        self.assertIn('foo', c.sections)
        self.assertEqual(1, len(c.sections['foo'].blocks))
        self.assertEqual([self.l3], block.lines)

    def test_add_or_update_duplicate(self):
        c = configfile.ConfigFile()
        block = c.enter_block('foo')
        c.insert_line(self.l1)
        c.insert_line(self.l3)
        c.insert_line(self.l1)

        updated = c.add_or_update('foo', 'x', '13')

        self.assertEqual(3, updated)
        self.assertEqual([block], c.blocks)
        self.assertEqual(block, c.current_block)
        self.assertIn('foo', c.sections)
        self.assertEqual(1, len(c.sections['foo'].blocks))
        self.assertEqual([self.l3, self.l3, self.l3], block.lines)

    def test_update_empty(self):
        c = configfile.ConfigFile()
        updated = c.update('foo', 'x', '13')

        self.assertEqual(0, updated)
        self.assertEqual([], c.blocks)
        self.assertIsNone(c.current_block)
        self.assertEqual({}, c.sections)

    def test_update(self):
        c = configfile.ConfigFile()
        block = c.enter_block('foo')
        c.insert_line(self.l1)
        c.insert_line(self.l3)
        c.insert_line(self.l1)

        updated = c.update('foo', 'x', '13')

        self.assertEqual(3, updated)
        self.assertEqual([block], c.blocks)
        self.assertEqual(block, c.current_block)
        self.assertEqual([self.l3, self.l3, self.l3], list(block))

    def test_update_once(self):
        c = configfile.ConfigFile()
        block = c.enter_block('foo')
        c.insert_line(self.l1)
        c.insert_line(self.l3)
        c.insert_line(self.l1)

        updated = c.update('foo', 'x', '13', once=True)

        self.assertEqual(1, updated)
        self.assertEqual([block], c.blocks)
        self.assertEqual(block, c.current_block)
        self.assertEqual([self.l3, self.l3, self.l1], list(block))

    def test_update_with_old(self):
        c = configfile.ConfigFile()
        block = c.enter_block('foo')
        c.insert_line(self.l1)
        c.insert_line(self.l3)
        c.insert_line(self.l1)

        updated = c.update('foo', 'x', '13', old_value='13', once=True)

        self.assertEqual(1, updated)
        self.assertEqual([block], c.blocks)
        self.assertEqual(block, c.current_block)
        self.assertEqual([self.l1, self.l3, self.l1], list(block))

    def test_remove_empty(self):
        c = configfile.ConfigFile()
        removed = c.remove('foo', '13')

        self.assertEqual(0, removed)
        self.assertEqual({}, c.sections)
        self.assertEqual([], c.blocks)

    def test_remove(self):
        c = configfile.ConfigFile()
        block = c.enter_block('foo')
        c.insert_line(self.l1)
        c.insert_line(self.l3)
        c.insert_line(self.l1)

        removed = c.remove('foo', 'x')
        self.assertEqual(3, removed)
        self.assertEqual([block], c.blocks)
        self.assertEqual(block, c.current_block)
        self.assertEqual([], list(block))

    def test_remove_with_value(self):
        c = configfile.ConfigFile()
        block = c.enter_block('foo')
        c.insert_line(self.l1)
        c.insert_line(self.l3)
        c.insert_line(self.l1)

        removed = c.remove('foo', 'x', '42')
        self.assertEqual(2, removed)
        self.assertEqual([block], c.blocks)
        self.assertEqual(block, c.current_block)
        self.assertEqual([self.l3], list(block))

    def test_items_empty(self):
        c = configfile.ConfigFile()
        self.assertEqual([], list(c.items('foo')))

    def test_items(self):
        c = configfile.ConfigFile()
        block = c.enter_block('foo')
        c.insert_line(self.l1)
        c.insert_line(self.l2)
        c.insert_line(self.l3)
        c.insert_line(self.l1)
        c.enter_block('bar')
        c.insert_line(self.l1)
        c.insert_line(self.l1)

        items = list(c.items('foo'))
        self.assertEqual([('x', '42'), ('x', '13'), ('x', '42')], items)

    def test_items_repeated(self):
        c = configfile.ConfigFile()
        block = c.enter_block('foo')
        c.insert_line(self.l1)
        c.insert_line(self.l3)
        c.insert_line(self.l1)
        c.enter_block('bar')
        c.insert_line(self.l1)
        c.insert_line(self.l1)

        items = list(c.items('foo'))
        self.assertEqual([('x', '42'), ('x', '13'), ('x', '42')], items)

        items = list(c.items('foo'))
        self.assertEqual([('x', '42'), ('x', '13'), ('x', '42')], items)

    def test_iter_empty(self):
        c = configfile.ConfigFile()
        lines = list(c)

        self.assertEqual([], lines)

    def test_iter_header_only(self):
        c = configfile.ConfigFile()
        c.insert_line(self.l1)
        c.insert_line(self.l3)

        lines = list(c)
        self.assertEqual([self.l1, self.l3], lines)

    def test_iter_usual(self):
        c = configfile.ConfigFile()
        c.insert_line(self.l1)
        c.enter_block('foo')
        c.insert_line(self.l3)
        c.insert_line(self.l3)
        c.enter_block('bar')
        c.insert_line(self.l1)
        c.insert_line(self.l1)

        lines = list(c)
        self.assertEqual([
            self.l1,
            self.h_foo,
            self.l3,
            self.l3,
            self.h_bar,
            self.l1,
            self.l1,
        ], lines)

    def test_iter_extra(self):
        c = configfile.ConfigFile()
        c.add('foo', 'x', '13')
        c.add('bar', 'x', '42')
        c.add('bar', 'x', '13')

        lines = list(c)
        self.assertEqual([
            self.h_foo,
            self.l3,
            self.h_bar,
            self.l1,
            self.l3,
        ], lines)

    def test_iter_removed(self):
        c = configfile.ConfigFile()
        c.enter_block('foo')
        c.enter_block('bar')
        c.add('foo', 'x', '13')
        c.add('bar', 'x', '42')
        c.add('bar', 'x', '13')

        c.remove('foo', 'x')

        lines = list(c)
        self.assertEqual([
            self.h_bar,
            self.l1,
            self.l3,
        ], lines)

    def test_idempotent(self):
        lines = [
            '# Comment before',
            '[foo]',
            'x: 13',
            '',
            '[bar]',
            'x: 42',
        ]
        c = configfile.ConfigFile()
        c.parse(lines)
        out_lines = list(c)
        self.assertEqual(lines, [str(l) for l in out_lines])

    def test_write_empty(self):
        f = io.StringIO()
        c = configfile.ConfigFile()
        c.write(f)
        self.assertEqual('', f.getvalue())

    def test_write_usual(self):
        c = configfile.ConfigFile()
        c.insert_line(self.l1)
        c.enter_block('foo')
        c.insert_line(self.l3)
        c.insert_line(self.l3)
        c.enter_block('bar')
        c.insert_line(self.l1)
        c.insert_line(self.l1)

        f = io.StringIO()
        c.write(f)
        self.assertEqual("x: 42\n[foo]\nx: 13\nx: 13\n[bar]\nx: 42\nx: 42\n",
            f.getvalue())

    def test_write_idempotent(self):
        lines = [
            '# Comment before',
            '[foo]',
            'x: 13',
            '',
            '[bar]',
            'x: 42',
        ]
        c = configfile.ConfigFile()
        c.parse(lines)

        f = io.StringIO()
        c.write(f)
        self.assertEqual(''.join(l + '\n' for l in lines), f.getvalue())


class SingleValuedSectionViewTestCase(unittest.TestCase):
    def _make_filled_configfile(self):
        self.l1 = configfile.ConfigLine(configfile.ConfigLine.KIND_DATA,
            key='x', value='13')
        self.l2 = configfile.ConfigLine(configfile.ConfigLine.KIND_DATA,
            key='y', value='14')
        self.l3 = configfile.ConfigLine(configfile.ConfigLine.KIND_DATA,
            key='z', value='2')
        self.l4 = configfile.ConfigLine(configfile.ConfigLine.KIND_DATA,
            key='x', value='42')

        cf = configfile.ConfigFile()
        cf.enter_block('foo')
        cf.insert_line(self.l1)
        cf.insert_line(self.l2)

        cf.enter_block('bar')
        cf.insert_line(self.l2)
        cf.insert_line(self.l4)

        cf.enter_block('foo')
        cf.insert_line(self.l3)
        return cf

    def setUp(self):
        self.empty_cf = configfile.ConfigFile()
        self.nonempty_cf = self._make_filled_configfile()

    def test_repr(self):
        view_foo = self.empty_cf.section_view('foo')
        self.assertIn('foo', repr(view_foo))
        view_baz = self.empty_cf.section_view('baz')
        self.assertIn('baz', repr(view_baz))

    def test_get_empty(self):
        view = self.empty_cf.section_view('foo')
        self.assertEqual([], view.items())
        with self.assertRaises(KeyError):
            view['x']

        self.assertIsNone(view.get('x'))
        self.assertEqual(13, view.get('x', 13))

    def test_get_nonempty(self):
        view = self.nonempty_cf.section_view('foo')
        self.assertEqual([('x', '13'), ('y', '14'), ('z', '2')], view.items())
        self.assertEqual('13', view['x'])
        self.assertEqual('14', view['y'])
        self.assertEqual('2', view['z'])
        self.assertEqual('13', view.get('x', 42))
        self.assertIsNone(view.get('t'))

    def test_setitem_empty(self):
        view = self.empty_cf.section_view('foo')

        self.assertEqual([], view.items())
        view['x'] = '13'
        self.assertEqual([('x', '13')], view.items())
        self.assertIn('foo', self.empty_cf)
        self.assertEqual([self.l1], list(self.empty_cf.sections['foo'].extra_block))

    def test_setitem_updates(self):
        view = self.nonempty_cf.section_view('foo')
        view['x'] = '42'
        self.assertEqual([('x', '42'), ('y', '14'), ('z', '2')], sorted(view.items()))
        self.assertEqual([self.l4, self.l2], list(self.nonempty_cf.blocks[0]))
        # Didn't touch other sections
        self.assertEqual([self.l2, self.l4], list(self.nonempty_cf.blocks[1]))

    def test_add_empty(self):
        view = self.empty_cf.section_view('foo')

        self.assertEqual([], view.items())
        view.add('x', '13')
        self.assertEqual([('x', '13')], view.items())
        self.assertIn('foo', self.empty_cf)
        self.assertEqual([self.l1], list(self.empty_cf.sections['foo'].extra_block))

    def test_add_updates(self):
        view = self.nonempty_cf.section_view('foo')
        view.add('x', '42')
        self.assertEqual([('x', '42'), ('y', '14'), ('z', '2')], sorted(view.items()))
        self.assertEqual([self.l4, self.l2], list(self.nonempty_cf.blocks[0]))
        # Didn't touch other sections
        self.assertEqual([self.l2, self.l4], list(self.nonempty_cf.blocks[1]))

    def test_del_empty(self):
        view = self.empty_cf.section_view('foo')
        with self.assertRaises(KeyError):
            del view['x']

    def test_del_nonempty(self):
        view = self.nonempty_cf.section_view('foo')
        del view['x']
        self.assertEqual([self.l2], list(self.nonempty_cf.blocks[0]))
        # Didn't touch other sections
        self.assertEqual([self.l2, self.l4], list(self.nonempty_cf.blocks[1]))


class MultiValuedSectionViewTestCase(unittest.TestCase):
    def _make_filled_configfile(self):
        self.l1 = configfile.ConfigLine(configfile.ConfigLine.KIND_DATA,
            key='x', value='13')
        self.l2 = configfile.ConfigLine(configfile.ConfigLine.KIND_DATA,
            key='y', value='14')
        self.l3 = configfile.ConfigLine(configfile.ConfigLine.KIND_DATA,
            key='z', value='2')
        self.l4 = configfile.ConfigLine(configfile.ConfigLine.KIND_DATA,
            key='x', value='42')
        self.l5 = configfile.ConfigLine(configfile.ConfigLine.KIND_DATA,
            key='x', value='15')

        cf = configfile.ConfigFile()
        cf.enter_block('foo')
        cf.insert_line(self.l1)
        cf.insert_line(self.l2)
        cf.insert_line(self.l1)

        cf.enter_block('bar')
        cf.insert_line(self.l2)
        cf.insert_line(self.l4)

        cf.enter_block('foo')
        cf.insert_line(self.l3)
        cf.insert_line(self.l4)
        return cf

    def setUp(self):
        self.empty_cf = configfile.ConfigFile()
        self.nonempty_cf = self._make_filled_configfile()

    def test_repr(self):
        view_foo = self.empty_cf.section_view('foo', multi_value=True)
        self.assertIn('foo', repr(view_foo))
        view_baz = self.empty_cf.section_view('baz', multi_value=True)
        self.assertIn('baz', repr(view_baz))

    def test_get_empty(self):
        view = self.empty_cf.section_view('foo', multi_value=True)
        self.assertEqual([], view.items())
        with self.assertRaises(KeyError):
            view['x']

        self.assertIsNone(view.get('x'))
        self.assertEqual(13, view.get('x', 13))

    def test_get_nonempty(self):
        view = self.nonempty_cf.section_view('foo', multi_value=True)
        self.assertEqual([
            ('x', ['13', '13', '42']),
            ('y', ['14']),
            ('z', ['2']),
        ], view.items())
        self.assertEqual(['13', '13', '42'], list(view['x']))
        self.assertEqual(['14'], list(view['y']))
        self.assertEqual(['2'], list(view['z']))
        self.assertIsNone(view.get('t'))

    def test_set_empty(self):
        view = self.empty_cf.section_view('foo', multi_value=True)

        self.assertEqual([], view.items())
        view['x'] = ['13']
        self.assertEqual([('x', ['13'])], view.items())
        self.assertIn('foo', self.empty_cf)
        self.assertEqual([self.l1], list(self.empty_cf.sections['foo'].extra_block))

    def test_setitem_adds(self):
        view = self.nonempty_cf.section_view('foo', multi_value=True)
        view['x'] = ['13', '15', '42']
        self.assertEqual([
            ('x', ['13', '13', '42', '15']),
            ('y', ['14']),
            ('z', ['2']),
        ], sorted(view.items()))
        self.assertEqual([self.l1, self.l2, self.l1], list(self.nonempty_cf.blocks[0]))
        self.assertEqual([self.l3, self.l4, self.l5], list(self.nonempty_cf.blocks[2]))
        # Didn't touch other sections
        self.assertEqual([self.l2, self.l4], list(self.nonempty_cf.blocks[1]))

    def test_setitem_updates(self):
        view = self.nonempty_cf.section_view('foo', multi_value=True)
        view['x'] = ['13', '15']
        self.assertEqual([
            ('x', ['13', '13', '15']),
            ('y', ['14']),
            ('z', ['2']),
        ], sorted(view.items()))
        self.assertEqual([self.l1, self.l2, self.l1], list(self.nonempty_cf.blocks[0]))
        self.assertEqual([self.l3, self.l5], list(self.nonempty_cf.blocks[2]))
        # Didn't touch other sections
        self.assertEqual([self.l2, self.l4], list(self.nonempty_cf.blocks[1]))

    def test_add_empty(self):
        view = self.empty_cf.section_view('foo', multi_value=True)
        self.assertEqual([], view.items())
        view.add('x', '13')
        self.assertEqual([('x', ['13'])], view.items())
        self.assertIn('foo', self.empty_cf)
        self.assertEqual([self.l1], list(self.empty_cf.sections['foo'].extra_block))

    def test_add_nonempty(self):
        view = self.nonempty_cf.section_view('foo', multi_value=True)
        view.add('x', '15')
        self.assertEqual([
            ('x', ['13', '13', '42', '15']),
            ('y', ['14']),
            ('z', ['2']),
        ], sorted(view.items()))
        self.assertEqual(['13', '13', '42', '15'], list(view['x']))
        self.assertEqual(['14'], list(view['y']))
        self.assertEqual(['2'], list(view['z']))
        self.assertIsNone(view.get('t'))
        self.assertEqual([self.l1, self.l2, self.l1], list(self.nonempty_cf.blocks[0]))
        self.assertEqual([self.l3, self.l4, self.l5], list(self.nonempty_cf.blocks[2]))
        # Didn't touch other sections
        self.assertEqual([self.l2, self.l4], list(self.nonempty_cf.blocks[1]))

    def test_del_empty(self):
        view = self.empty_cf.section_view('foo', multi_value=True)
        with self.assertRaises(KeyError):
            del view['x']

    def test_del_nonempty(self):
        view = self.nonempty_cf.section_view('foo', multi_value=True)
        del view['x']
        self.assertEqual([self.l2], list(self.nonempty_cf.blocks[0]))
        # Didn't touch other sections
        self.assertEqual([self.l2, self.l4], list(self.nonempty_cf.blocks[1]))
