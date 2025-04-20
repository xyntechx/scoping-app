#!%cd ~/dev/downward/src/translate

from scoping.actions import VarValAction

a1 = VarValAction(
    "a1",
    [("x", 0), ("y", 0)],
    [("x", 2), ("y", 2)],
    1,
)


def test_exact_state():
    state = [("x", 0), ("y", 0)]
    assert a1.can_run(state)


def test_more_specific():
    state = [("x", 0), ("y", 0), ("z", 0)]
    assert a1.can_run(state)


def test_less_specific():
    state = [("x", 0)]
    assert not a1.can_run(state)


def test_wrong_x():
    state = [("x", 1), ("y", 0)]
    assert not a1.can_run(state)


def test_wrong_y():
    state = [("x", 0), ("y", 1)]
    assert not a1.can_run(state)


test_exact_state()
test_more_specific()
test_less_specific()
test_wrong_x()
test_wrong_y()

print("All tests passed.")
