# %%
#!%cd ~/dev/downward/src/translate

# %%
from collections import defaultdict
from typing import Any, Tuple

from translate.sas_tasks import SASTask, VarValPair
from scoping.actions import VarValAction
from scoping.factset import FactSet
from scoping.merging import merge
from scoping.task import ScopingTask


def filter_causal_links(
    facts: FactSet,
    init: list[VarValPair],
    actions: set[VarValAction],
    enable_fact_based: bool = False,
) -> FactSet:
    """Remove any facts from `facts` that are present in the initial state `init` and
    unthreatened by any of the `actions`."""
    affected_facts = FactSet()
    for a in actions:
        affected_facts.add(a.effect)

    def benign_sets(val):
        return [set(), set([val])] if enable_fact_based else [set()]

    unthreatened_init_facts = [
        (var, val) for (var, val) in init if affected_facts[var] in benign_sets(val)
    ]
    unthreatened_init_facts = FactSet(unthreatened_init_facts)
    relevant_facts = FactSet()
    for var, values in facts:
        for val in values:
            if (var, val) not in unthreatened_init_facts:
                relevant_facts.add(var, val)
    return relevant_facts


def get_goal_relevant_actions(
    facts: FactSet, actions: list[VarValAction]
) -> list[VarValAction]:
    """Find all actions that achieve at least one fact in `facts`."""
    # The same action may achieve multiple facts, so we de-duplicate with a set
    return list(set([a for a in actions for fact in a.effect if fact in facts]))


def partition_actions(
    relevant_variables: list[Any], actions: list[VarValAction]
) -> list[list[VarValAction]]:
    """Partition actions by (effect, cost), ignoring irrelevant variables"""
    # TODO: replace with hash map
    unique_effects_and_costs = defaultdict(list)
    for a in actions:
        unique_effects_and_costs[a.effect_hash(relevant_variables)].append(a)
    # unique_effects_and_costs = set([a.effect_hash(relevant_variables) for a in actions])
    effect_cost_partitions = unique_effects_and_costs.values()
    # for effect_cost in unique_effects_and_costs:
    #     matching_actions = [
    #         a for a in actions if a.effect_hash(relevant_variables) == effect_cost
    #     ]
    #     effect_cost_partitions.append(matching_actions)
    return effect_cost_partitions


def coarsen_facts_to_variables(facts: FactSet, domains: FactSet) -> FactSet:
    for var, _ in facts:
        facts.union(var, domains[var])


def get_goal_relevant_facts(
    domains: FactSet,
    relevant_facts: FactSet,
    relevant_actions: list[VarValAction],
    enable_merging: bool = False,
) -> tuple[FactSet, dict]:
    """Find all facts that appear in the (simplified) preconditions
    of the (possibly merged) relevant actions."""
    relevant_vars = relevant_facts.variables
    if enable_merging:
        action_partitions = partition_actions(relevant_vars, relevant_actions)
    else:
        # make an separate partition for each action
        action_partitions = list(map(lambda x: [x], relevant_actions))

    relevant_facts = FactSet()
    aggregated_info = defaultdict(int)
    for actions in action_partitions:
        relevant_precond_facts, info = merge(actions, relevant_vars, domains)
        for key, val in info.items():
            aggregated_info[key] += val
        relevant_facts.union(relevant_precond_facts)

    return relevant_facts, aggregated_info


def goal_relevance_step(
    domains: FactSet,
    facts: FactSet,
    init: list[VarValPair],
    actions: list[VarValAction],
    relevant_actions: list[VarValAction],
    enable_merging: bool = False,
    enable_causal_links: bool = False,
    enable_fact_based: bool = False,
) -> Tuple[FactSet, list[VarValAction], dict]:
    if enable_causal_links:
        filtered_facts = filter_causal_links(
            facts, init, relevant_actions, enable_fact_based=enable_fact_based
        )
    else:
        filtered_facts = facts
    if not enable_fact_based:
        coarsen_facts_to_variables(filtered_facts, domains)
    relevant_actions = get_goal_relevant_actions(filtered_facts, actions)
    relevant_facts, info = get_goal_relevant_facts(
        domains,
        filtered_facts,
        relevant_actions,
        enable_merging=enable_merging,
    )
    relevant_facts.union(filtered_facts)

    return relevant_facts, relevant_actions, info


def compute_goal_relevance(
    scoping_task: ScopingTask,
    enable_merging: bool = False,
    enable_causal_links: bool = False,
    enable_fact_based: bool = False,
) -> Tuple[FactSet, list[VarValAction], dict]:
    relevant_facts = FactSet(scoping_task.goal)
    if not enable_fact_based:
        coarsen_facts_to_variables(relevant_facts, scoping_task.domains)
    relevant_actions = []
    prev_facts = None
    prev_actions = []
    while relevant_facts != prev_facts or len(relevant_actions) != len(prev_actions):
        prev_facts, prev_actions = relevant_facts, relevant_actions
        relevant_facts, relevant_actions, info = goal_relevance_step(
            scoping_task.domains,
            relevant_facts,
            scoping_task.init,
            scoping_task.actions,
            relevant_actions,
            enable_merging,
            enable_causal_links,
            enable_fact_based=enable_fact_based,
        )
    relevant_facts.add(scoping_task.init)
    return relevant_facts, relevant_actions, info


# %%
if __name__ == "main":
    import options
    from translate import pddl_parser
    from scoping.sas_parser import SasParser
    from translate import pddl_to_sas

    # domain_filename = "../../../scoping/domains/propositional/ipc/gripper/domain.pddl"
    # task_filename = "../../../scoping/domains/propositional/ipc/gripper/prob04.pddl"

    domain_filename = (
        "../../../scoping/domains/propositional/toy-minecraft/toy-example.pddl"
    )
    task_filename = (
        "../../../scoping/domains/propositional/toy-minecraft/example-2.pddl"
    )
    options.keep_unimportant_variables = True
    options.keep_unreachable_facts = True
    options.sas_file = True
    task = pddl_parser.open(domain_filename, task_filename)
    sas_task: SASTask = pddl_to_sas(task)

    # %%
    # sas_path = "../../toy-minecraft-merging.sas"
    # parser = SasParser(pth=sas_path)
    # parser.parse()
    # sas_task: SASTask = parser.to_fd()

    # %%
    # sas_task.dump()

    for merging in [False, True]:
        for causal_links in [False, True]:
            facts, actions, info = compute_goal_relevance(
                sas_task,
                enable_merging=merging,
                enable_causal_links=causal_links,
            )
            print(f"{merging=}")
            print(f"{causal_links=}")
            print("actions:", len(actions), sorted(a.name for a in actions))
            print("facts:", sorted(facts))
            print()
