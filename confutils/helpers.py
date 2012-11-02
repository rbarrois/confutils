# -*- coding: utf-8 -*-
# This code is distributed under the two-clause BSD license.
# Copyright (c) 2012 Raphaël Barrois


class DictMixin(object):
    """Help implementing dict-like classes from a limited set of methods.

    Subclasses should only implement a handful of methods.
    """
    def __getitem__(self, key):
        raise NotImplementedError()

    def __setitem__(self, key, value):
        raise NotImplementedError()

    def __delitem__(self, key):
        raise NotImplementedError()

    def iteritems(self):
        raise NotImplementedError()

    def __len__(self):
        return len(self.items())

    def __contains__(self, key):
        try:
            self[key]
        except KeyError:
            return False
        return True

    def __iter__(self):
        for key, _value in self.iteritems():
            yield key

    def setdefault(self, key, default=None):
        if key not in self:
            self[key] = default
        return self[key]

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    class __NoDefault(object):
        """Private argument marker for pop()."""
        pass

    def pop(self, key, default=__NoDefault):
        try:
            prev = self[key]
        except KeyError:
            if default == self.__NoDefault:
                raise
            else:
                return default

        del self[key]
        return prev

    def iterkeys(self):
        for key, _value in self.iteritems():
            yield key

    def itervalues(self):
        for _key, value in self.iteritems():
            yield value

    def items(self):
        return list(self.iteritems())

    def keys(self):
        return list(self.iterkeys())

    def values(self):
        return list(self.itervalues())

