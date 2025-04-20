from typing import Any

from translate.normalize import convert_to_DNF
from translate.pddl.conditions import Condition, Disjunction, Conjunction
from translate.pddl.actions import Action, PropositionalAction
from translate.sas_tasks import VarValPair
from scoping.actions import VarValAction
from scoping.factset import FactSet


def get_precondition_facts(action: VarValAction, variable_domains: FactSet) -> FactSet:
    precond_facts = FactSet()
    for var, val in action.precondition:
        if val == -1:
            # TODO: shouldn't these have all been removed during sas parsing?
            precond_facts.union(var, variable_domains[var])
        else:
            precond_facts.add(var, val)
    return precond_facts


def simplify_tautologies(
    partial_states: set[tuple[VarValPair]],
    all_precond_vars: set[Any],
    variable_domains: FactSet,
):
    """Condense the partial states by removing any unconstrained variables"""
    removed_vars = []
    for removed_var in all_precond_vars:
        partial_states_without_var = {
            tuple((var, val) for var, val in partial_state if var != removed_var)
            for partial_state in partial_states
        }

        if len(partial_states_without_var) * len(variable_domains[removed_var]) == len(
            partial_states
        ):
            partial_states = partial_states_without_var
            removed_vars.append(removed_var)
    return partial_states


def select_actions_matching_var(
    actions: list[VarValAction], var: Any
) -> list[VarValAction]:
    """Select actions that have a specific variable in their precondition"""
    selected_actions = []
    for action in actions:
        if any(a_var == var for a_var, _ in action.precondition):
            selected_actions.append(action)
    return selected_actions


def select_actions_matching_precond(
    actions: list[VarValAction], precond: list[VarValPair], free_var: Any
) -> list[VarValAction]:
    """Select actions that have a specific precondition, not accounting for free_var"""
    selected_actions = []
    for action in actions:
        precond_without_var = sorted(
            [(var, val) for var, val in action.precondition if var != free_var]
        )
        if precond_without_var == sorted(precond):
            selected_actions.append(action)
    return selected_actions


def merge(
    actions: list[VarValAction],
    relevant_variables: list[Any],
    variable_domains: FactSet,
) -> tuple[FactSet, dict]:
    """Get the relevant precondition facts after merging actions"""
    info = {
        "Scoping merge attempts": 0,
    }
    if len(actions) == 1:
        return get_precondition_facts(actions[0], variable_domains), info
    h0 = actions[0].effect_hash(relevant_variables)
    for a in actions[1:]:
        h = a.effect_hash(relevant_variables)
        assert h == h0, "Attempted to merge skills with different effects/costs"
    info["Scoping merge attempts"] += 1

    # Merging only helps if at least one variable spans its whole domain
    precond_facts = FactSet()
    is_empty_precondition = False
    for a in actions:
        precond_facts.union(get_precondition_facts(a, variable_domains))
        if not a.precondition:
            is_empty_precondition = True
    if is_empty_precondition:
        if all([len(action.precondition) == 0 for action in actions]):
            info["Scoping merge attempts"] = 0
        return FactSet(), info
    spanning_vars = [
        var for var, values in precond_facts if values == variable_domains[var]
    ]
    if not spanning_vars:
        return precond_facts, info

    relevant_precond_facts = FactSet()
    visited_action_names = set()
    for var_to_remove in spanning_vars:
        # find all actions that have this variable in their precondition
        # and look for ways to simplify the preconditions
        matching_actions = select_actions_matching_var(actions, var_to_remove)
        if not matching_actions:
            # no actions have this variable in their precondition, so the
            # variable can be deleted, and there are no relevant facts to add
            continue

        # compute the unique preconditions for the actions, excluding this variable
        preconds_without_var = [
            [(var, val) for var, val in action.precondition if var != var_to_remove]
            for action in matching_actions
        ]
        unique_preconds_without_var = set(
            [tuple(sorted(precond)) for precond in preconds_without_var]
        )
        for precond_without_var in unique_preconds_without_var:
            # get all actions that match this partial precondition
            considered_actions = select_actions_matching_precond(
                actions, precond_without_var, var_to_remove
            )

            # get list of values of var_to_remove required for the considered_actions
            var_to_remove_values = [
                FactSet(a.precondition)[var_to_remove] for a in considered_actions
            ]
            var_to_remove_values = set().union(
                *[
                    val_set if val_set else variable_domains[var_to_remove]
                    for val_set in var_to_remove_values
                ]
            )

            # check if all possible values of var_to_remove are covered by some action
            if var_to_remove_values != variable_domains[var_to_remove]:
                # not all possible values of the variable are covered by some action
                # so we need to store the var_to_remove facts
                relevant_precond_facts.add(
                    (var_to_remove, val) for val in var_to_remove_values
                )
            # either way, we need to store the precondition facts without the variable
            relevant_precond_facts.add(precond_without_var)

            # mark the considered_actions as visited
            for a in considered_actions:
                visited_action_names.add(a.name)

    # We should have marked actions as visited already so there shouldn't be too
    # many left to consider. There are no variables to remove in these actions,
    # because we've already tried to remove all possible variables. so we just mark
    # their preconditions as relevant.
    for action in actions:
        if action.name not in visited_action_names:
            relevant_precond_facts.add(action.precondition)

    return relevant_precond_facts, info


def merge_pddl(actions: list[(Action | PropositionalAction)]):
    # Check if actions have same effects (on relevant vars)!
    #  - either pass relevant_vars as input to merge()
    #  - or scope the actions so they don't include irrelevant vars before sending to merge()
    h0 = actions[0].hashable()
    for a in actions[1:]:
        h = a.hashable()
        assert h == h0, "Attempted to merge skills with different effects"
    if isinstance(actions[0], PropositionalAction):
        get_precond = lambda action: Conjunction(action.precondition)
    else:
        get_precond = lambda action: action.precondition
    formula_dnf = Disjunction([get_precond(a) for a in actions])
    formula_cnf = dnf2cnf(formula_dnf)
    return formula_cnf, formula_dnf


def fully_simplify(formula: Condition, max_iters: int = 10):
    result = formula
    for _ in range(max_iters):
        simplified = result.simplified()
        if simplified == result:
            break
        else:
            result = simplified
    return result


def dnf2cnf(formula: Disjunction):
    """Convert formula ϕ to CNF"""
    formula = fully_simplify(formula)
    # print('ϕ')
    # formula.dump()

    # 1. negate ϕ => ¬ϕ
    negated_formula = fully_simplify(formula.negate())
    # print('¬ϕ')
    # negated_formula.dump()

    # 2. convert ¬ϕ to DNF
    negated_DNF = fully_simplify(convert_to_DNF(negated_formula))
    # print('(¬ϕ)_DNF')
    # negated_DNF.dump()

    # 3. negate result and simplify
    cnf = fully_simplify(negated_DNF.negate())
    # print('CNF')
    # cnf.dump()

    return cnf
