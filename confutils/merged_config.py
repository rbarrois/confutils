# -*- coding: utf-8 -*-
# This code is distributed under the two-clause BSD license.
# Copyright (c) 2012 Raphaël Barrois


from __future__ import unicode_literals


"""Merge configuration options from a configuration file and CLI arguments."""


class Default(object):
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return 'Default(%r)' % (self.value,)

    def __hash__(self):
        return hash(self.value)

    def __bool__(self):
        return bool(self.value)

    __nonzero__ = __bool__

    def __eq__(self, other):
        if not isinstance(other, Default):
            return NotImplemented
        return self.value == other.value


class NoDefault(object):
    pass


def normalize_key(key):
    """Normalize a config key.

    Returns the same key, with only lower-case characters and no '-'.
    """
    return key.lower().replace('-', '_')


class NormalizedDict(dict):
    """A dict whose lookups are performed on normalized keys."""

    def __init__(self, *args, **kwargs):
        d = dict(*args, **kwargs)
        super(NormalizedDict, self).__init__()
        for k, v in d.items():
            self[k] = v

    def __getitem__(self, key):
        return super(NormalizedDict, self).__getitem__(normalize_key(key))

    def __setitem__(self, key, value):
        super(NormalizedDict, self).__setitem__(normalize_key(key), value)

    def setdefault(self, key, default):
        return super(NormalizedDict, self).setdefault(normalize_key(key), default)

    def get(self, key, default=None):
        return super(NormalizedDict, self).get(normalize_key(key), default)

    def pop(self, key, *args):
        return super(NormalizedDict, self).pop(normalize_key(key), *args)


class DictNamespace(dict):
    """Convert a 'Namespace' into a dict-like object."""

    def __init__(self, ns):
        return super(DictNamespace, self).__init__(vars(ns))


class MergedConfig(object):
    """A merged configuration holder.

    Merges options from a set of dicts."""

    def __init__(self, *options, **kwargs):
        self.options = []
        for option in options:
            self.add_options(option)

    def add_options(self, options, normalize=True):
        if normalize:
            options = NormalizedDict(options)
        self.options.append(options)

    def get(self, key, default=NoDefault):
        """Retrieve a value from its key.

        Retrieval steps are:
        1) Normalize the key
        2) For each option group:
           a) Retrieve the value at that key
           b) If no value exists, continue
           c) If the value is an instance of 'Default', continue
           d) Otherwise, return the value
        3) If no option had a non-default value for the key, return the
            first Default() option for the key (or :arg:`default`).
        """
        key = normalize_key(key)
        if default is NoDefault:
            defaults = []
        else:
            defaults = [default]

        for options in self.options:
            try:
                value = options[key]
            except KeyError:
                continue

            if isinstance(value, Default):
                defaults.append(value.value)
                continue
            else:
                return value

        if defaults:
            return defaults[0]

        return NoDefault

    def __repr__(self):   # pragma: no cover
        return '%s(%r)' % (self.__class__.__name__, self.options)
