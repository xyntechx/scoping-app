%cd ~/dev/downward/src/translate

#%%
from collections import namedtuple
from typing import List
import sys

import pddl_parser
import pddl_to_prolog
import build_model
from normalize import normalize
from instantiate import instantiate

domain_filename = '../../../scoping/domains/propositional/toy-minecraft/toy-example.pddl'
task_filename = '../../../scoping/domains/propositional/toy-minecraft/example-1.pddl'
sys.argv.extend([domain_filename, task_filename])

from pddl.actions import PropositionalAction
from scoping.merging import merge_pddl as merge

task = pddl_parser.open()
normalize(task)
prog = pddl_to_prolog.translate(task)
model = build_model.compute_model(prog)

TaskInstantiation = namedtuple('TaskInstantiation', [
    'relaxed_reachable',
    'fluent_facts',
    'actions',
    'goal',
    'axioms',
    'reachable_action_parameters',
])
grounded_task = TaskInstantiation(*instantiate(task, model))
grounded_actions = sorted(grounded_task.actions, key=lambda x: x.name)

gather_sth, gather_stv = grounded_actions[2:4]
hunt_sth, hunt_stv = grounded_actions[8:10]

merge([hunt_sth, gather_sth])

def project_irrelevant_vars(action: PropositionalAction, relevant_vars: List[str]):
    name = action.name
    precondition = action.precondition
    cost = action.cost
    new_action = PropositionalAction(name, precondition, effects=[], cost=cost)
    new_action.add_effects = [(c, e) for c, e in action.add_effects if e.predicate in relevant_vars]
    new_action.del_effects = [(c, e) for c, e in action.del_effects if e.predicate in relevant_vars]
    return new_action

has_food_steve_atom = sorted(list(grounded_task.fluent_facts))[3]
relevant_vars = [has_food_steve_atom.args]
projected_actions = sorted([project_irrelevant_vars(a, relevant_vars) for a in grounded_task.actions], key=lambda x:x.name)

gather_sth, gather_stv = projected_actions[2:4]
hunt_sth, hunt_stv = projected_actions[8:10]

hunt_sth.precondition
merge([hunt_sth, gather_sth])


actions = {a.name: a for a in task.actions}

hunt = actions['hunt']
hunt.precondition.parts

#%% -----------------------------

print(task.domain_name)
print(task.task_name)
print(task.requirements)
print(task.types)
print(task.objects)
print(*task.predicates, sep='\n')
task.axioms
for a in actions.values():
    a.dump()
    print()
print(task.init)
task.goal.dump()

formula_cnf, formula_dnf = merge([actions[name] for name in ['hunt', 'gather']])

formula_dnf.dump()

formula_cnf.dump()
