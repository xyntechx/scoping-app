#!%cd ~/dev/downward/src/translate
#
from scoping.actions import VarValAction
from scoping.forward import compute_reachability
from scoping.factset import FactSet
from scoping.task import ScopingTask


def make_task(
    domains=FactSet(
        {
            "x": {0, 1, 2},
            "y": {0, 1},
            "z": {0, 1, 2},
        }
    ),
    actions=[
        VarValAction("a", [("x", 0)], [("x", 1)], 1),
        VarValAction("b", [("x", 1)], [("x", 2)], 1),
        VarValAction("c", [("y", 0)], [("y", 1)], 1),
        VarValAction("d", [("z", 0)], [("z", 1)], 1),
        VarValAction("e", [("z", 1)], [("z", 2)], 1),
    ],
    init=[
        ("x", 0),
        ("y", 0),
        ("z", 0),
    ],
    goal=[
        ("x", 2),
    ],
):
    return ScopingTask(domains, init, goal, actions)


def test_all_reachable():
    scoping_task = make_task()
    facts, actions, goal_reachable = compute_reachability(scoping_task)

    assert facts == scoping_task.domains
    assert sorted([a.name for a in actions]) == ["a", "b", "c", "d", "e"]
    assert goal_reachable


def test_mid_unreachable():
    scoping_task = make_task(init=[("x", 1), ("y", 1), ("z", 1)], goal=[("x", 0)])
    facts, actions, goal_reachable = compute_reachability(scoping_task)

    assert facts == FactSet({"x": {1, 2}, "y": {1}, "z": {1, 2}})
    assert sorted([a.name for a in actions]) == ["b", "e"]
    assert not goal_reachable


def test_last_unreachable():
    scoping_task = make_task(init=[("x", 2), ("y", 1), ("z", 2)], goal=[("y", 0)])
    facts, actions, goal_reachable = compute_reachability(scoping_task)

    assert facts == FactSet({"x": {2}, "y": {1}, "z": {2}})
    assert sorted([a.name for a in actions]) == []
    assert not goal_reachable


# %%
test_all_reachable()
test_mid_unreachable()
test_last_unreachable()

print("All tests passed.")
