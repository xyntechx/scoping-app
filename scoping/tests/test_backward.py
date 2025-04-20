#!%cd ~/dev/downward/src/translate
#
from scoping.actions import VarValAction
from scoping.backward import compute_goal_relevance
from scoping.factset import FactSet
from scoping.task import ScopingTask


def make_vanilla_task(
    domains=FactSet(
        {
            "x": {0, 1, 2},
            "y": {0, 1},
            "z": {0, 1, 2},
        }
    ),
    actions=[
        VarValAction("a1", [("x", 0)], [("x", 1)], 1),
        VarValAction("a2", [("x", 1)], [("y", 1)], 1),
        VarValAction("a3", [("y", 1)], [("z", 1)], 1),
        VarValAction("b1", [("y", 0)], [("x", 2)], 1),
        VarValAction("b2", [("z", 0)], [("z", 2)], 1),
    ],
    init=[
        ("x", 0),
        ("y", 0),
        ("z", 0),
    ],
    goal=[
        ("x", 1),
    ],
):
    return ScopingTask(domains, init, goal, actions)


def make_merge_task(
    domains=FactSet(
        {
            "x": {0, 1, 2},
            "y": {0, 1},
            "z": {0, 1, 2, 3},
            "w": {0, 1},
        }
    ),
    actions=[
        VarValAction("a1", [("x", 0)], [("x", 1)], 1),
        VarValAction("a2", [("x", 1)], [("y", 1)], 1),
        VarValAction("a3", [("y", 1)], [("z", 1), ("w", 1)], 1),
        VarValAction("a4", [("y", 0)], [("z", 1), ("w", 0)], 1),
    ],
    init=[
        ("x", 0),
        ("y", 0),
        ("z", 0),
    ],
    goal=[
        ("z", 1),
    ],
):
    return ScopingTask(domains, init, goal, actions)


def test_vanilla_values_single():
    scoping_task = make_vanilla_task()
    relevant_facts, relevant_actions = compute_goal_relevance(
        scoping_task,
        enable_merging=False,
        enable_causal_links=False,
        enable_fact_based=True,
    )

    assert relevant_facts == FactSet({"x": {0, 1}, "y": {0}, "z": {0}})
    assert sorted([a.name for a in relevant_actions]) == ["a1"]


def test_vanilla_variables_single():
    scoping_task = make_vanilla_task()
    relevant_facts, relevant_actions = compute_goal_relevance(
        scoping_task,
        enable_merging=False,
        enable_causal_links=False,
        enable_fact_based=False,
    )

    assert relevant_facts == FactSet({"x": {0, 1, 2}, "y": {0, 1}, "z": {0}})
    assert sorted([a.name for a in relevant_actions]) == ["a1", "a2", "b1"]


def test_vanilla_values_chain():
    scoping_task = make_vanilla_task(goal=[("z", 1)])
    relevant_facts, relevant_actions = compute_goal_relevance(
        scoping_task,
        enable_merging=False,
        enable_causal_links=False,
        enable_fact_based=True,
    )

    assert relevant_facts == FactSet({"x": {0, 1}, "y": {0, 1}, "z": {0, 1}})
    assert sorted([a.name for a in relevant_actions]) == ["a1", "a2", "a3"]


def test_vanilla_variables_chain():
    scoping_task = make_vanilla_task(goal=[("z", 1)])
    relevant_facts, relevant_actions = compute_goal_relevance(
        scoping_task,
        enable_merging=False,
        enable_causal_links=False,
        enable_fact_based=False,
    )

    assert relevant_facts == scoping_task.domains
    assert sorted([a.name for a in relevant_actions]) == ["a1", "a2", "a3", "b1", "b2"]


def test_merge_values():
    scoping_task = make_merge_task()
    merging_facts, merging_actions = compute_goal_relevance(
        scoping_task,
        enable_merging=True,
        enable_causal_links=False,
        enable_fact_based=True,
    )

    nonmerging_facts, nonmerging_actions = compute_goal_relevance(
        scoping_task,
        enable_merging=False,
        enable_causal_links=False,
        enable_fact_based=True,
    )

    assert merging_facts == FactSet({"x": {0}, "y": {0}, "z": {1, 0}})
    assert sorted([a.name for a in merging_actions]) == ["a3", "a4"]
    assert nonmerging_facts == FactSet({"x": {0, 1}, "y": {0, 1}, "z": {1, 0}})
    assert sorted([a.name for a in nonmerging_actions]) == ["a1", "a2", "a3", "a4"]


def make_merge_multi_task(
    domains=FactSet(
        {
            "x": {0, 1, 2},
            "y": {0, 1, 2},
            "z": {0, 1},
        }
    ),
    actions=[
        VarValAction("a1", [("x", 0), ("y", 0)], [("z", 1)], 1),
        VarValAction("a2", [("x", 2), ("y", 0)], [("z", 1)], 1),
        VarValAction("a3", [("x", 1)], [("z", 1)], 1),
    ],
    init=[
        ("x", 0),
        ("y", 0),
        ("z", 0),
    ],
    goal=[
        ("z", 1),
    ],
):
    return ScopingTask(domains, init, goal, actions)


def test_merge_multi():
    scoping_task = make_merge_multi_task()
    merging_facts, merging_actions = compute_goal_relevance(
        scoping_task,
        enable_merging=True,
        enable_causal_links=False,
        enable_fact_based=True,
    )

    nonmerging_facts, nonmerging_actions = compute_goal_relevance(
        scoping_task,
        enable_merging=False,
        enable_causal_links=False,
        enable_fact_based=True,
    )

    assert merging_facts == FactSet({"z": {1}})
    assert sorted([a.name for a in merging_actions]) == ["a3", "a4"]
    assert nonmerging_facts == FactSet({"x": {1}, "y": {0}, "z": {1}})
    assert sorted([a.name for a in nonmerging_actions]) == ["a1", "a2", "a3", "a4"]


def test_causal_links_variables():
    scoping_task = make_vanilla_task(
        init=[("x", 1), ("y", 0), ("z", 0)],
        goal=[("z", 1)],
    )
    relevant_facts, relevant_actions = compute_goal_relevance(
        scoping_task,
        enable_merging=False,
        enable_causal_links=True,
        enable_fact_based=False,
    )

    assert relevant_facts == FactSet({"x": {1}, "y": {0, 1}, "z": {0, 1, 2}})
    assert sorted([a.name for a in relevant_actions]) == ["a2", "a3", "b2"]


def test_causal_links_values():
    scoping_task = make_vanilla_task(
        init=[("x", 0), ("y", 1), ("z", 0)],
        goal=[("z", 1)],
    )
    relevant_facts, relevant_actions = compute_goal_relevance(
        scoping_task,
        enable_merging=False,
        enable_causal_links=True,
        enable_fact_based=True,
    )

    assert relevant_facts == FactSet({"x": {0}, "y": {1}, "z": {0, 1}})
    assert sorted([a.name for a in relevant_actions]) == ["a3"]


# %%
test_vanilla_values_single()
test_vanilla_variables_single()

test_vanilla_values_chain()
test_vanilla_variables_chain()

test_merge_values()
# test_merge_multi()

test_causal_links_variables()
test_causal_links_values()

print("All tests passed.")
