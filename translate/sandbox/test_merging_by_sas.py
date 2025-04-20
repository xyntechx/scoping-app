# %%
#!%cd ~/dev/downward/src/translate

# %%
from typing import Dict, List, Set, Tuple, Union
import sys

import pddl_parser

from translate.sas_tasks import VarValPair
from scoping.actions import VarValAction
from scoping.merging import merge

import options
from translate import pddl_to_sas

# %% Hack argv to make translate work with ipython
domain_filename = (
    "../../../scoping/domains/propositional/toy-minecraft/toy-example.pddl"
)
task_filename = "../../../scoping/domains/propositional/toy-minecraft/example-1.pddl"
options.keep_unimportant_variables = True
task = pddl_parser.open(domain_filename, task_filename)
sas_task = pddl_to_sas(task)
sas_task.dump()

actions = sorted(
    [VarValAction.from_sas(op) for op in sas_task.operators],
    key=lambda a: a.name,
)
variable_domains = {i: set(range(r)) for i, r in enumerate(sas_task.variables.ranges)}

hunt_stv = actions[4]
gather_stv = actions[1]
actions = [hunt_stv, gather_stv]

# %% ---------------------

variable_domains: Dict[str, Set] = {
    "A": {0, 1, 2},
    "B": {0, 1, 2},
    "C": {0, 1},
    "D": {0, 1},
}
preconds = [
    {"B": 2, "C": 1},
    {"A": 1, "B": 2},
    {"A": 2, "B": 2, "C": 0},
    {"A": 0, "B": 2, "C": 0},
    {"B": 0, "C": 1},
    {"A": 1, "B": 0},
    {"A": 2, "B": 0, "C": 0},
    {"A": 0, "B": 0, "C": 0},
    {"C": 0},
    # {"C": 1},
]
variables = [v for v in sorted(variable_domains.keys())]


def precond_to_varval_list(
    variables: List[str], precondition: Dict[str, int]
) -> List[VarValPair]:
    return [(var, precondition[var]) for var in variables if var in precondition]


names = [f"a{i}" for i, _ in enumerate(preconds)]
precond_lists = [precond_to_varval_list(variables, precond) for precond in preconds]
dummy_effects = [[(i, 0) for i, _ in enumerate(variables)] for _ in preconds]
costs = [1 for _ in preconds]

actions = [
    VarValAction(name, pre, eff, cost)
    for name, pre, eff, cost in zip(names, precond_lists, dummy_effects, costs)
]

# %% ----------------------

merge(actions, variable_domains, output_info=True, mode="values")
