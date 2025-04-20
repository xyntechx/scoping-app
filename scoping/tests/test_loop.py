#!%cd ~/dev/downward/src/translate
# %%

from scoping.actions import VarValAction
from scoping.core import scope
from scoping.factset import FactSet
from scoping.options import ScopingOptions
from scoping.task import ScopingTask
from scoping.visualization import TaskGraph

# %%


def make_task(
    domains=FactSet(
        {
            "v": {0, 1},
            "w": {0, 1},
            "x": {0, 1},
            "y": {0, 1},
            "z": {0, 1, 2},
        }
    ),
    actions=[
        VarValAction("a", [("w", 0)], [("w", 1)], 1),
        VarValAction("b", [("w", 1)], [("x", 1)], 1),
        VarValAction("c", [("x", 1), ("y", 1)], [("z", 2)], 1),
        VarValAction("d", [("w", 0)], [("x", 1)], 1),
        VarValAction("e", [("x", 1), ("y", 0)], [("z", 2)], 1),
        VarValAction("f", [("x", 0), ("y", 0)], [("z", 2)], 1),
        VarValAction("g", [], [("v", 0)], 1),
        VarValAction("h", [("v", 0)], [("y", 0)], 1),
        VarValAction("i", [("x", 0)], [("z", 1)], 1),
    ],
    init=[
        ("v", 0),
        ("w", 0),
        ("x", 0),
        ("y", 0),
        ("z", 0),
    ],
    goal=[
        ("z", 2),
    ],
):
    return ScopingTask(domains, init, goal, actions)


def test_none():
    scoping_task = make_task()
    scoped_task = scope(scoping_task, ScopingOptions(0, 0, 0, 0, 0))

    assert scoped_task.domains == scoping_task.domains
    assert sorted(a.name for a in scoped_task.actions) == list("abcdefghi")


def test_values():
    scoping_task = make_task()
    scoped_task = scope(scoping_task, ScopingOptions(0, 0, 1, 0, 0))

    assert scoped_task.domains == FactSet(
        {"w": {0, 1}, "x": {0, 1}, "y": {0, 1}, "z": {0, 2}}
    )
    assert sorted(a.name for a in scoped_task.actions) == list("abcdefgh")


def test_merge():
    scoping_task = make_task()
    scoped_task = scope(scoping_task, ScopingOptions(0, 1, 0, 0, 0))

    assert scoped_task.domains == scoping_task.domains
    assert sorted(a.name for a in scoped_task.actions) == list("bcdefghi")


def test_cl():
    scoping_task = make_task()
    scoped_task = scope(scoping_task, ScopingOptions(1, 0, 0, 0, 0))

    assert scoped_task.domains == FactSet(
        {"w": {0, 1}, "x": {0, 1}, "y": {0, 1}, "z": {0, 1, 2}}
    )
    assert sorted(a.name for a in scoped_task.actions) == list("abcdefhi")


def test_cl_values():
    scoping_task = make_task()
    scoped_task = scope(scoping_task, ScopingOptions(1, 0, 1, 0, 0))

    assert scoped_task.domains == FactSet(
        {"w": {0, 1}, "x": {0, 1}, "y": {0, 1}, "z": {0, 2}}
    )
    assert sorted(a.name for a in scoped_task.actions) == list("abcdef")


def test_merge_values():
    scoping_task = make_task()
    scoped_task = scope(scoping_task, ScopingOptions(0, 1, 1, 0, 0))

    assert scoped_task.domains == FactSet(
        {"w": {0, 1}, "x": {0, 1}, "y": {0, 1}, "z": {0, 2}}
    )
    assert sorted(a.name for a in scoped_task.actions) == list("bcdefgh")


def test_cl_merge():
    scoping_task = make_task()
    scoped_task = scope(scoping_task, ScopingOptions(1, 1, 0, 0, 0))

    assert scoped_task.domains == FactSet(
        {"w": {0, 1}, "x": {0, 1}, "y": {0, 1}, "z": {0, 1, 2}}
    )
    assert sorted(a.name for a in scoped_task.actions) == list("bcdefhi")


def test_cl_merge_values():
    scoping_task = make_task()
    scoped_task = scope(scoping_task, ScopingOptions(1, 1, 1, 0, 0))

    assert scoped_task.domains == FactSet(
        {"w": {0, 1}, "x": {0, 1}, "y": {0, 1}, "z": {0, 2}}
    )
    assert sorted(a.name for a in scoped_task.actions) == list("bcdef")


def test_forward_none():
    scoping_task = make_task()
    scoped_task = scope(scoping_task, ScopingOptions(0, 0, 0, 1, 0))

    assert scoped_task.domains == FactSet({"w": {0, 1}, "x": {0, 1}, "z": {0, 1, 2}})
    assert sorted(a.name for a in scoped_task.actions) == list("abdefghi")


def test_forward_cl_merge_values():
    scoping_task = make_task()
    scoped_task = scope(scoping_task, ScopingOptions(1, 1, 1, 1, 0))

    assert scoped_task.domains == FactSet({"x": {0, 1}, "z": {0, 2}})
    assert sorted(a.name for a in scoped_task.actions) == list("def")


def test_loop():
    scoping_task = make_task()
    scoped_task = scope(scoping_task, ScopingOptions(1, 1, 1, 1, 1))

    assert scoped_task.domains == FactSet({"z": {0, 2}})
    assert sorted(a.name for a in scoped_task.actions) == list("f")


# %%
test_none()  # abcdefghi
test_values()  # abcdefgh
test_merge()  # bcdefghi
test_merge_values()  # abcdefhi
test_cl()  # abcdef
test_cl_values()  # bcdefgh
test_cl_merge()  # bcdefhi
test_cl_merge_values()  # bcdef

test_forward_none()  # abdefghi
test_forward_cl_merge_values()  # def
test_loop()  # f

print("All tests passed.")


# %%
scoping_task = make_task()
TaskGraph(scoping_task, ScopingOptions(0, 0, 1, 0, 0))

# %%
scoped_task = scope(scoping_task, ScopingOptions(1, 1, 1, 0, 0, 0))
TaskGraph(scoped_task, ScopingOptions(0, 0, 1, 0, 0))
