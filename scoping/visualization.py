import math

from scoping.task import ScopingTask, VarValPair, VarValAction
from scoping.options import ScopingOptions
from scoping.backward import goal_relevance_step, coarsen_facts_to_variables
from scoping.forward import reachability_step
from scoping.factset import FactSet


def compute_forward_scoping_layer(
    layer: int,
    task: ScopingTask,
    _: ScopingOptions,
) -> tuple[FactSet, list[VarValAction], bool]:
    reachable_facts = FactSet(task.init)
    reachable_actions = []
    prev_facts = None
    prev_actions = []
    n_levels = 0
    stopped_early = False
    while reachable_facts != prev_facts or len(reachable_actions) != len(prev_actions):
        prev_facts, prev_actions = reachable_facts, reachable_actions
        reachable_facts, reachable_actions = reachability_step(
            reachable_facts,
            actions=task.actions,
        )
        n_levels += 1
        if n_levels >= layer:
            stopped_early = True
            break
    if not stopped_early:
        reachable_facts.add(task.init)
    new_facts = FactSet(
        {var: val for (var, val) in reachable_facts if (var, val) not in prev_facts}
    )
    new_actions = [a for a in reachable_actions if a not in prev_actions]
    return new_facts, new_actions, stopped_early


def compute_backward_scoping_layer(
    layer: int,
    task: ScopingTask,
    options: ScopingOptions,
) -> tuple[FactSet, list[VarValAction], bool]:
    if layer is None:
        layer = math.inf
    enable_merging: bool = options.enable_merging
    enable_causal_links: bool = options.enable_causal_links
    enable_fact_based: bool = options.enable_fact_based

    relevant_facts = FactSet(task.goal)
    if not enable_fact_based:
        coarsen_facts_to_variables(relevant_facts, task.domains)
    relevant_actions = []
    prev_facts = None
    prev_actions = []
    n_levels = 0
    stopped_early = False
    while relevant_facts != prev_facts or len(relevant_actions) != len(prev_actions):
        prev_facts, prev_actions = relevant_facts, relevant_actions
        relevant_facts, relevant_actions, _ = goal_relevance_step(
            task.domains,
            relevant_facts,
            task.init,
            task.actions,
            relevant_actions,
            enable_merging,
            enable_causal_links,
            enable_fact_based=enable_fact_based,
        )
        n_levels += 1
        if n_levels >= layer:
            stopped_early = True
            break
    if not stopped_early:
        relevant_facts.add(task.init)
    new_facts = FactSet(
        {var: val for (var, val) in relevant_facts if (var, val) not in prev_facts}
    )
    new_actions = [a for a in relevant_actions if a not in prev_actions]
    return new_facts, new_actions, stopped_early


class Node:
    def __init__(
        self,
        name: str,
        precondition: list[VarValPair],
        effect: list[VarValPair],
        parents: list["Node"] = None,
    ) -> None:
        self.name = name
        self.precondition = precondition
        self.effect = effect
        self.parents = parents or []
        self.children = []

        self.is_goal = self.name == "goal"
        self.is_init = self.name == "init"
        self.is_star = self.name == "*"

    def __repr__(self) -> str:
        return (
            f"Node('{self.name}', {self.precondition}, {self.effect}, {self.parents})"
        )


def get_scoping_layers(task: ScopingTask, options: ScopingOptions):
    fact_layers: list[FactSet] = []
    actions_layers: list[list[VarValAction]] = []
    layer = 1
    compute_next_scoping_layer = (
        compute_forward_scoping_layer
        if options.enable_forward_pass
        else compute_backward_scoping_layer
    )
    while True:
        facts_layer, actions_layer, stopped_early = compute_next_scoping_layer(
            layer, task, options
        )
        layer += 1
        fact_layers.append(facts_layer)
        actions_layers.append(actions_layer)
        if not stopped_early:
            break
    return list(zip(fact_layers, actions_layers))


def effect(x):
    return x.effect


def precondition(x):
    return x.precondition


def find_successors(
    action: VarValAction,
    fact_filter: FactSet,
    prev_layer: list[Node],
    forward: bool = False,
    variables: bool = False,
):
    if forward:
        source_fn, dest_fn = precondition, effect
    else:
        source_fn, dest_fn = effect, precondition
    action_parents = []
    for fact in source_fn(action):
        if fact in fact_filter:
            # fact just became relevant
            # find first matching node in prev_layer
            # TODO: technically this might be wrong for merging
            for node in prev_layer:
                fact_match = fact in dest_fn(node)
                var_match = fact[0] in [var for var, val in dest_fn(node)]
                if (
                    fact_match or (variables and var_match)
                ) and node not in action_parents:
                    action_parents.append(node)
                    # break
    return action_parents


def build_action_node(
    action: VarValAction,
    fact_filter: FactSet,
    prev_layer: list[Node],
    forward=False,
    variables=False,
):
    successors = find_successors(action, fact_filter, prev_layer, forward, variables)
    return Node(action.name, action.precondition, action.effect, successors)


class TaskGraph():
    def __init__(
        self,
        task: ScopingTask,
        options: ScopingOptions
    ):
        self.layers = []
        forward = options.enable_forward_pass
        variables = not options.enable_fact_based
        nodes = []
        goal_node = Node("goal", task.goal, [], None)
        init_node = Node("init", [], task.init, None)
        star_node = Node("*", [], [], None)
        if forward:
            root_node, final_node = init_node, goal_node
        else:
            root_node, final_node = goal_node, init_node
        nodes.append(root_node)
        prev_layer = [root_node]
        if forward:
            prev_layer.append(star_node)
            nodes.append(star_node)
        self.layers.append(prev_layer)
        for fact_layer, action_layer in get_scoping_layers(task, options):
            child_layer = []
            for action in action_layer:
                action_node = build_action_node(
                    action, fact_layer, prev_layer, forward, variables
                )
                if forward and not action_node.parents:
                    action_node.parents.append(star_node)
                nodes.append(action_node)
                child_layer.append(action_node)
            self.layers.append(child_layer)
            prev_layer = child_layer

        nodes.append(final_node)
        for node in nodes:
            if node.parents:
                for parent in node.parents:
                    if node not in parent.children:
                        parent.children.append(node)

        for node in nodes:
            if node is not final_node and node.name != "*":
                if forward:
                    if FactSet(final_node.precondition) in FactSet(node.effect):
                        node.children.append(final_node)
                else:
                    if FactSet(node.precondition) in FactSet(final_node.effect):
                        node.children.append(final_node)

        self.roots = [root_node]
        if forward:
            self.roots.append(star_node)
        self.final = final_node

        def to_node(action):
            return Node(action.name, action.precondition, action.effect, [])

        node_names = [a.name for a in nodes]
        self.other_nodes = [
            to_node(a) for a in task.actions if a.name not in node_names
        ]
