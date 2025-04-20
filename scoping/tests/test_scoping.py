#!%cd ~/dev/downward/src/translate
# %%

from scoping.actions import VarValAction
from scoping.core import scope
from scoping.factset import FactSet
from scoping.options import ScopingOptions
from scoping.task import ScopingTask


def make_task(
    domains=FactSet({"x": {0, 1, 2, 3}, "y": {0, 1, 2}, "z": {0, 1}}),
    init=[("x", 0), ("y", 0), ("z", 0)],
    goal=[("y", 1)],
    actions=[
        VarValAction("a", [("y", 0)], [("x", 2), ("y", 1), ("z", 0)], 1),
        VarValAction("b", [("z", 0)], [("x", 1), ("y", 1)], 1),
        VarValAction("c", [], [("y", 0), ("z", 0)], 1),
        VarValAction("d", [], [("y", 0)], 1),
        VarValAction("e", [("y", 2), ("z", 0)], [("x", 2), ("y", 0)], 1),
        VarValAction("f", [("x", 1)], [("y", 2)], 1),
        VarValAction("g", [("x", 1)], [("x", 3), ("y", 2)], 1),
        VarValAction("h", [], [("z", 0)], 1),
        VarValAction("i", [("x", 0), ("y", 2)], [("z", 1)], 1),
    ],
):
    return ScopingTask(domains, init, goal, actions)


def test_vars():
    scoping_task = make_task()
    scoped_task = scope(scoping_task, ScopingOptions(0, 0, 0, 0, 0))
    actions = "".join(sorted([a.name for a in scoped_task.actions]))
    domains = scoped_task.domains
    assert domains == FactSet({"x": {0, 1, 2, 3}, "y": {0, 1, 2}, "z": {0, 1}})
    assert actions == "abcdefghi"


def test_cl():
    scoping_task = make_task()
    scoped_task = scope(scoping_task, ScopingOptions(1, 0, 0, 0, 0))
    actions = "".join(sorted([a.name for a in scoped_task.actions]))
    domains = scoped_task.domains
    assert domains == FactSet({"x": {0, 1, 2, 3}, "y": {0, 1, 2}, "z": {0, 1}})
    assert actions == "abcdefghi"


def test_merge():
    scoping_task = make_task()
    scoped_task = scope(scoping_task, ScopingOptions(0, 1, 0, 0, 0))
    actions = "".join(sorted([a.name for a in scoped_task.actions]))
    domains = scoped_task.domains
    assert domains == FactSet({"x": {0, 1, 2, 3}, "y": {0, 1, 2}, "z": {0, 1}})
    assert actions == "abcdefghi"


def test_cl_merge():
    scoping_task = make_task()
    scoped_task = scope(scoping_task, ScopingOptions(1, 1, 0, 0, 0))
    actions = "".join(sorted([a.name for a in scoped_task.actions]))
    domains = scoped_task.domains
    assert domains == FactSet({"x": {0, 1, 2, 3}, "y": {0, 1, 2}, "z": {0, 1}})
    assert actions == "abcdefghi"


def test_forward_vars():
    scoping_task = make_task()
    scoped_task = scope(scoping_task, ScopingOptions(0, 0, 0, 1, 0))
    actions = "".join(sorted([a.name for a in scoped_task.actions]))
    domains = scoped_task.domains
    assert domains == FactSet({"x": {0, 1, 2, 3}, "y": {0, 1, 2}, "z": {0, 1}})
    assert actions == "abcdefghi"


def test_vals():
    scoping_task = make_task()
    scoped_task = scope(scoping_task, ScopingOptions(0, 0, 1, 0, 0))
    actions = "".join(sorted([a.name for a in scoped_task.actions]))
    domains = scoped_task.domains
    assert domains == FactSet({"x": {0, 1, 2, 3}, "y": {0, 1, 2}})
    assert actions == "abcdefgh"


def test_cl_vals():
    scoping_task = make_task()
    scoped_task = scope(scoping_task, ScopingOptions(1, 0, 1, 0, 0))
    actions = "".join(sorted([a.name for a in scoped_task.actions]))
    domains = scoped_task.domains
    assert domains == FactSet({"x": {0, 1, 2, 3}, "y": {0, 1, 2}})
    assert actions == "abcdefg"


def test_merge_vals():
    scoping_task = make_task()
    scoped_task = scope(scoping_task, ScopingOptions(0, 1, 1, 0, 0))
    actions = "".join(sorted([a.name for a in scoped_task.actions]))
    domains = scoped_task.domains
    assert domains == FactSet({"y": {0, 1, 2}})
    assert actions == "abcdeh"


def test_cl_merge_vals():
    scoping_task = make_task()
    scoped_task = scope(scoping_task, ScopingOptions(1, 1, 1, 0, 0))
    actions = "".join(sorted([a.name for a in scoped_task.actions]))
    domains = scoped_task.domains
    assert domains == FactSet({"y": {0, 1, 2}})
    assert actions == "abcde"


def test_forward_cl_merge_vals():
    scoping_task = make_task()
    scoped_task = scope(scoping_task, ScopingOptions(1, 1, 1, 1, 0))
    actions = "".join(sorted([a.name for a in scoped_task.actions]))
    domains = scoped_task.domains
    assert domains == FactSet({"y": {0, 1}})
    assert actions == "abcd"


def test_loop():
    scoping_task = make_task()
    scoped_task = scope(scoping_task, ScopingOptions(1, 1, 1, 1, 1))
    actions = "".join(sorted([a.name for a in scoped_task.actions]))
    domains = scoped_task.domains
    assert domains == FactSet({"y": {0, 1}})
    assert actions == "ab"


# %%
# fmt: off
test_vars()                   # abcdefghi +|-
test_cl()                     # abcdefghi +|-
test_merge()                  # abcdefghi +|-
test_cl_merge()               # abcdefghi +|-
test_forward_vars()           # abcdefghi +|-
test_vals()                   # abcdefgh  +|-         i
test_cl_vals()                # abcdefg   +|-        hi
test_merge_vals()             # abcde  h  +|-      fg i
test_cl_merge_vals()          # abcde     +|-      fghi
test_forward_cl_merge_vals()  # abcd      +|-     efghi
test_loop()                   # ab        +|-   cdefghi
# fmt: on

print("All tests passed.")
