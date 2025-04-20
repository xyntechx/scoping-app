from dataclasses import dataclass, field

import translate.sas_tasks as fd
from scoping.actions import VarValAction
from scoping.factset import FactSet, VarValPair


@dataclass
class ScopingTask:
    domains: FactSet
    init: list[VarValPair]
    goal: list[VarValPair]
    actions: list[VarValAction]
    mutexes: list[list[VarValPair]] = field(default_factory=list)
    axioms: list[VarValAction] = field(default_factory=list)
    metric: bool = False
    value_names: dict[int, list[str]] = field(default_factory=dict)

    def from_sas(sas_task: fd.SASTask) -> "ScopingTask":
        domains = FactSet(
            {i: set(range(r)) for i, r in enumerate(sas_task.variables.ranges)}
        )
        value_names = {i: vals for i, vals in enumerate(sas_task.variables.value_names)}
        init = list(enumerate(sas_task.init.values))
        goal = sas_task.goal.pairs
        actions = [VarValAction.from_sas(op) for op in sas_task.operators]
        mutexes = [mutex.facts for mutex in sas_task.mutexes]
        axioms = [
            VarValAction(name="", precondition=ax.condition, effect=[ax.effect], cost=0)
            for ax in sas_task.axioms
        ]
        metric = sas_task.metric
        return ScopingTask(
            domains=domains,
            init=init,
            goal=goal,
            actions=actions,
            mutexes=mutexes,
            axioms=axioms,
            metric=metric,
            value_names=value_names,
        )

    def to_sas(self) -> fd.SASTask:
        sorted_vars = sorted(self.domains.variables)
        var_index = {var: i for i, var in enumerate(sorted_vars)}
        sorted_vals = {var: sorted(vals) for var, vals in self.domains}
        val_index = {
            var: {val: i for i, val in enumerate(vals)}
            for var, vals in sorted_vals.items()
        }
        [vals.update({-1: -1}) for _, vals in val_index.items()]
        variables = fd.SASVariables(
            ranges=[len(self.domains[var]) for var in sorted_vars],
            axiom_layers=[-1 for _ in sorted_vars],
            value_names=[
                [self.value_names[var][val] for val in sorted_vals[var]]
                for var in sorted_vars
            ],
        )
        mutexes = (
            []
            if self.mutexes is None
            else [
                fd.SASMutexGroup(
                    facts=[(var_index[var], val_index[var][val]) for var, val in mutex]
                )
                for mutex in self.mutexes
                if mutex and len(mutex) > 1
            ]
        )
        init = fd.SASInit(
            values=[val_index[var][val] for var, val in sorted(self.init)]
        )
        goal = fd.SASGoal(
            [(var_index[var], val_index[var][val]) for var, val in self.goal]
        )
        operators = [
            fd.SASOperator(
                name=a.name,
                prevail=[
                    (var_index[var], val_index[var][val]) for var, val in a.prevail
                ],
                pre_post=[
                    (var_index[var], val_index[var][pre], val_index[var][post], cond)
                    for var, pre, post, cond in a.pre_post
                ],
                cost=a.cost,
            )
            for a in self.actions
        ]
        axioms = (
            []
            if self.axioms is None
            else [
                fd.SASAxiom(
                    condition=[
                        (var_index[var], val_index[var][val])
                        for var, val in ax.precondition
                    ],
                    effect=(
                        var_index[ax.effect[0][0]],
                        val_index[ax.effect[0][0]][ax.effect[0][1]],
                    ),
                )
                for ax in self.axioms
                if ax.effect
            ]
        )
        metric = self.metric
        sas_task = fd.SASTask(
            variables=variables,
            mutexes=mutexes,
            init=init,
            goal=goal,
            operators=operators,
            axioms=axioms,
            metric=metric,
        )
        return sas_task

    def __eq__(self, other: "ScopingTask") -> bool:
        if self.domains != other.domains:
            return False
        if sorted(self.init) != sorted(other.init):
            return False
        if sorted(self.goal) != sorted(other.goal):
            return False
        if len(self.actions) != len(other.actions):
            return False
        if len(self.mutexes) != len(other.mutexes):
            return False
        if self.metric != other.metric:
            return False
        for a, b in zip(self.actions, other.actions):
            if a != b:
                return False
        for a, b in zip(self.mutexes, other.mutexes):
            if sorted(a) != sorted(b):
                return False
        for a, b in zip(self.value_names.keys(), other.value_names.keys()):
            if a != b:
                return False
            if self.value_names[a] != other.value_names[a]:
                return False
        return True

    def dump(self):
        print(f"domains={self.domains},")
        print(f"init={self.init},")
        print(f"goal={self.goal},")
        print("actions=[")
        for a in self.actions:
            print(
                f"    VarValAction('{a.name}', {a.precondition}, {a.effect}, {a.cost}),"
            )
        print("]")
