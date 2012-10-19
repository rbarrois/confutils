# coding: utf-8
# Copyright (c) 2010-2012 Raphaël Barrois

import unittest

from confutils import configwriter


class LineTestCase(unittest.TestCase):
    def test_compare_other(self):
        l = configwriter.ConfigLine(configwriter.ConfigLine.KIND_BLANK, '# x')
        self.assertFalse(l == '# x')
        self.assertFalse('# x' == l)

    def test_blank(self):
        """Test 'blank' lines."""
        l = configwriter.ConfigLine(configwriter.ConfigLine.KIND_BLANK, '# foo')
        self.assertEqual('# foo', str(l))
        self.assertTrue(l.match(l))

        l2 = configwriter.ConfigLine(configwriter.ConfigLine.KIND_BLANK,
                ' # foo ')
        self.assertTrue(l.match(l2))
        self.assertTrue(l2.match(l))
        self.assertNotEqual(l, l2)
        self.assertNotEqual(hash(l), hash(l2))

        l3 = configwriter.ConfigLine(configwriter.ConfigLine.KIND_BLANK,
                '# foo')
        self.assertEqual(l, l3)
        self.assertTrue(l.match(l3))
        self.assertTrue(l3.match(l))
        self.assertEqual(hash(l), hash(l3))

    def test_blank_notext(self):
        """Test 'blank' lines without provided text."""
        l = configwriter.ConfigLine(configwriter.ConfigLine.KIND_BLANK)
        self.assertEqual('', l.text)

    def test_header(self):
        """Test 'header' lines."""
        l1 = configwriter.ConfigLine(configwriter.ConfigLine.KIND_HEADER,
                '[foo]', header='foo')
        l2 = configwriter.ConfigLine(configwriter.ConfigLine.KIND_HEADER,
                '[foo] # Blah', header='foo')
        l3 = configwriter.ConfigLine(configwriter.ConfigLine.KIND_HEADER,
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
        l = configwriter.ConfigLine(configwriter.ConfigLine.KIND_HEADER,
                header='foo')
        self.assertEqual('[foo]', l.text)

    def test_data(self):
        """Test 'data' lines."""
        l1 = configwriter.ConfigLine(configwriter.ConfigLine.KIND_DATA,
                'foo = bar', key='foo', value='bar')
        l2 = configwriter.ConfigLine(configwriter.ConfigLine.KIND_DATA,
                '  foo = bar', key='foo', value='bar')
        l3 = configwriter.ConfigLine(configwriter.ConfigLine.KIND_DATA,
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
        l = configwriter.ConfigLine(configwriter.ConfigLine.KIND_DATA,
                key='foo', value='bar')
        self.assertEqual('foo: bar', l.text)

    def test_cross_compare(self):
        """Test comparisions between different kinds."""
        l1 = configwriter.ConfigLine(configwriter.ConfigLine.KIND_BLANK,
                '# foo')
        l2 = configwriter.ConfigLine(configwriter.ConfigLine.KIND_HEADER,
                '[foo]', header='foo')
        l3 = configwriter.ConfigLine(configwriter.ConfigLine.KIND_DATA,
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
        l1 = configwriter.ConfigLine(configwriter.ConfigLine.KIND_BLANK,
                '# foo')
        self.assertIn('foo', repr(l1))

        l2 = configwriter.ConfigLine(configwriter.ConfigLine.KIND_HEADER,
                '[foo]', header='foo')
        self.assertIn('[foo]', repr(l2))

        l3 = configwriter.ConfigLine(configwriter.ConfigLine.KIND_DATA,
                'foo = bar', key='foo', value='bar')
        self.assertIn('foo', repr(l3))
        self.assertIn('bar', repr(l3))


class LexerTestCase(unittest.TestCase):
    def test_parse_empty_line(self):
        lexer = configwriter.Lexer()
        l = lexer.parse_line('')
        self.assertEqual(l.KIND_BLANK, l.kind)
        self.assertEqual('', l.text)
        self.assertIsNone(l.key)
        self.assertIsNone(l.value)
        self.assertIsNone(l.header)

    def test_parse_space_line(self):
        lexer = configwriter.Lexer()
        l = lexer.parse_line('  ')
        self.assertEqual(l.KIND_BLANK, l.kind)
        self.assertEqual('  ', l.text)
        self.assertIsNone(l.key)
        self.assertIsNone(l.value)
        self.assertIsNone(l.header)

    def test_parse_commented_line(self):
        lexer = configwriter.Lexer()
        l = lexer.parse_line(' # foo')
        self.assertEqual(l.KIND_BLANK, l.kind)
        self.assertEqual(' # foo', l.text)
        self.assertIsNone(l.key)
        self.assertIsNone(l.value)
        self.assertIsNone(l.header)

    def test_parse_data_line(self):
        lexer = configwriter.Lexer()
        l = lexer.parse_line('foo: bar')
        self.assertEqual(l.KIND_DATA, l.kind)
        self.assertEqual('foo: bar', l.text)
        self.assertEqual('foo', l.key)
        self.assertEqual('bar', l.value)
        self.assertIsNone(l.header)

    def test_parse_data_line_with_space(self):
        lexer = configwriter.Lexer()
        l = lexer.parse_line('  foo= bar')
        self.assertEqual(l.KIND_DATA, l.kind)
        self.assertEqual('  foo= bar', l.text)
        self.assertEqual('foo', l.key)
        self.assertEqual('bar', l.value)
        self.assertIsNone(l.header)

    def test_parse_data_line_with_comment(self):
        lexer = configwriter.Lexer()
        l = lexer.parse_line('foo: bar  # baz')
        self.assertEqual(l.KIND_DATA, l.kind)
        self.assertEqual('foo: bar  # baz', l.text)
        self.assertEqual('foo', l.key)
        self.assertEqual('bar  # baz', l.value)
        self.assertIsNone(l.header)

    def test_section_line(self):
        lexer = configwriter.Lexer()
        l = lexer.parse_line('[foo]')
        self.assertEqual(l.KIND_HEADER, l.kind)
        self.assertEqual('[foo]', l.text)
        self.assertIsNone(l.key)
        self.assertIsNone(l.value)
        self.assertEqual('foo', l.header)

    def test_section_line_with_space(self):
        lexer = configwriter.Lexer()
        l = lexer.parse_line('[foo]   ')
        self.assertEqual(l.KIND_HEADER, l.kind)
        self.assertEqual('[foo]   ', l.text)
        self.assertIsNone(l.key)
        self.assertIsNone(l.value)
        self.assertEqual('foo', l.header)

    def test_section_line_with_comment(self):
        lexer = configwriter.Lexer()
        l = lexer.parse_line('[foo]#bar')
        self.assertEqual(l.KIND_HEADER, l.kind)
        self.assertEqual('[foo]#bar', l.text)
        self.assertIsNone(l.key)
        self.assertIsNone(l.value)
        self.assertEqual('foo', l.header)

    def test_parse_invalid_line(self):
        lexer = configwriter.Lexer()
        self.assertRaises(ValueError, lexer.parse_line, ' foo')

    def test_parse_lines(self):
        lexer = configwriter.Lexer()
        lines = list(lexer.parse([
            '  # Initial comment',
            '[foo]  # First section',
            'x = 42',
            'y: 13',
        ]))

        self.assertEqual(lines, [
            configwriter.ConfigLine(configwriter.ConfigLine.KIND_BLANK,
                '  # Initial comment'),
            configwriter.ConfigLine(configwriter.ConfigLine.KIND_HEADER,
                '[foo]  # First section', header='foo'),
            configwriter.ConfigLine(configwriter.ConfigLine.KIND_DATA,
                'x = 42', key='x', value='42'),
            configwriter.ConfigLine(configwriter.ConfigLine.KIND_DATA,
                'y: 13', key='y', value='13'),
        ])


class ConfigLineList(unittest.TestCase):
    def setUp(self):
        self.l1 = configwriter.ConfigLine(configwriter.ConfigLine.KIND_HEADER,
                '[foo]', header='foo')
        self.l2 = configwriter.ConfigLine(configwriter.ConfigLine.KIND_DATA,
                'foo: bar', key='foo', value='bar')
        self.l3 = configwriter.ConfigLine(configwriter.ConfigLine.KIND_DATA,
                'baz: 42', key='baz', value='42')

    def test_init(self):
        l = configwriter.ConfigLineList()
        self.assertEqual([], l.lines)

        l = configwriter.ConfigLineList(self.l1, self.l2, self.l3)
        self.assertEqual([self.l1, self.l2, self.l3], l.lines)

    def test_len(self):
        l = configwriter.ConfigLineList(self.l1, self.l2, self.l3)
        self.assertEqual(3, len(l))

    def test_iter(self):
        l = configwriter.ConfigLineList(self.l1, self.l2, self.l3)
        self.assertEqual([self.l1, self.l2, self.l3], list(l))

    def test_contains(self):
        l = configwriter.ConfigLineList(self.l1, self.l2, self.l3)
        self.assertIn(self.l1, l)
        self.assertIn(self.l2, l)
        self.assertIn(self.l3, l)

        line = configwriter.ConfigLine(configwriter.ConfigLine.KIND_DATA,
            'foo =', key='foo')
        self.assertIn(line, l)

    def test_empty_list(self):
        l = configwriter.ConfigLineList()
        self.assertEqual(0, len(l))
        self.assertNotIn(self.l1, l)

    def test_eq(self):
        l = configwriter.ConfigLineList(self.l1, self.l2, self.l3)
        ll = configwriter.ConfigLineList(self.l1, self.l2, self.l3)
        self.assertEqual(l, ll)

        lll = configwriter.ConfigLineList(self.l1, self.l2)
        self.assertNotEqual(l, lll)

        self.assertFalse(l == [self.l1, self.l2, self.l3])

    def test_hash(self):
        l = configwriter.ConfigLineList(self.l1, self.l2, self.l3)
        self.assertNotEqual(hash((self.l1, self.l2, self.l3)), hash(l))

        ll = configwriter.ConfigLineList(self.l1, self.l2, self.l3)
        self.assertEqual(hash(l), hash(ll))

    def test_repr(self):
        l = configwriter.ConfigLineList(self.l1, self.l2, self.l3)
        self.assertIn(repr(self.l1), repr(l))
        self.assertIn(repr(self.l2), repr(l))
        self.assertIn(repr(self.l3), repr(l))

    def test_append(self):
        l = configwriter.ConfigLineList(self.l1, self.l2, self.l3)
        l.append(self.l3)
        self.assertEqual([self.l1, self.l2, self.l3, self.l3], l.lines)

    def test_remove(self):
        l = configwriter.ConfigLineList(self.l1, self.l2, self.l3)
        l.remove(self.l3)
        self.assertEqual([self.l1, self.l2], l.lines)

    def test_remove_duplicated(self):
        l = configwriter.ConfigLineList(self.l3, self.l3, self.l1, self.l3,
                self.l2, self.l3)
        l.remove(self.l3)
        self.assertEqual([self.l1, self.l2], l.lines)

    def test_remove_empty(self):
        l = configwriter.ConfigLineList()
        l.remove(self.l1)
        self.assertEqual([], l.lines)

    def test_update(self):
        l = configwriter.ConfigLineList(self.l1, self.l2, self.l3)
        nb_updates = l.update(self.l1, self.l2)

        self.assertEqual(1, nb_updates)
        self.assertEqual([self.l2, self.l2, self.l3], l.lines)

    def test_update_duplicated(self):
        l = configwriter.ConfigLineList(self.l1, self.l3, self.l1, self.l3)
        nb_updates = l.update(self.l1, self.l2)

        self.assertEqual(2, nb_updates)
        self.assertEqual([self.l2, self.l3, self.l2, self.l3], l.lines)

    def test_update_duplicated_once(self):
        l = configwriter.ConfigLineList(self.l1, self.l3, self.l1, self.l3)
        nb_updates = l.update(self.l1, self.l2, once=True)

        self.assertEqual(1, nb_updates)
        self.assertEqual([self.l2, self.l3, self.l1, self.l3], l.lines)

    def test_update_empty(self):
        l = configwriter.ConfigLineList()
        nb_updates = l.update(self.l1, self.l2)

        self.assertEqual(0, nb_updates)
        self.assertEqual([], l.lines)


class SectionBlockTestCase(unittest.TestCase):
    def setUp(self):
        self.l1 = configwriter.ConfigLine(configwriter.ConfigLine.KIND_HEADER,
                '[foo]', header='foo')
        self.l2 = configwriter.ConfigLine(configwriter.ConfigLine.KIND_DATA,
                'foo: bar', key='foo', value='bar')
        self.l3 = configwriter.ConfigLine(configwriter.ConfigLine.KIND_DATA,
                'baz: 42', key='baz', value='42')

    def test_init(self):
        sb = configwriter.SectionBlock('foo', self.l1, self.l2, self.l3)
        self.assertEqual('foo', sb.name)
        self.assertEqual([self.l1, self.l2, self.l3], list(sb))

    def test_repr(self):
        sb = configwriter.SectionBlock('blah', self.l1, self.l2, self.l3)
        self.assertIn('blah', repr(sb))
        self.assertIn(repr(self.l1), repr(sb))
        self.assertIn(repr(self.l2), repr(sb))
        self.assertIn(repr(self.l3), repr(sb))

    def test_header_line(self):
        sb = configwriter.SectionBlock('blah', self.l1, self.l2, self.l3)
        header = sb.header_line()
        self.assertEqual(configwriter.ConfigLine.KIND_HEADER, header.kind)
        self.assertEqual('[blah]', header.text)
        self.assertEqual('blah', header.header)
        self.assertIsNone(header.key)
        self.assertIsNone(header.value)


class SectionTestCase(unittest.TestCase):
    def setUp(self):
        self.l1 = configwriter.ConfigLine(configwriter.ConfigLine.KIND_HEADER,
                '[foo]', header='foo')
        self.l2 = configwriter.ConfigLine(configwriter.ConfigLine.KIND_DATA,
                'foo: bar', key='foo', value='bar')
        self.l3 = configwriter.ConfigLine(configwriter.ConfigLine.KIND_DATA,
                'baz: 42', key='baz', value='42')

    def test_init(self):
        s = configwriter.Section('foo')
        self.assertEqual('foo', s.name)
        self.assertEqual([], s.blocks)
        self.assertIsNone(s.extra_block)

    def test_repr(self):
        s = configwriter.Section('foo')
        self.assertIn('foo', repr(s))

    def test_new_block(self):
        s = configwriter.Section('foo')
        block = s.new_block()

        self.assertEqual([block], s.blocks)
        self.assertIsNone(s.extra_block)
        self.assertEqual([block], list(s))

        self.assertEqual('foo', block.name)
        self.assertEqual(0, len(block))

    def test_new_block_chain(self):
        s = configwriter.Section('foo')
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
        s = configwriter.Section('foo')
        self.assertIsNone(s.find_block(self.l1))

        block1 = s.new_block()
        self.assertIsNone(s.find_block(self.l1))

        block2 = s.new_block()
        self.assertIsNone(s.find_block(self.l1))

    def test_find_block(self):
        s = configwriter.Section('foo')
        block = s.new_block()
        block.append(self.l1)
        block.append(self.l2)

        self.assertEqual(block, s.find_block(self.l2))

    def test_find_block_duplicated(self):
        s = configwriter.Section('foo')
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
        s = configwriter.Section('foo')
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
        s = configwriter.Section('foo')
        block = s.new_block()

        target_block = s.insert(self.l1)

        self.assertEqual(block, target_block)
        self.assertEqual([block], s.blocks)
        self.assertIsNone(s.extra_block)
        self.assertEqual([self.l1], block.lines)

    def test_insert_close(self):
        """Ensure similar lines are inserted nearby."""
        s = configwriter.Section('foo')
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
        s = configwriter.Section('foo')
        block = s.insert(self.l1)

        self.assertEqual(block, s.extra_block)
        self.assertEqual([block], s.blocks)
        self.assertEqual([self.l1], block.lines)

    def test_update(self):
        s = configwriter.Section('foo')
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
        s = configwriter.Section('foo')
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
        s = configwriter.Section('foo')
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
        s = configwriter.Section('foo')
        block1 = s.new_block()
        block2 = s.new_block()

        nb_updates = s.update(self.l2, self.l3)

        self.assertEqual(0, nb_updates)
        self.assertEqual([block1, block2], s.blocks)
        self.assertEqual([], block1.lines)
        self.assertEqual([], block2.lines)

    def test_update_noblocks(self):
        s = configwriter.Section('foo')

        nb_updates = s.update(self.l2, self.l3)

        self.assertEqual(0, nb_updates)
        self.assertEqual([], s.blocks)
        self.assertIsNone(s.extra_block)

    def test_remove(self):
        s = configwriter.Section('foo')
        block1 = s.new_block()
        block1.append(self.l1)

        block2 = s.new_block()
        block2.append(self.l1)
        block2.append(self.l2)

        s.remove(self.l1)

        self.assertEqual([block1, block2], s.blocks)
        self.assertEqual([], block1.lines)
        self.assertEqual([self.l2], block2.lines)

    def test_remove_nonexistant(self):
        """Test removing an absent line."""
        s = configwriter.Section('foo')
        block1 = s.new_block()
        block1.append(self.l1)

        block2 = s.new_block()
        block2.append(self.l1)
        block2.append(self.l2)

        s.remove(self.l3)

        self.assertEqual([block1, block2], s.blocks)
        self.assertEqual([self.l1], block1.lines)
        self.assertEqual([self.l1, self.l2], block2.lines)

    def test_remove_empty(self):
        """Test removing from an empty section."""
        s = configwriter.Section('foo')
        s.remove(self.l1)

        self.assertIsNone(s.extra_block)
        self.assertEqual([], s.blocks)


class ConfigFileTestCase(unittest.TestCase):
    def setUp(self):
        self.l1 = configwriter.ConfigLine(configwriter.ConfigLine.KIND_DATA,
                key='x', value='42')
        self.l2 = configwriter.ConfigLine(configwriter.ConfigLine.KIND_HEADER,
                header='bar')
        self.l3 = configwriter.ConfigLine(configwriter.ConfigLine.KIND_DATA,
                key='x', value='13')
        self.l4 = configwriter.ConfigLine(configwriter.ConfigLine.KIND_DATA,
                key='x', value=None)

    def test_enter_block(self):
        c = configwriter.ConfigFile()
        self.assertEqual([], c.blocks)
        self.assertIsNone(c.current_block)

        block = c.enter_block('foo')
        self.assertEqual([block], c.blocks)
        self.assertEqual(block, c.current_block)
        self.assertIn('foo', c.sections)
        self.assertEqual([block], c.sections['foo'].blocks)

    def test_enter_block_twice(self):
        c = configwriter.ConfigFile()
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
        c = configwriter.ConfigFile()
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
        c = configwriter.ConfigFile()
        c.insert_line(self.l1)

        self.assertEqual([], c.blocks)
        self.assertIsNone(c.current_block)
        self.assertEqual([self.l1], list(c.header))

    def test_insert_line(self):
        c = configwriter.ConfigFile()
        block = c.enter_block('foo')

        c.insert_line(self.l1)

        self.assertEqual([self.l1], list(block))
        self.assertEqual([self.l1], list(c.current_block))
        self.assertEqual([], list(c.header))

    def test_handle_line_data_header(self):
        c = configwriter.ConfigFile()
        c.handle_line(self.l1)

        self.assertEqual([], c.blocks)
        self.assertIsNone(c.current_block)
        self.assertEqual([self.l1], list(c.header))

    def test_handle_line_data_block(self):
        c = configwriter.ConfigFile()
        block = c.enter_block('foo')

        c.handle_line(self.l1)

        self.assertEqual([self.l1], list(block))
        self.assertEqual([self.l1], list(c.current_block))
        self.assertEqual([], list(c.header))

    def test_handle_line_section_header(self):
        c = configwriter.ConfigFile()
        block = c.enter_block('foo')

        c.handle_line(self.l2)

        self.assertEqual(2, len(c.blocks))
        self.assertEqual('bar', c.current_block.name)
        self.assertIn('bar', c.sections)

    def test_get_line_undefined(self):
        c = configwriter.ConfigFile()
        c.enter_block('foo')
        lines = list(c.get_line('foo', self.l1))
        self.assertEqual([], lines)

    def test_get_line_invalid_section(self):
        c = configwriter.ConfigFile()
        self.assertRaises(KeyError, c.get_line, 'foo', self.l1)

    def test_get_line(self):
        c = configwriter.ConfigFile()
        c.enter_block('foo')
        c.insert_line(self.l1)
        c.enter_block('bar')
        c.insert_line(self.l3)

        lines = list(c.get_line('foo', self.l1))
        self.assertEqual([self.l1], lines)

        lines = list(c.get_line('foo', self.l4))
        self.assertEqual([self.l1], lines)

    def test_add_line_empty(self):
        c = configwriter.ConfigFile()
        block = c.add_line('foo', self.l1)
        self.assertEqual('foo', block.name)
        self.assertIn('foo', c.sections)
        self.assertEqual(block, c.sections['foo'].extra_block)
        self.assertEqual([self.l1], list(block))

    def test_add_line_existing_block(self):
        c = configwriter.ConfigFile()
        c.enter_block('foo')

        block = c.add_line('foo', self.l1)
        self.assertEqual('foo', block.name)
        self.assertEqual(block, c.current_block)
        self.assertEqual([block], c.blocks)
        self.assertIn('foo', c.sections)
        self.assertEqual(block, c.sections['foo'].blocks[0])
        self.assertEqual([self.l1], list(block))