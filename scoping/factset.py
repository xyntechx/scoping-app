from __future__ import annotations
from collections import defaultdict
from typing import Any, Iterable, Optional, overload, Tuple, Union

VarValPair = Tuple[int, int]


class FactSet:
    facts: dict[Any, set[Any]]

    def __init__(
        self,
        facts: Union[FactSet, dict[Any, set[Any]], Iterable[VarValPair], None] = None,
    ) -> None:
        self.facts = defaultdict(set)
        if facts is None:
            return
        if isinstance(facts, (FactSet, dict)):
            self.union(facts)
        else:
            self.add(facts)

    def __repr__(self) -> str:
        return f"FactSet({repr(dict(self.facts))})"

    def __getitem__(self, key: Any) -> set[Any]:
        return self.facts[key]

    def __eq__(self, other: Optional[FactSet]) -> bool:
        if other is None:
            return False
        return self.facts == other.facts

    def __len__(self) -> int:
        return len(self.facts)

    def __iter__(self):
        return iter(self.facts.items())

    @property
    def variables(self) -> list[Any]:
        return list(self.facts.keys())

    @property
    def n_facts(self) -> int:
        return sum([len(values) for _, values in self])

    @overload
    def add(self, var: Any, val: Any) -> None: ...
    @overload
    def add(self, facts_iterable: Iterable[VarValPair]) -> None: ...
    def add(
        self,
        facts_iterable_or_var: Union[Any, Iterable[VarValPair]],
        val: Optional[Any] = None,
    ) -> None:
        """Add a new fact (var = val), or an iterable of such facts, to the FactSet"""
        if val is None:
            facts_iterable = facts_iterable_or_var
            for var, val in facts_iterable:
                self.add(var, val)
        else:
            var = facts_iterable_or_var
            self.facts[var].add(val)

    @overload
    def union(self, other_facts: FactSet | dict) -> None: ...
    @overload
    def union(self, var: Any, values: set[Any]) -> None: ...
    def union(
        self,
        other_facts_or_var: Union[FactSet, Any],
        values: Optional[set[Any]] = None,
    ) -> None:
        """Take the in-place union of the FactSet with the specified additional facts"""
        if values is None:
            other_facts = other_facts_or_var
            if isinstance(other_facts, FactSet):
                other_facts = other_facts.facts
            for var, values in other_facts.items():
                self.union(var, values)
        else:
            var = other_facts_or_var
            self.facts[var] = self.facts[var].union(values)

    def __contains__(self, item: VarValPair | FactSet) -> bool:
        """Check if a (var, val) pair is an element of the FactSet, or if another
        FactSet is a subset of this one"""
        if isinstance(item, FactSet):
            other_facts = item
            for var, values in other_facts:
                if any([(var, val) not in self for val in values]):
                    return False
            return True
        else:
            var, val = item
            if var not in self.facts:
                return False
            values = self.facts[var]
            return val in values
