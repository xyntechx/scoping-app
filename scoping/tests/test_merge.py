#!%cd ~/dev/downward/src/translate

from scoping.actions import VarValAction
from scoping.factset import FactSet
from scoping.merging import merge, merge_old


# a1 = VarValAction(
#     "a1",
#     [("x", 0), ("v1", 0)],
#     [("x", 2)],
#     1,
# )

# b1 = VarValAction(
#     "b1",
#     [("x", 0), ("v1", 1)],
#     [("x", 2)],
#     1,
# )

# a2 = VarValAction(
#     "a2",
#     [("x", 0), ("v2", 0)],
#     [("x", 2)],
#     1,
# )

# b2 = VarValAction(
#     "b2",
#     [("x", 0), ("v2", 1)],
#     [("x", 2)],
#     1,
# )


n_action_pairs = 17
actions = [
    VarValAction(f"a{i:02d}", [("x", 0), (f"v{i}", 0)], [("x", 1)], 1)
    for i in range(n_action_pairs)
] + [
    VarValAction(f"b{i:02d}", [("x", 0), (f"v{i}", 1)], [("x", 1)], 1)
    for i in range(n_action_pairs)
]

variable_domains = FactSet()
for action in actions:
    variable_domains.add(action.precondition)
    variable_domains.add(action.effect)

relevant_variables = variable_domains.variables

# relevant_precondition_facts = merge(
#     actions=actions,
#     relevant_variables=relevant_variables,
#     variable_domains=variable_domains,
# )

relevant_precondition_facts_old = merge_old(
    actions=actions,
    relevant_variables=relevant_variables,
    variable_domains=variable_domains,
)

# assert relevant_precondition_facts == relevant_precondition_facts_old
