# %reload_ext autoreload
# %autoreload 2
# %%
from scoping.actions import VarValAction
from scoping.factset import FactSet

from merging import merge

actions = [
    VarValAction("a0", [("v4", 1)], [("v4", 0)], 1),
    VarValAction("a1", [("v4", 1), ("v5", 0)], [("v4", 0)], 1),
    VarValAction("a2", [("v4", 1), ("v5", 1)], [("v4", 0)], 1),
    VarValAction("a3", [("v4", 1), ("v5", 4)], [("v4", 0)], 1),
    VarValAction("a4", [("v4", 2), ("v5", 0)], [("v4", 0)], 1),
    VarValAction("a5", [("v4", 2), ("v5", 1)], [("v4", 0)], 1),
    VarValAction("a6", [("v4", 2), ("v5", 2)], [("v4", 0)], 1),
    VarValAction("a7", [("v4", 2), ("v5", 3)], [("v4", 0)], 1),
    VarValAction("b0", [("v4", 1)], [("v4", 0)], 1),
    VarValAction("b1", [("v4", 1), ("v6", 0)], [("v4", 0)], 1),
    VarValAction("b2", [("v4", 1), ("v6", 1)], [("v4", 0)], 1),
    VarValAction("b3", [("v4", 1), ("v6", 4)], [("v4", 0)], 1),
    VarValAction("b4", [("v4", 2), ("v6", 0)], [("v4", 0)], 1),
    VarValAction("b5", [("v4", 2), ("v6", 1)], [("v4", 0)], 1),
    VarValAction("b6", [("v4", 2), ("v6", 2)], [("v4", 0)], 1),
    VarValAction("b7", [("v4", 2), ("v6", 3)], [("v4", 0)], 1),
]
relevant_variables = ["v4"]
variable_domains = FactSet(
    {"v4": {0, 1, 2}, "v5": {0, 1, 2, 3, 4}, "v6": {0, 1, 2, 3, 4}}
)

# %%
relevant_precondition_facts = merge(actions, relevant_variables, variable_domains)
