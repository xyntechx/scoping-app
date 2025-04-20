#!%cd ~/dev/downward/src/translate
# %%
import math
import random
from tqdm import tqdm

from scoping.actions import VarValAction
from scoping.core import scope, scope_forward
from scoping.factset import FactSet
from scoping.options import ScopingOptions
from scoping.task import ScopingTask


def generate_task(max_n_vars=3, max_n_vals=3, max_n_actions=6):
    goal_reachable = False
    while not goal_reachable:
        n_variables = random.randint(2, max_n_vars)
        var_names = list("zyxwvuts"[:n_variables])
        ranges = [random.randint(2, max_n_vals) for _ in var_names]
        domains = FactSet({var: set(range(r)) for var, r in zip(var_names, ranges)})
        n_actions = random.randint(2, max_n_actions)
        ac_names = "abcdefghijklmnopqr"[:n_actions]
        n_precond_vars = [random.randint(0, n_variables) for _ in range(n_actions)]
        n_effect_vars = [random.randint(1, n_variables) for _ in range(n_actions)]
        actions = []
        for name, n_pre, n_eff in zip(ac_names, n_precond_vars, n_effect_vars):
            pre_vars = random.sample(var_names, n_pre)
            eff_vars = random.sample(var_names, n_eff)
            precond = [
                (var, random.sample(list(domains[var]), 1)[0]) for var in pre_vars
            ]
            effect = [
                (var, random.sample(list(domains[var]), 1)[0]) for var in eff_vars
            ]
            precond = [fact for fact in precond if fact not in effect]
            actions.append(VarValAction(name, precond, effect, 1))

        init = [(var, 0) for var in var_names]
        goal = init
        while goal == init:
            n_goal_vars = random.randint(1, n_variables)
            goal_vars = random.sample(var_names, n_goal_vars)
            goal = [(var, random.sample(list(domains[var]), 1)[0]) for var in goal_vars]
        task = ScopingTask(domains, init, goal, actions)
        task, goal_reachable = scope_forward(task)
    return task


def tasks_are_equal(task_a, task_b):
    if task_a.domains != task_b.domains:
        return False
    a_actions = sorted(a.name for a in task_a.actions)
    b_actions = sorted(b.name for b in task_b.actions)
    if any([a != b for a, b in zip(a_actions, b_actions)]):
        return False
    return True


# %%
def find_example():
    found = False

    MAX_N_VALS = [3, 4, 5]
    MAX_N_ACTIONS = [5, 6, 7, 8, 9, 10, 11, 12, 13]
    MAX_N_VARS = [3, 4, 5, 6, 7]
    MAX_ATTEMPTS = range(500000)
    N_TOTAL_ATTEMPTS = math.prod(
        map(len, [MAX_N_ACTIONS, MAX_N_VARS, MAX_N_VALS, MAX_ATTEMPTS])
    )

    with tqdm(total=N_TOTAL_ATTEMPTS) as pbar:
        for max_n_vals in MAX_N_VALS:
            if found:
                break
            for max_n_actions in MAX_N_ACTIONS:
                if found:
                    break
                for max_n_vars in MAX_N_VARS:
                    if found:
                        break
                    for _ in MAX_ATTEMPTS:
                        if found:
                            break

                        scoping_task = generate_task(
                            max_n_vars, max_n_vals, max_n_actions
                        )
                        pbar.update(1)
                        reachable_task, is_reachable = scope_forward(scoping_task)
                        assert is_reachable
                        assert tasks_are_equal(scoping_task, reachable_task)

                        # want double to improve on forward
                        task_forward = scope(
                            scoping_task, ScopingOptions(1, 1, 1, 1, 0)
                        )
                        task_double = scope(task_forward, ScopingOptions(1, 1, 1, 1, 0))
                        if tasks_are_equal(task_double, task_forward):
                            continue

                        # want forward to improve on backward
                        task_backward = scope(
                            scoping_task, ScopingOptions(1, 1, 1, 0, 0)
                        )
                        if tasks_are_equal(task_forward, task_backward):
                            continue

                        # want backward to improve on merge
                        task_merge = scope(scoping_task, ScopingOptions(0, 1, 1, 0, 0))
                        if tasks_are_equal(task_backward, task_merge):
                            continue

                        # want merge to improve on values
                        task_values = scope(scoping_task, ScopingOptions(0, 0, 1, 0, 0))
                        if tasks_are_equal(task_merge, task_values):
                            continue

                        # want CL to improve on values, and in a different way from merge
                        task_cl = scope(scoping_task, ScopingOptions(1, 0, 1, 0, 0))
                        if tasks_are_equal(task_cl, task_values):
                            continue
                        if tasks_are_equal(task_cl, task_merge):
                            continue

                        # want values to improve on vars
                        task_vars = scope(scoping_task, ScopingOptions(0, 0, 0, 0, 0))
                        if tasks_are_equal(task_values, task_vars):
                            continue

                        found = True

    if found:
        print("Found example!")
        print()
        print("scoping_task:")
        scoping_task.dump()
        print("task_vars:")
        task_vars.dump()
        print("task_values:")
        task_values.dump()
        print("task_merge:")
        task_merge.dump()
        print("task_cl:")
        task_cl.dump()
        print("task_backward:")
        task_backward.dump()
        print("task_forward:")
        task_forward.dump()
        print("task_double:")
        task_double.dump()


# %%

find_example()

print("All tests passed.")
