import uuid

from nose.tools import assert_raises

from teena import cached_property


class Counter(object):
    def __init__(self):
        self.state = {'value': 0}

    @cached_property
    def attr(self):
        self.state['value'] += 1
        return self.state['value']


def test_cached_property_is_computed_on_access():
    counter = Counter()
    initial_state = counter.state.copy()
    value = counter.attr
    final_state = counter.state.copy()
    assert value == 1
    assert initial_state['value'] == 0
    assert final_state['value'] == 1


def test_cached_property_is_only_computed_once():
    counter = Counter()
    assert counter.state['value'] == 0
    first_value = counter.attr
    assert first_value == 1
    assert counter.state['value'] == 1
    second_value = counter.attr
    assert second_value == 1
    assert counter.state['value'] == 1


def test_setting_a_cached_property_overwrites_its_value_entirely():
    # Access, set, access
    counter = Counter()
    first_value = counter.attr
    assert first_value == 1
    counter.attr = 123
    second_value = counter.attr
    assert second_value == 123
    assert counter.state['value'] == 1  # Not recomputed.

    # Set, access
    counter2 = Counter()
    counter2.attr = 123
    value = counter2.attr
    assert value == 123
    assert counter2.state['value'] == 0  # Never computed.


def test_deleting_a_cached_property_removes_it_from_the_instance():
    # Access, delete, access
    counter = Counter()
    counter.attr
    del counter.attr
    assert_raises(AttributeError, lambda: counter.attr)
    assert counter.state['value'] == 1  # Not recomputed.

    # Delete, access
    counter2 = Counter()
    del counter2.attr
    assert_raises(AttributeError, lambda: counter2.attr)
    assert counter2.state['value'] == 0  # Never computed.


def test_the_cached_property_descriptor_is_available_on_the_class():
    assert isinstance(Counter.attr, cached_property)


class MultiCounter(object):
    def __init__(self):
        self.state = {'foo': 0, 'bar': 0}

    @cached_property
    def foo(self):
        self.state['foo'] += 1
        return self.state['foo']

    @cached_property
    def bar(self):
        self.state['bar'] += 1
        return self.state['bar']


def test_can_put_multiple_cached_properties_on_one_instance():
    # Just a sanity check.
    counter = MultiCounter()

    assert counter.foo == 1
    assert counter.state == {'foo': 1, 'bar': 0}

    assert counter.bar == 1
    assert counter.state == {'foo': 1, 'bar': 1}

    counter.foo = 123
    assert counter.foo == 123
    assert counter.state == {'foo': 1, 'bar': 1}

    counter.bar = 456
    assert counter.bar == 456
    assert counter.state == {'foo': 1, 'bar': 1}

    del counter.foo
    assert_raises(AttributeError, lambda: counter.foo)
    assert counter.state == {'foo': 1, 'bar': 1}

    del counter.bar
    assert_raises(AttributeError, lambda: counter.bar)
    assert counter.state == {'foo': 1, 'bar': 1}


class ObjectWithIdentifier(object):

    def __init__(self):
        self.ident = str(uuid.uuid4())
        self.deallocation_flag = [False]

    def __eq__(self, other):
        return (ObjectWithIdentifier, self.ident) == other

    def __del__(self):
        self.deallocation_flag[0] = True

    @cached_property
    def some_property(self):
        return 123


def test_objects_with_cached_properties_can_be_garbage_collected():
    import gc
    obj = ObjectWithIdentifier()
    ident = obj.ident
    dealloc_flag = obj.deallocation_flag

    # Invoke the cached_property.
    obj.some_property

    # The object is tracked by the garbage collector.
    assert any(tracked_obj == (ObjectWithIdentifier, ident)
               for tracked_obj in gc.get_objects()), \
            "The object is not being tracked by the garbage collector"

    # Delete the object and run a full garbage collection.
    del obj
    gc.collect()

    # The object is no longer tracked by the garbage collector.
    assert not any(tracked_obj == (ObjectWithIdentifier, ident)
                   for tracked_obj in gc.get_objects()), \
            "The object is still being tracked by the garbage collector"
    # The object has been deallocated.
    assert dealloc_flag[0], "The object was not deallocated"
