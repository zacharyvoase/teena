import weakref

__all__ = ['cached_property']


class CachedProperty(object):

    __slots__ = ('func', 'cache')

    def __init__(self, func):
        self.func = func
        self.cache = weakref.WeakKeyDictionary()

    def __get__(self, obj, type=None):
        if obj is None:  # the property was accessed on the class.
            return self
        if obj not in self.cache:
            self.cache[obj] = val = CachedPropertyValue(is_computed=True,
                                                        value=self.func(obj))
            return val.value
        val = self.cache[obj]
        if val.is_present:
            if val.is_computed:
                return val.value
            val.value = result = self.func(obj)
            val.is_computed = True
            return result
        raise AttributeError('%r has no attribute %r' %
                             (obj, self.func.__name__))

    def __set__(self, obj, value):
        if obj not in self.cache:
            self.cache[obj] = CachedPropertyValue(is_computed=True,
                                                  value=value)
        else:
            val = self.cache[obj]
            val.is_computed = True
            val.value = value

    def __delete__(self, obj):
        self.cache[obj] = CachedPropertyValue(is_present=False)


# An alias, for naming consistency with `property`.
cached_property = CachedProperty


class CachedPropertyValue(object):

    __slots__ = ('is_present', 'is_computed', 'value')

    def __init__(self, is_present=True, is_computed=False, value=None):
        self.is_present = is_present
        self.is_computed = is_computed
        self.value = value
