# %%
from scoping.actions import VarValAction
from scoping.factset import FactSet
from scoping.options import ScopingOptions
from scoping.task import ScopingTask
from scoping.visualization import TaskGraph
from scoping.core import scope


# %%
def make_task(
    domains=FactSet(
        {
            "job": {0, 1},
            "hungry": {0, 1},
            "food": {0, 1},
            "money": {0, 1},
            "serves": {0, 1, 2},
        }
    ),
    actions=[
        VarValAction("a. dance", [("hungry", 0)], [("hungry", 1)], 1),
        VarValAction("d. hunt", [("hungry", 0)], [("food", 1)], 1),
        VarValAction("c. cook", [("food", 1), ("money", 0)], [("serves", 2)], 1),
        VarValAction("b. gather", [("hungry", 1)], [("food", 1)], 1),
        VarValAction("e. hire_chef", [("food", 1), ("money", 1)], [("serves", 2)], 1),
        VarValAction("f. takeout", [("food", 0), ("money", 1)], [("serves", 2)], 1),
        VarValAction("g. get_job", [], [("job", 1)], 1),
        VarValAction("h. work", [("job", 1)], [("money", 1)], 1),
        VarValAction("i. leftovers", [("food", 0)], [("serves", 1)], 1),
    ],
    init=[
        ("job", 1),
        ("hungry", 0),
        ("food", 0),
        ("money", 1),
        ("serves", 0),
    ],
    goal=[
        ("serves", 2),
    ],
):
    return ScopingTask(domains, init, goal, actions)


# %%
scoping_task = make_task()
TaskGraph(scoping_task, ScopingOptions(0, 0, 1, 0, 0), XSCALE=1, YSCALE=1).show()

# %%
scoped_task = scope(scoping_task, ScopingOptions(1, 1, 1, 1, 1))
TaskGraph(scoped_task, ScopingOptions(0, 0, 0, 0, 0))