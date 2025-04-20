from typing import Any, List, Tuple

from translate.sas_tasks import SASOperator
from scoping.factset import FactSet, VarValPair


class VarValAction:
    def __init__(
        self,
        name: str,
        precondition: List[VarValPair],
        effect: List[VarValPair],
        cost: int,
    ):
        self.name = name
        self.precondition = precondition
        self.effect = effect
        self.cost = cost

    @classmethod
    def from_sas(cls, sas_operator: SASOperator):
        assert not any(
            [cond for (_, _, _, cond) in sas_operator.pre_post]
        ), "Conditional effects not implemented"
        pre_list = [
            (var, pre) for (var, pre, _, _) in sas_operator.pre_post if pre != -1
        ]
        pre_list += sas_operator.prevail
        eff_list = [(var, post) for (var, pre, post, conds) in sas_operator.pre_post]
        # Remove any duplicates while preserving order
        pre_list = list(dict.fromkeys(pre_list))
        return cls(sas_operator.name, pre_list, eff_list, sas_operator.cost)

    @property
    def prevail(self) -> list[VarValPair]:
        effect_facts = FactSet(self.effect)

        def is_prevail(var_val: VarValPair):
            if var_val not in self.precondition:
                return False
            var, val = var_val
            if var not in effect_facts.variables:
                return True
            if set([val]) != effect_facts[var]:
                return False
            return True

        return [fact for fact in self.precondition if is_prevail(fact)]

    @property
    def pre_post(self) -> List[Tuple[int, int, int, List[VarValPair]]]:
        prevails = self.prevail
        precond_facts = FactSet(
            [fact for fact in self.precondition if fact not in prevails]
        )

        def get_precond(var):
            if precond_facts[var]:
                return precond_facts[var].pop()
            return -1

        return [
            (var, get_precond(var), val, [])
            for var, val in self.effect
            if (var, val) not in prevails
        ]

    def __eq__(self, other: "VarValAction") -> bool:
        if self.name != other.name:
            return False
        if self.precondition != other.precondition:
            return False
        if self.effect != other.effect:
            return False
        if self.cost != other.cost:
            return False
        return True

    def __repr__(self):
        return f"VarValAction({self.name}, pre={self.precondition}, eff={self.effect})"

    def __hash__(self) -> int:
        return hash(
            (self.name, tuple(self.precondition), tuple(self.effect), self.cost)
        )

    def effect_hash(
        self, relevant_variables: List[Any]
    ) -> Tuple[List[VarValPair], int]:
        return tuple(
            [(var, val) for (var, val) in self.effect if var in relevant_variables]
        ), self.cost

    def can_run(self, state: List[VarValPair]) -> bool:
        state_facts = set(state)
        for fact in self.precondition:
            if fact not in state_facts:
                return False
        return True

    def dump(self):
        print(self.name)
        for fact in self.precondition:
            print(f"PRE: {fact}")
        for fact in self.effect:
            print(f"EFF: {fact}")
        print("cost:", self.cost)
