# -*- coding: utf-8 -*-
# This code is distributed under the two-clause BSD license.
# Copyright (c) 2012-2013 Raphaël Barrois

from . import compat
unittest = compat.unittest

from confutils import helpers


class DictMixinTestCase(unittest.TestCase):
    def setUp(self):
        """Sets up a DictMixin subclass working around a dict."""
        class MyDict(helpers.DictMixin):
            def __init__(self, d):
                self.d = d

            def __getitem__(self, key):
                return self.d[key]

            def __setitem__(self, key, value):
                self.d[key] = value

            def __delitem__(self, key):
                del self.d[key]

            def iteritems(self):
                return compat.iteritems(self.d)

        self.MyDict = MyDict

    def test_len_empty(self):
        d = self.MyDict({})
        self.assertEqual(0, len(d))

    def test_len_nonempty(self):
        d = self.MyDict({'x': 1, 'y': 3})
        self.assertEqual(2, len(d))

    def test_len_updates(self):
        d = self.MyDict({})
        self.assertEqual(0, len(d))
        d['x'] = 1
        self.assertEqual(1, len(d))
        d['x'] = 2
        self.assertEqual(1, len(d))

    def test_items_empty(self):
        d = self.MyDict({})
        self.assertEqual([], list(d.items()))
        self.assertEqual([], list(d.iteritems()))

    def test_items_nonempty(self):
        d = self.MyDict({'x': 1, 'y': 2})
        self.assertEqual([('x', 1), ('y', 2)], sorted(d.items()))
        self.assertEqual([('x', 1), ('y', 2)], sorted(d.iteritems()))

        # Repeated access to generators shouldn't fail
        self.assertEqual([('x', 1), ('y', 2)], sorted(d.iteritems()))

    def test_items_updates(self):
        d = self.MyDict({})
        self.assertEqual([], list(d.items()))
        self.assertEqual([], list(d.iteritems()))

        d['x'] = 1
        self.assertEqual([('x', 1)], list(d.items()))
        self.assertEqual([('x', 1)], list(d.iteritems()))

        d['y']  =2
        self.assertEqual([('x', 1), ('y', 2)], sorted(d.items()))
        self.assertEqual([('x', 1), ('y', 2)], sorted(d.iteritems()))

    def test_contains_empty(self):
        d = self.MyDict({})
        self.assertNotIn(0, d)
        self.assertNotIn('x', d)

    def test_contains_nonempty(self):
        d = self.MyDict({'x': 1})
        self.assertIn('x', d)
        self.assertNotIn('y', d)
        self.assertNotIn(1, d)  # Don't mix values and keys
        self.assertNotIn(0, d)  # Don't mix indexes and keys

    def test_contains_updates(self):
        d = self.MyDict({})
        self.assertNotIn('x', d)

        d['x'] = 1
        self.assertIn('x', d)
        d['y'] = 2
        self.assertIn('x', d)  # Previous key is still here
        self.assertIn('y', d)

    def test_get_empty(self):
        d = self.MyDict({})
        self.assertIsNone(d.get('x'))
        self.assertEqual(42, d.get('x', 42))

    def test_get_nonempty(self):
        d = self.MyDict({'x': 1, 'y': 2})

        # Present key
        self.assertEqual(1, d.get('x'))
        self.assertEqual(1, d.get('x', 42))

        # Absent key
        self.assertIsNone(d.get('z'))
        self.assertEqual(42, d.get('z', 42))

    def test_get_updates(self):
        d = self.MyDict({})
        self.assertIsNone(d.get('x'))
        self.assertEqual(42, d.get('x', 42))

        d['x'] = 1
        self.assertEqual(1, d.get('x'))
        self.assertEqual(1, d.get('x', 42))

        d['y'] = 2
        self.assertEqual(2, d.get('y'))
        self.assertEqual(2, d.get('y', 42))

        # Ensure previous key is still there
        self.assertEqual(1, d.get('x'))
        self.assertEqual(1, d.get('x', 42))

    def test_setdefault_empty(self):
        d = self.MyDict({})
        self.assertNotIn('x', d)
        self.assertEqual(42, d.setdefault('x', 42))
        self.assertIn('x', d)
        self.assertEqual(42, d['x'])

    def test_setdefault_nonempty(self):
        d = self.MyDict({'x': 13})
        self.assertIn('x', d)
        self.assertEqual(13, d.setdefault('x', 42))
        self.assertIn('x', d)
        self.assertEqual(13, d['x'])

    def test_setdefault_nonempty_absent_key(self):
        d = self.MyDict({'x': 13})
        self.assertNotIn('y', d)
        self.assertEqual(42, d.setdefault('y', 42))
        self.assertIn('y', d)
        self.assertEqual(42, d['y'])

        # Ensure original key is still there
        self.assertEqual(13, d['x'])

    def test_pop_empty(self):
        d = self.MyDict({})
        with self.assertRaises(KeyError):
            d.pop('x')

        self.assertEqual(13, d.pop('x', 13))

    def test_pop_nonempty(self):
        d = self.MyDict({'x': 13})
        self.assertEqual(13, d.pop('x'))
        self.assertNotIn('x', d)

    def test_pop_nonempty_unknown_key(self):
        d = self.MyDict({'x': 13})

        with self.assertRaises(KeyError):
            d.pop('y')
        self.assertEqual(13, d.pop('y', 13))

        # Ensure the previous key is still there
        self.assertIn('x', d)
        self.assertEqual(13, d['x'])

    def test_iter_empty(self):
        d = self.MyDict({})
        self.assertEqual([], list(d))

    def test_iter_nonempty(self):
        d = self.MyDict({'x': 1, 'y': 2})
        self.assertEqual(['x', 'y'], list(sorted(d)))

        # Ensure generators can be called several times
        self.assertEqual(['x', 'y'], list(sorted(d)))

    def test_iter_updates(self):
        d = self.MyDict({})
        self.assertEqual([], list(d))

        d['x'] = 1
        self.assertEqual(['x'], list(d))

        d['y'] = 2
        self.assertEqual(['x', 'y'], list(sorted(d)))

        # Ensure generators can be called several times
        self.assertEqual(['x', 'y'], list(sorted(d)))

    def test_iterkeys_empty(self):
        d = self.MyDict({})
        self.assertEqual([], list(d.iterkeys()))

    def test_iterkeys_nonempty(self):
        d = self.MyDict({'x': 1, 'y': 2})
        self.assertEqual(['x', 'y'], list(sorted(d.iterkeys())))

        # Ensure generators can be called several times
        self.assertEqual(['x', 'y'], list(sorted(d.iterkeys())))

    def test_iterkeys_updates(self):
        d = self.MyDict({})
        self.assertEqual([], list(d.iterkeys()))

        d['x'] = 1
        self.assertEqual(['x'], list(d.iterkeys()))

        d['y'] = 2
        self.assertEqual(['x', 'y'], list(sorted(d.iterkeys())))

        # Ensure generators can be called several times
        self.assertEqual(['x', 'y'], list(sorted(d.iterkeys())))

    def test_keys_empty(self):
        d = self.MyDict({})
        self.assertEqual([], list(d.keys()))

    def test_keys_nonempty(self):
        d = self.MyDict({'x': 1, 'y': 2})
        self.assertEqual(['x', 'y'], list(sorted(d.keys())))

        # Ensure generators can be called several times
        self.assertEqual(['x', 'y'], list(sorted(d.keys())))

    def test_keys_updates(self):
        d = self.MyDict({})
        self.assertEqual([], list(d.keys()))

        d['x'] = 1
        self.assertEqual(['x'], list(d.keys()))

        d['y'] = 2
        self.assertEqual(['x', 'y'], list(sorted(d.keys())))

        # Ensure generators can be called several times
        self.assertEqual(['x', 'y'], list(sorted(d.keys())))

    def test_itervalues_empty(self):
        d = self.MyDict({})
        self.assertEqual([], list(d.itervalues()))

    def test_itervalues_nonempty(self):
        d = self.MyDict({'x': 1, 'y': 2})
        self.assertEqual([1, 2], list(sorted(d.itervalues())))

        # Ensure generators can be called several times
        self.assertEqual([1, 2], list(sorted(d.itervalues())))

    def test_itervalues_updates(self):
        d = self.MyDict({})
        self.assertEqual([], list(d.itervalues()))

        d['x'] = 1
        self.assertEqual([1], list(d.itervalues()))

        d['y'] = 2
        self.assertEqual([1, 2], list(sorted(d.itervalues())))

        # Ensure generators can be called several times
        self.assertEqual([1, 2], list(sorted(d.itervalues())))

    def test_values_empty(self):
        d = self.MyDict({})
        self.assertEqual([], list(d.values()))

    def test_values_nonempty(self):
        d = self.MyDict({'x': 1, 'y': 2})
        self.assertEqual([1, 2], list(sorted(d.values())))

        # Ensure generators can be called several times
        self.assertEqual([1, 2], list(sorted(d.values())))

    def test_values_updates(self):
        d = self.MyDict({})
        self.assertEqual([], list(d.values()))

        d['x'] = 1
        self.assertEqual([1], list(d.values()))

        d['y'] = 2
        self.assertEqual([1, 2], list(sorted(d.values())))

        # Ensure generators can be called several times
        self.assertEqual([1, 2], list(sorted(d.values())))
