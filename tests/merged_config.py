# -*- coding: utf-8 -*-
# This code is distributed under the two-clause BSD license.
# Copyright (c) 2012-2013 Raphaël Barrois

from .compat import unittest

from confutils import merged_config


class DefaultTestCase(unittest.TestCase):
    def test_init(self):
        d = merged_config.Default(42)
        self.assertEqual(42, d.value)

    def test_repr(self):
        d = merged_config.Default(13)
        self.assertEqual('Default(13)', repr(d))

        d = merged_config.Default((13, 42))
        self.assertEqual('Default((13, 42))', repr(d))

    def test_hash(self):
        d = merged_config.Default((1, 2))
        self.assertEqual(hash(d), hash(d.value))

    def test_bool(self):
        d = merged_config.Default([])
        self.assertFalse(d)

        d = merged_config.Default(1)
        self.assertTrue(d)

    def test_eq(self):
        d1 = merged_config.Default([])
        d2 = merged_config.Default([])

        self.assertEqual(d1, d2)
        self.assertFalse(d1 == [])


class NormalizeKeyTestCase(unittest.TestCase):
    def test_idempotent(self):
        k = 'FooBar'
        k1 = merged_config.normalize_key(k)
        k2 = merged_config.normalize_key(k1)
        self.assertEqual(k1, k2)

    def test_simple(self):
        k = 'Foo-Bar-Baz'
        self.assertEqual('foo_bar_baz', merged_config.normalize_key(k))

    def test_empty(self):
        k = ''
        self.assertEqual('', merged_config.normalize_key(k))


class NormalizedDictTestCase(unittest.TestCase):
    def test_init_empty(self):
        d = merged_config.NormalizedDict()
        self.assertEqual({}, d)
        self.assertNotIn('', d)

    def test_init_alt_dict(self):
        d = merged_config.NormalizedDict({'foo': 1, 'BAR': 2})
        self.assertEqual({'foo': 1, 'bar': 2}, d)

    def test_init_kwargs(self):
        d = merged_config.NormalizedDict(foo=1, BAR=2)
        self.assertEqual({'foo': 1, 'bar': 2}, d)

    def test_init_tuple(self):
        d = merged_config.NormalizedDict([('foo', 1), ('BAR', 2)])
        self.assertEqual({'foo': 1, 'bar': 2}, d)

    def test_init_ambiguous(self):
        d = merged_config.NormalizedDict({'FOO': 1, 'foo': 2})
        self.assertEqual({'foo': 2}, d)

    def test_setitem(self):
        d = merged_config.NormalizedDict()
        d['foo'] = 1
        self.assertEqual(d, {'foo': 1})
        d['FOO'] = 2
        self.assertEqual(d, {'foo': 2})

    def test_getitem(self):
        d = merged_config.NormalizedDict()
        self.assertRaises(KeyError, d.__getitem__, 'foo')
        d['foo'] = 1
        self.assertEqual(1, d['foo'])
        self.assertEqual(1, d['FOO'])

    def test_setdefault(self):
        d = merged_config.NormalizedDict()
        x = d.setdefault('FOO', 1)
        self.assertEqual(1, x)
        self.assertEqual({'foo': 1}, d)

        y = d.setdefault('Foo', 2)
        self.assertEqual(1, y)
        self.assertEqual({'foo': 1}, d)

    def test_get(self):
        d = merged_config.NormalizedDict()
        x = d.get('Foo')
        self.assertIsNone(x)

        d['foo'] = 13
        x = d.get('FOO')
        self.assertEqual(13, x)

    def test_pop(self):
        d = merged_config.NormalizedDict()
        self.assertRaises(KeyError, d.pop, 'foo')

        x = d.pop('foo', None)
        self.assertIsNone(x)

        d['foo'] = 13
        x = d.pop('FOO')
        self.assertEqual(13, x)
        self.assertEqual({}, d)


class DictNamespaceTestCase(unittest.TestCase):
    def setUp(self):
        class NS(object):
            def __init__(self):
                self.x = 1
                self.y = 2
                self.z = 3
        self.ns = NS()

    def test_init(self):
        d = merged_config.DictNamespace(self.ns)
        self.assertEqual({'x': 1, 'y': 2, 'z': 3}, d)

    def test_empty_object(self):
        class O(object):
            pass

        d = merged_config.DictNamespace(O())
        self.assertEqual({}, d)


class MergedConfigTestCase(unittest.TestCase):
    def test_init(self):
        mc = merged_config.MergedConfig()
        self.assertEqual([], mc.options)

        d = {'x': 1, 'y': 2}
        mc = merged_config.MergedConfig(d)
        self.assertEqual([d], mc.options)

    def test_init_normalizes(self):
        d = {'X': 1, 'y': 2}
        dn = {'x': 1, 'y': 2}
        mc = merged_config.MergedConfig(d, d)
        self.assertEqual([dn, dn], mc.options)

    def test_add_options(self):
        d = {'x': 1, 'y': 2}
        mc = merged_config.MergedConfig()
        mc.add_options(d)
        self.assertEqual([d], mc.options)

    def test_add_options_duplicate(self):
        d = {'x': 1, 'y': 2}
        mc = merged_config.MergedConfig(d)
        mc.add_options(d)
        self.assertEqual([d, d], mc.options)

    def test_add_options_normalizes(self):
        d = {'X': 1, 'y': 2}
        dn = {'x': 1, 'y': 2}
        mc = merged_config.MergedConfig()
        mc.add_options(d)
        self.assertEqual([dn], mc.options)

    def test_add_options_no_normalize(self):
        d = {'X': 1, 'y': 2}
        mc = merged_config.MergedConfig()
        mc.add_options(d, normalize=False)
        self.assertEqual([d], mc.options)

    def test_get_empty(self):
        mc = merged_config.MergedConfig()
        value = mc.get('foo')
        self.assertEqual(merged_config.NoDefault, value)

    def test_get_empty_with_default(self):
        mc = merged_config.MergedConfig()
        value = mc.get('foo', None)
        self.assertEqual(None, value)

    def test_get_missing(self):
        d1 = {'x': 1, 'y': 2}
        d2 = {'foo': 13, 'bar': 42}
        mc = merged_config.MergedConfig(d1, d2)

        value = mc.get('z')
        self.assertEqual(merged_config.NoDefault, value)

    def test_get_from_first_dict(self):
        d1 = {'x': 1, 'y': 2}
        d2 = {'foo': 13, 'bar': 42}
        mc = merged_config.MergedConfig(d1, d2)

        value = mc.get('y')
        self.assertEqual(2, value)

    def test_get_from_second_dict(self):
        d1 = {'x': 1, 'y': 2}
        d2 = {'foo': 13, 'bar': 42}
        mc = merged_config.MergedConfig(d1, d2)

        value = mc.get('foo')
        self.assertEqual(13, value)

    def test_get_picks_first_result(self):
        d1 = {'x': 1, 'y': 2}
        d2 = {'x': 13}
        mc = merged_config.MergedConfig(d1, d2)

        value = mc.get('x')
        self.assertEqual(1, value)

    def test_get_is_normalized(self):
        d1 = {'x': 1, 'y': 2}
        d2 = {'foo': 13, 'bar': 42}
        mc = merged_config.MergedConfig(d1, d2)

        value = mc.get('FOO')
        self.assertEqual(13, value)

    def test_get_skips_defaults(self):
        d1 = {'x': merged_config.Default(1)}
        d2 = {'x': merged_config.Default(13)}
        d3 = {'x': 42}
        mc = merged_config.MergedConfig(d1, d2, d3)

        value = mc.get('x')
        self.assertEqual(42, value)

    def test_get_respects_defaults_order(self):
        d1 = {'x': merged_config.Default(1)}
        d2 = {'x': merged_config.Default(13)}

        mc = merged_config.MergedConfig(d1, d2)
        self.assertEqual(1, mc.get('x'))

    def test_get_caller_default_has_higher_precedence(self):
        d1 = {'x': merged_config.Default(1)}
        d2 = {'x': merged_config.Default(13)}

        mc = merged_config.MergedConfig(d1, d2)
        self.assertEqual(42, mc.get('x', 42))
