#! /usr/bin/env python3


from collections import deque, defaultdict
import itertools
import random
import time
from typing import List

from translate import invariants, options, pddl, timers

class BalanceChecker:
    def __init__(self, task, reachable_action_params):
        self.predicates_to_add_actions = defaultdict(list)
        self.random = random.Random(314159)
        self.action_to_heavy_action = {}
        for act in task.actions:
            action = self.add_inequality_preconds(act, reachable_action_params)
            too_heavy_effects = []
            create_heavy_act = False
            heavy_act = action
            for eff in action.effects:
                too_heavy_effects.append(eff)
                if eff.parameters: # universal effect
                    create_heavy_act = True
                    too_heavy_effects.append(eff.copy())
                if not eff.literal.negated:
                    predicate = eff.literal.predicate
                    add_actions = self.predicates_to_add_actions[predicate]
                    if not add_actions or add_actions[-1] is not action:
                        add_actions.append(action)
            if create_heavy_act:
                heavy_act = pddl.Action(action.name, action.parameters,
                                        action.num_external_parameters,
                                        action.precondition, too_heavy_effects,
                                        action.cost)
            # heavy_act: duplicated universal effects and assigned unique names
            # to all quantified variables (implicitly in constructor)
            self.action_to_heavy_action[action] = heavy_act

    def get_threats(self, predicate):
        return self.predicates_to_add_actions.get(predicate, list())

    def get_heavy_action(self, action):
        return self.action_to_heavy_action[action]

    def add_inequality_preconds(self, action, reachable_action_params):
        if reachable_action_params is None or len(action.parameters) < 2:
            return action
        inequal_params = []
        combs = itertools.combinations(range(len(action.parameters)), 2)
        for pos1, pos2 in combs:
            for params in reachable_action_params[action]:
                if params[pos1] == params[pos2]:
                    break
            else:
                inequal_params.append((pos1, pos2))

        if inequal_params:
            precond_parts = [action.precondition]
            for pos1, pos2 in inequal_params:
                param1 = action.parameters[pos1].name
                param2 = action.parameters[pos2].name
                new_cond = pddl.NegatedAtom("=", (param1, param2))
                precond_parts.append(new_cond)
            precond = pddl.Conjunction(precond_parts).simplified()
            return pddl.Action(
                action.name, action.parameters, action.num_external_parameters,
                precond, action.effects, action.cost)
        else:
            return action

def get_fluents(task):
    fluent_names = set()
    for action in task.actions:
        for eff in action.effects:
            fluent_names.add(eff.literal.predicate)
    return [pred for pred in task.predicates if pred.name in fluent_names]

def get_initial_invariants(task):
    for predicate in get_fluents(task):
        all_args = list(range(len(predicate.arguments)))
        part = invariants.InvariantPart(predicate.name, all_args, None)
        yield invariants.Invariant((part,))
        for omitted in range(len(predicate.arguments)):
            inv_args = (all_args[0:omitted] + [invariants.COUNTED] +
                        all_args[omitted:-1])
            part = invariants.InvariantPart(predicate.name, inv_args, omitted)
            yield invariants.Invariant((part,))

def find_invariants(task, reachable_action_params):
    limit = options.invariant_generation_max_candidates
    candidates = deque(itertools.islice(get_initial_invariants(task), 0, limit))
    print(len(candidates), "initial candidates")
    seen_candidates = set(candidates)

    balance_checker = BalanceChecker(task, reachable_action_params)

    def enqueue_func(invariant):
        if len(seen_candidates) < limit and invariant not in seen_candidates:
            candidates.append(invariant)
            seen_candidates.add(invariant)

    start_time = time.process_time()
    while candidates:
        candidate = candidates.popleft()
        if time.process_time() - start_time > options.invariant_generation_max_time:
            print("Time limit reached, aborting invariant generation")
            return
        if candidate.check_balance(balance_checker, enqueue_func):
            yield candidate

def useful_groups(invariants, initial_facts):
    predicate_to_invariants = defaultdict(list)
    for invariant in invariants:
        for predicate in invariant.predicates:
            predicate_to_invariants[predicate].append(invariant)

    nonempty_groups = dict() # dict instead of set because it is stable
    overcrowded_groups = set()
    for atom in initial_facts:
        if isinstance(atom, pddl.Assign):
            continue
        for invariant in predicate_to_invariants.get(atom.predicate, ()):
            parameters = invariant.get_parameters(atom)
            # we need to make the parameters dictionary hashable, so
            # we store the values as a tuple
            parameters_tuple = tuple(parameters[var]
                                     for var in range(invariant.arity()))

            group_key = (invariant, parameters_tuple)
            if group_key not in nonempty_groups:
                nonempty_groups[group_key] = True
            else:
                overcrowded_groups.add(group_key)
    useful_groups = [group_key for group_key in nonempty_groups.keys()
                     if group_key not in overcrowded_groups]
    for (invariant, parameters) in useful_groups:
        yield [part.instantiate(parameters) for part in sorted(invariant.parts)]

# returns a list of mutex groups (parameters instantiated, counted variables not)
def get_groups(task, reachable_action_params=None) -> List[List[pddl.Atom]]:
    with timers.timing("Finding invariants", block=True):
        invariants = list(find_invariants(task, reachable_action_params))
    with timers.timing("Checking invariant weight"):
        result = list(useful_groups(invariants, task.init))
    return result

if __name__ == "__main__":
    import normalize
    import pddl_parser

    print("Parsing...")
    task = pddl_parser.open()
    print("Normalizing...")
    normalize.normalize(task)
    print("Finding invariants...")
    print("NOTE: not passing in reachable_action_params.")
    print("This means fewer invariants might be found.")
    for invariant in find_invariants(task, None):
        print(invariant)
    print("Finding fact groups...")
    groups = get_groups(task)
    for group in groups:
        print("[%s]" % ", ".join(map(str, group)))
