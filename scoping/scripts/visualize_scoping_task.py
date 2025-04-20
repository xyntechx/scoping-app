#!%cd ~/dev/downward/src/translate
# %%

from scoping.actions import VarValAction
from scoping.core import scope
from scoping.factset import FactSet
from scoping.options import ScopingOptions
from scoping.task import ScopingTask
from scoping.visualization import TaskGraph


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


# %%
scoping_task = make_task()
# %%

options = ScopingOptions(1, 1, 1, 0, 0)
TaskGraph(scoping_task, options)

# %%
backward_task = scope(scoping_task, options)
TaskGraph(backward_task, ScopingOptions(0, 0, 0, 1, 0), YSCALE=1)

# %%
forward_task = scope(scoping_task, ScopingOptions(1, 1, 1, 1, 0))
TaskGraph(scoping_task, ScopingOptions(0, 0, 0, 1, 0), YSCALE=1)

# %%
forward_task = scope(scoping_task, ScopingOptions(1, 1, 1, 1, 0))
TaskGraph(forward_task, ScopingOptions(1, 1, 1, 0, 0), YSCALE=1)

# %%
final_task = scope(scoping_task, ScopingOptions(1, 1, 1, 1, 1))
TaskGraph(final_task, ScopingOptions(1, 1, 1, 1, 0), YSCALE=1)
