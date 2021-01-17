from unittest.mock import Mock

import pytest

from veils.veil import Veil
from veils.veil import veil
from veils.unpiercable import Unpiercable, unpiercable


class Foo:
    def __init__(self):
        self._bar_call_count = 0
        self.prop1 = "Property 1"
        self.prop2 = "Property 2"

    def bar(self):
        return 42

    def baz(self, name):
        return "hello {}".format(name)

    def foo(self, *args, **kwargs):
        return ", ".join(map(str, [*args, kwargs]))

    async def greet_async(self, name):
        return "Asynchronous hello to {}!".format(name)

    async def dummy_async(self):
        return "Dummy async method"

    def __str__(self):
        return "Foo object str"

    def __getitem__(self, item):
        return str(item)


@pytest.mark.parametrize("veil_of", [unpiercable, veil])
def test_dunder(veil_of):
    obj = veil_of(Foo(), methods={"__str__": "Hello, world!", "__getitem__": "42"})
    assert str(obj) == "Hello, world!"
    assert obj["foo"] == "42"


def test_dunder_piercing():
    obj = veil(Foo(), methods={"__str__": "Hello, world!", "__getitem__": "42"})
    assert str(obj) == "Hello, world!", "should return cached value"
    assert obj["foo"] == "42", "should return cached value"
    assert obj.bar() == 42
    assert str(obj) == "Foo object str", "should be pierced"
    assert obj["foo"] == "foo", "should be pierced"


@pytest.mark.parametrize("veil_class", [veil, Veil])
def test_veil_piercing(veil_class):
    """
    Should pierce after calling a method that is not cached
    """
    veiled = veil_class(Foo(), methods={"bar": 69})
    for _ in range(10):
        assert veiled.bar() == 69

    assert veiled.baz("Donald") == "hello Donald"
    assert veiled.bar() == 42


@pytest.mark.parametrize("veil_class", [veil, Veil])
def test_veild_piercing_async(veil_class):
    """
    Should pierce after calling an async method that is not cached
    """
    veiled = veil_class(Foo(), methods={"bar": 69})
    for _ in range(10):
        assert veiled.bar() == 69

    assert veiled.baz("Donald") == "hello Donald"
    assert veiled.bar() == 42


@pytest.mark.parametrize("veil_class", [veil, Veil])
def test_veil_piercing_prop(veil_class):
    """
    Should pierce after accessing a property that is not cached
    """
    veiled = veil_class(Foo(), methods={"bar": 69}, props={"prop1": "Cached prop1"})
    assert veiled.prop1 == "Cached prop1"
    assert veiled.bar() == 69
    assert veiled.prop2 == "Property 2"
    assert veiled.prop1 == "Property 1"


@pytest.mark.asyncio
@pytest.mark.parametrize("veil_class", [veil, Veil, unpiercable, Unpiercable])
async def test_veil_simple_with_args(veil_class):
    veiled = veil_class(
        Foo(),
        methods={"bar": 69, "baz": "Don't care! Veiled!"},
        async_methods={"greet_async": "Cached greet async"},
        props={"prop1": "Veiled prop1!", "prop2": "Veiled prop2!"},
    )
    assert veiled.bar() == 69
    assert veiled.baz("Donald") == "Don't care! Veiled!"
    assert await veiled.greet_async("Donald") == "Cached greet async"
    assert (
        veiled.foo("Some", "Args", keyword_args="Too")
        == "Some, Args, {'keyword_args': 'Too'}"
    )


@pytest.mark.parametrize("veil_class", [veil, Veil, unpiercable, Unpiercable])
def test_veil_isinstance(veil_class):
    assert isinstance(veil_class(Foo()), Foo)


@pytest.mark.asyncio
@pytest.mark.parametrize("veil_class", [unpiercable, Unpiercable])
async def test_unpiercable(veil_class):
    """
    Should not get pierced even after accessing any property or method
    """
    veiled = veil_class(
        Foo(),
        methods={"bar": 69},
        async_methods={"dummy_async": "Decorated dummy"},
        props={"prop1": "Cached prop1"},
    )

    assert veiled.bar() == 69
    assert veiled.baz("Donald") == "hello Donald"
    assert veiled.bar() == 69
    assert veiled.prop2 == "Property 2"
    assert veiled.prop1 == "Cached prop1"
    assert await veiled.greet_async("Donald") == "Asynchronous hello to Donald!"
    assert await veiled.dummy_async() == "Decorated dummy"


@pytest.mark.asyncio
@pytest.mark.parametrize("veil_class", [veil, Veil, unpiercable, Unpiercable])
async def test_not_calling_decorated(veil_class):
    mock = Mock()
    veiled = veil_class(
        mock,
        methods={"bar": 69},
        async_methods={"dummy_async": "Decorated dummy"},
    )
    assert veiled.bar() == 69
    assert await veiled.dummy_async() == "Decorated dummy"
    mock.bar.assert_not_called()
    mock.dummy_async.assert_not_called()


@pytest.mark.parametrize("veil_class", [veil, Veil, unpiercable, Unpiercable])
def test_repr(veil_class):
    obj = Foo()
    veiled = veil_class(obj, methods={"bar": 69})
    assert repr(veiled) == "<{} at 0x{:x} for {} at 0x{:x}>".format(
        type(veiled).__name__, id(veiled), type(obj).__name__, id(obj)
    )
    assert veiled.bar() == 69, "should not be pierced"
