# %%
#!%cd ~/dev/downward/src/translate

# %%
from typing import Tuple

from scoping.actions import VarValAction
from scoping.factset import FactSet
from scoping.task import ScopingTask


def reachability_step(
    facts: FactSet,
    actions: list[VarValAction],
) -> Tuple[FactSet, list[VarValAction]]:
    reachable_facts = FactSet(facts)
    reachable_actions = []
    for action in actions:
        if FactSet(action.precondition) in facts:
            reachable_facts.add(action.effect)
            reachable_actions.append(action)
    return reachable_facts, reachable_actions


def compute_reachability(
    scoping_task: ScopingTask,
) -> Tuple[FactSet, list[VarValAction], bool]:
    reachable_facts = FactSet(scoping_task.init)
    reachable_actions = []
    prev_facts = None
    prev_actions = []
    while reachable_facts != prev_facts or len(reachable_actions) != len(prev_actions):
        prev_facts, prev_actions = reachable_facts, reachable_actions
        reachable_facts, reachable_actions = reachability_step(
            reachable_facts,
            actions=scoping_task.actions,
        )
    # If goal is not reachable, task is impossible. Caller should do something smart!
    goal_reachable = FactSet(scoping_task.goal) in reachable_facts

    return reachable_facts, reachable_actions, goal_reachable
