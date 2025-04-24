import os
import re
from typing import Tuple, List, NewType, Optional


import translate.sas_tasks as fd


SasValueName = NewType("SasValueName", str)


class SasVar:
    def __init__(self, nm: str, axiom_layer: int, range: int, vals: tuple):
        self.nm = nm
        self.axiom_layer = axiom_layer
        self.range = range
        self.vals = vals
        # Freeze attributes (simulate frozen=True)
        object.__setattr__(self, '_frozen', True)
    
    def __setattr__(self, key, value):
        if hasattr(self, '_frozen') and self._frozen:
            raise AttributeError("Cannot modify frozen instance")
        object.__setattr__(self, key, value)
    
    # Implement ordering (order=True)
    def __lt__(self, other):
        if not isinstance(other, SasVar):
            return NotImplemented
        return (self.nm, self.axiom_layer, self.range, self.vals) < (other.nm, other.axiom_layer, other.range, other.vals)
    
    def __le__(self, other):
        if not isinstance(other, SasVar):
            return NotImplemented
        return (self.nm, self.axiom_layer, self.range, self.vals) <= (other.nm, other.axiom_layer, other.range, other.vals)
    
    def __gt__(self, other):
        if not isinstance(other, SasVar):
            return NotImplemented
        return (self.nm, self.axiom_layer, self.range, self.vals) > (other.nm, other.axiom_layer, other.range, other.vals)
    
    def __ge__(self, other):
        if not isinstance(other, SasVar):
            return NotImplemented
        return (self.nm, self.axiom_layer, self.range, self.vals) >= (other.nm, other.axiom_layer, other.range, other.vals)
    
    def __eq__(self, other):
        if not isinstance(other, SasVar):
            return NotImplemented
        return (self.nm, self.axiom_layer, self.range, self.vals) == (other.nm, other.axiom_layer, other.range, other.vals)
    
    def __hash__(self):
        return hash((self.nm, self.axiom_layer, self.range, self.vals))
    
    # Replace auto-generated __repr__ from dataclass
    def __repr__(self):
        return f"SasVar(nm={repr(self.nm)}, axiom_layer={repr(self.axiom_layer)}, range={repr(self.range)}, vals={repr(self.vals)})"
    
    @staticmethod
    def from_regex_tuple(m: tuple) -> 'SasVar':
        return SasVar(m[0], int(m[1]), int(m[2]), SasVar.split_values(m[3]))

    @staticmethod
    def split_values(s: str) -> tuple:
        return tuple([SasValueName(x) for x in s.split("\n")])

    def lookup(self, value):
        if value is None:
            return -1
        return self.vals.index(value)

    def get_var_val_pair(self, i: int):
        return SasVarValPair(self, i)


class SasVarValPair:
    def __init__(self, var: SasVar, val: int):
        self.var = var
        self.val = val
        # Freeze attributes (simulate frozen=True)
        object.__setattr__(self, '_frozen', True)
    
    def __setattr__(self, key, value):
        if hasattr(self, '_frozen') and self._frozen:
            raise AttributeError("Cannot modify frozen instance")
        object.__setattr__(self, key, value)
    
    # Implement ordering (order=True)
    def __lt__(self, other):
        if not isinstance(other, SasVarValPair):
            return NotImplemented
        return (self.var, self.val) < (other.var, other.val)
    
    def __le__(self, other):
        if not isinstance(other, SasVarValPair):
            return NotImplemented
        return (self.var, self.val) <= (other.var, other.val)
    
    def __gt__(self, other):
        if not isinstance(other, SasVarValPair):
            return NotImplemented
        return (self.var, self.val) > (other.var, other.val)
    
    def __ge__(self, other):
        if not isinstance(other, SasVarValPair):
            return NotImplemented
        return (self.var, self.val) >= (other.var, other.val)
    
    def __eq__(self, other):
        if not isinstance(other, SasVarValPair):
            return NotImplemented
        return (self.var, self.val) == (other.var, other.val)
    
    def __hash__(self):
        return hash((self.var, self.val))
    
    # Replace auto-generated __repr__ from dataclass
    def __repr__(self):
        return f"SasVarValPair(var={repr(self.var)}, val={repr(self.val)})"
    
    @property
    def val_nm(self) -> 'SasValueName':
        return self.var.vals[self.val]


class SasEffect:
    """
    Sas files distinguish between the condition on non-affected vars,
    and the condition on the affected var.
    Note that the var in condition_affected_var
    and the var in result must be the same
    It is maybe wasteful to keep it separate
    """

    def __init__(self, cond: tuple, var: int, affected_var, pre, post: int):
        self.cond = cond
        self.var = var
        self.affected_var = affected_var
        self.pre = pre
        self.post = post
        # Freeze attributes (simulate frozen=True)
        object.__setattr__(self, '_frozen', True)
    
    def __setattr__(self, key, value):
        if hasattr(self, '_frozen') and self._frozen:
            raise AttributeError("Cannot modify frozen instance")
        object.__setattr__(self, key, value)
    
    # Implement ordering (order=True)
    def __lt__(self, other):
        if not isinstance(other, SasEffect):
            return NotImplemented
        return (self.cond, self.var, self.affected_var, self.pre, self.post) < (other.cond, other.var, other.affected_var, other.pre, other.post)
    
    def __le__(self, other):
        if not isinstance(other, SasEffect):
            return NotImplemented
        return (self.cond, self.var, self.affected_var, self.pre, self.post) <= (other.cond, other.var, other.affected_var, other.pre, other.post)
    
    def __gt__(self, other):
        if not isinstance(other, SasEffect):
            return NotImplemented
        return (self.cond, self.var, self.affected_var, self.pre, self.post) > (other.cond, other.var, other.affected_var, other.pre, other.post)
    
    def __ge__(self, other):
        if not isinstance(other, SasEffect):
            return NotImplemented
        return (self.cond, self.var, self.affected_var, self.pre, self.post) >= (other.cond, other.var, other.affected_var, other.pre, other.post)
    
    def __eq__(self, other):
        if not isinstance(other, SasEffect):
            return NotImplemented
        return (self.cond, self.var, self.affected_var, self.pre, self.post) == (other.cond, other.var, other.affected_var, other.pre, other.post)
    
    def __hash__(self):
        return hash((self.cond, self.var, self.affected_var, self.pre, self.post))
    
    # Replace auto-generated __repr__ from dataclass
    def __repr__(self):
        return f"SasEffect(cond={repr(self.cond)}, var={repr(self.var)}, affected_var={repr(self.affected_var)}, pre={repr(self.pre)}, post={repr(self.post)})"
    
    @property
    def affected_var_condition_pair(self):
        if self.pre is None:
            return None
        else:
            return SasVarValPair(self.affected_var, self.pre)

    @property
    def result_var_val_pair(self):
        return SasVarValPair(self.affected_var, self.post)

    @property
    def full_condition(self):
        """
        Combination of non-affected var condition
        and affected var condition
        MF: Should we sort by var? Nah.
        """
        if self.pre is None:
            return self.cond
        else:
            return self.cond + (self.affected_var_condition_pair,)


class SasOperator:
    def __init__(self, nm: str, prevail: tuple, effects: tuple, cost: int = 1):
        self._nm = nm
        self._prevail = prevail
        self._effects = effects
        self._cost = cost

    @property
    def nm(self):
        return self._nm

    @property
    def prevail(self):
        return self._prevail

    @property
    def effects(self):
        return self._effects

    @property
    def cost(self):
        return self._cost

    def __eq__(self, other):
        if not isinstance(other, SasOperator):
            return NotImplemented
        return (self.nm, self.prevail, self.effects, self.cost) == (other.nm, other.prevail, other.effects, other.cost)

    def __lt__(self, other):
        if not isinstance(other, SasOperator):
            return NotImplemented
        return (self.nm, self.prevail, self.effects, self.cost) < (other.nm, other.prevail, other.effects, other.cost)

    def __hash__(self):
        return hash((self.nm, self.prevail, self.effects, self.cost))

    def __repr__(self):
        return f"SasOperator(nm={self.nm!r}, prevail={self.prevail!r}, effects={self.effects!r}, cost={self.cost!r})"


"""An axiom is basically an effect that is applied every timestep, if applicable"""


class SasAxiom(SasEffect):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __eq__(self, other):
        return super().__eq__(other)

    def __lt__(self, other):
        return super().__lt__(other)

    def __hash__(self):
        return super().__hash__()

    def __setattr__(self, key, value):
        raise AttributeError(f"{self.__class__.__name__} is immutable")


class SasMutex:
    def __init__(self, facts: tuple):
        self._facts = facts

    @property
    def facts(self):
        return self._facts

    def __eq__(self, other):
        if not isinstance(other, SasMutex):
            return NotImplemented
        return self.facts == other.facts

    def __lt__(self, other):
        if not isinstance(other, SasMutex):
            return NotImplemented
        return self.facts < other.facts

    def __hash__(self):
        return hash(self.facts)

    def __setattr__(self, name, value):
        if hasattr(self, name):
            raise AttributeError(f"{self.__class__.__name__} is immutable")
        super().__setattr__(name, value)

    def __repr__(self):
        return f"SasMutex(facts={self.facts!r})"


class SasPartialState:
    """It would be nice to enforce uniqueness of keys"""

    def __init__(self, var_value_pairs: tuple):
        self._var_value_pairs = var_value_pairs

    @property
    def var_value_pairs(self):
        return self._var_value_pairs

    def __getitem__(self, key):
        candidates = [x.val for x in self.var_value_pairs if x.var == key]
        return candidates[0]

    def __eq__(self, other):
        if not isinstance(other, SasPartialState):
            return NotImplemented
        return self.var_value_pairs == other.var_value_pairs

    def __lt__(self, other):
        if not isinstance(other, SasPartialState):
            return NotImplemented
        return self.var_value_pairs < other.var_value_pairs

    def __hash__(self):
        return hash(self.var_value_pairs)

    def __setattr__(self, name, value):
        if hasattr(self, name):
            raise AttributeError(f"{self.__class__.__name__} is immutable")
        super().__setattr__(name, value)

    def __repr__(self):
        return f"SasPartialState(var_value_pairs={self.var_value_pairs!r})"


class SasState(SasPartialState):
    """It would be nice to enforce full specification of vars"""

    pass


class SasParser:
    """
    Parse sas planning files into python datastructures.
    There are three sets of methods:

    1. Parsing functions. One for each section, and one to string them together.
    2. Helper functions
    3. File writing functions
    """

    # Regex patterns used in parsing
    pattern_var_val_pair = r"(?P<var_num>\d+) (?P<val_num>\d+)"

    # Type annotations for parsed values
    s_sas: str
    sas_vars: Tuple[SasVar, ...]
    sas_operators: Tuple[SasOperator, ...]
    sas_mutexes: Tuple[SasMutex, ...]
    sas_axioms: Tuple[SasAxiom, ...]
    initial_state: SasState
    goal: SasPartialState

    def __init__(self, s_sas: Optional[str] = None, pth: Optional[str] = None) -> None:
        """
        Specify either s_sas or pth.

        """
        if s_sas is not None:
            self.s_sas = s_sas
        elif pth is not None:
            with open(pth, "r") as f:
                self.s_sas = f.read()
        else:
            raise ValueError(
                "Please specify either s_sas or the pth of the sas file when creating a SasParser."
            )

    # Parsing functions
    def parse(self):
        """Do entire parsing"""
        self.parse_version()
        self.parse_metric()
        self.parse_vars()
        self.parse_mutex()
        self.parse_initial_state()
        self.parse_goal()
        self.parse_operators()
        self.parse_axioms()

    def parse_version(self) -> str:
        pattern_version = r"begin_version\n(\d+)\nend_version"
        versions = re.findall(pattern_version, self.s_sas)
        if len(versions) != 1:
            raise ValueError(
                f"File specifies {len(versions)} versions. It should specify 1."
            )
        self.version = versions[0]  # Just versions[0], since it's a string
        return self.version

    def parse_metric(self) -> int:
        """The metric should be 0 or 1"""
        pattern_metric = r"begin_metric\n(\d+)\nend_metric"
        metrics = re.findall(pattern_metric, self.s_sas)
        if len(metrics) != 1:
            raise ValueError(
                f"File specifies {len(metrics)} metrics. It should specify 1."
            )
        self.metric = int(metrics[0])  # Just [0] is fine
        return self.metric

    def parse_vars(self) -> Tuple[SasVar, ...]:
        sas_vars: List[SasVar] = []

        # Split based on variable block structure
        parts = self.s_sas.split("begin_variable\n")
        for part in parts[1:]:  # skip the part before the first variable
            if "end_variable" not in part:
                continue  # skip malformed entries

            block, _ = part.split("end_variable", 1)
            lines = block.strip().splitlines()

            if len(lines) < 3:
                continue  # invalid block

            nm = lines[0]
            axiom_layer = lines[1]
            var_range = lines[2]
            vals = "\n".join(lines[3:])  # any remaining lines are values

            sas_vars.append(SasVar.from_regex_tuple((nm, axiom_layer, var_range, vals)))

        sas_vars = tuple(sas_vars)
        self.sas_vars = sas_vars
        return sas_vars

    def parse_mutex(self) -> Tuple[SasMutex, ...]:
        """
        Must be run after parse_vars
        """
        mutex_pattern = r"begin_mutex_group\n(\d+)\n(.*?)\nend_mutex_group"
        mutexes_lst: List[SasMutex] = []

        for mutex_group_match in re.finditer(mutex_pattern, self.s_sas, re.DOTALL):
            facts_lst: List[SasVarValPair] = []
            facts_strs = mutex_group_match.group(2).splitlines()
            for fs in facts_strs:
                fact = self.get_sas_var_val_pair_from_str(fs)
                facts_lst.append(fact)
            mutex = SasMutex(tuple(facts_lst))
            mutexes_lst.append(mutex)

        mutexes = tuple(mutexes_lst)
        self.mutexes = mutexes
        return mutexes

    def parse_initial_state(self) -> SasState:
        pattern_initial_state = r"begin_state\n(.*?)\nend_state"
        match = re.search(pattern_initial_state, self.s_sas, re.DOTALL)
        if not match:
            raise ValueError("Could not find initial state block.")
        s_state = match.group(1)
        vals = s_state.splitlines()
        assert len(vals) == len(self.sas_vars)
        var_val_pairs = tuple(
            [self.sas_vars[i].get_var_val_pair(int(vals[i])) for i in range(len(vals))]
        )
        self.initial_state = SasState(var_val_pairs)
        return self.initial_state

    def parse_goal(self) -> SasPartialState:
        pattern_goal = r"begin_goal\n(\d+)\n(.*?)\nend_goal"
        match = re.search(pattern_goal, self.s_sas, re.DOTALL)
        if not match:
            raise ValueError("Could not find goal section in SAS file.")
        s_goal = match.group(2)
        var_val_strs = s_goal.splitlines()
        var_val_pairs = tuple(
            [self.get_sas_var_val_pair_from_str(s) for s in var_val_strs]
        )
        self.goal = SasPartialState(var_val_pairs)
        return self.goal

    def parse_axioms(self) -> Tuple[SasAxiom, ...]:
        pattern_axiom = (
            r"begin_rule\n(\d+)\n(.*?)"      # num conditions and condition lines
            r"(\d+) (\d+) (\d+)\nend_rule"   # var_num, val_old, val_new
        )
        axioms_lst: List[SasAxiom] = []

        for m_axiom in re.finditer(pattern_axiom, self.s_sas, re.DOTALL):
            conds_strs = m_axiom.group(2).splitlines()
            conds = [self.get_sas_var_val_pair_from_str(c) for c in conds_strs]

            i_affected_var = int(m_axiom.group(3))
            i_val_old = int(m_axiom.group(4))
            i_val_new = int(m_axiom.group(5))

            affected_var = self.sas_vars[i_affected_var]

            val_cond = None if i_val_old == -1 else affected_var.vals[i_val_old]

            axioms_lst.append(
                SasAxiom(
                    cond=tuple(conds),
                    var=i_affected_var,
                    affected_var=affected_var,
                    pre=val_cond,
                    post=i_val_new,
                )
            )

        self.axioms = tuple(axioms_lst)
        return self.axioms

    def parse_operators(self) -> Tuple[SasOperator, ...]:
        # Get number of operators from after `end_goal`
        pattern_operator_count = r"end_goal\n(\d+)\n"
        match_count = re.search(pattern_operator_count, self.s_sas)
        if not match_count:
            raise ValueError("Could not determine number of operators.")
        n_operators = int(match_count.group(1))

        operators: List[SasOperator] = []

        # Split the SAS string by operator blocks
        parts = self.s_sas.split("begin_operator\n")
        for part in parts[1:]:  # Skip the first part before any operator
            if "end_operator" not in part:
                continue

            block, _ = part.split("end_operator", 1)
            lines = block.strip().splitlines()
            if len(lines) < 4:
                continue  # malformed block

            idx = 0
            name = lines[idx].strip()
            idx += 1

            n_prevail = int(lines[idx])
            idx += 1

            prevail_lines = lines[idx:idx + n_prevail]
            prevail = tuple(self.get_sas_var_val_pair_from_str(x) for x in prevail_lines)
            idx += n_prevail

            n_effects = int(lines[idx])
            idx += 1

            effect_lines = lines[idx:idx + n_effects]
            effects = tuple(self.parse_effect(x) for x in effect_lines)
            idx += n_effects

            cost = lines[idx].strip()

            operators.append(
                SasOperator(
                    nm=f"({name})",
                    prevail=prevail,
                    effects=effects,
                    cost=cost,
                )
            )

        if len(operators) != n_operators:
            raise ValueError(
                f"The sas file claims to have {n_operators} operators, but we found {len(operators)}"
            )

        self.operators = tuple(operators)
        return self.operators

    def parse_effect(self, s: str) -> SasEffect:
        s_split = s.split(" ")
        n_cond = int(s_split[0])

        conds: List[SasVarValPair] = []
        i_conds_start = 1
        for i_pair in range(n_cond):
            num_var = int(s_split[i_conds_start + i_pair * 2])
            num_val = int(s_split[i_conds_start + (i_pair * 2) + 1])
            conds.append(self.get_sas_var_val_pair_from_ints(num_var, num_val))

        i_conds_end = i_conds_start + n_cond * 2
        num_var_affected = int(s_split[i_conds_end])
        var_affected = self.sas_vars[num_var_affected]
        num_val_cond = int(s_split[i_conds_end + 1])
        
        # Handle the -1 condition check for affected var
        val_cond = None if num_val_cond == -1 else var_affected.vals[num_val_cond]

        num_val_result = int(s_split[i_conds_end + 2])
        if i_conds_end + 2 != len(s_split) - 1:
            raise ValueError("We miscounted the total number of elements in the effect")

        return SasEffect(
            cond=tuple(conds),
            var=num_var_affected,
            affected_var=var_affected,
            pre=val_cond,
            post=num_val_result,
        )

    # Helper functions
    ## Getting SasVarValPairs
    def get_sas_var_val_pair_from_ints(
        self, var_num: int, val_num: int
    ) -> SasVarValPair:
        var0 = self.sas_vars[var_num]
        # val0 = var0.vals[val_num]
        return SasVarValPair(var0, val_num)

    @staticmethod
    def get_var_val_nums_from_str(s: str) -> Tuple[int, int]:
        m = re.match(SasParser.pattern_var_val_pair, s)
        if m is None:
            raise ValueError(f"The string is not a pair of ints:\n{s}")
        var_num = int(m.group("var_num"))
        val_num = int(m.group("val_num"))
        return var_num, val_num

    def get_sas_var_val_pair_from_str(self, s: str) -> SasVarValPair:
        var_num, val_num = SasParser.get_var_val_nums_from_str(s)
        # return self.get_sas_var_val_pair_from_ints(var_num, val_num)
        return (var_num, val_num)

    def var_val_pair2ints(self, p: SasVarValPair) -> Tuple[int, int]:
        """Returns the pair of ints a sas file would use to represent p"""
        i_var = self.sas_vars.index(p.var)
        # i_val = p.var.vals.index(p.val)
        return (i_var, p.val)

    def var_val_pair2sas_str(self, p: SasVarValPair) -> str:
        return " ".join(map(str, self.var_val_pair2ints(p)))

    # Writing back to SAS
    def generate_sas(self) -> str:
        pieces: List[str] = [
            self.generate_version_and_metric_sections(),
            self.generate_variables_section(),
            self.generate_mutexes_section(),
            self.generate_initial_state_section(),
            self.generate_goal_section(),
            self.generate_operators_section(),
            self.generate_axioms_section(),
        ]
        return "\n".join(pieces) + "\n"

    def generate_version_and_metric_sections(self) -> str:
        return f"begin_version\n{self.version}\nend_version\nbegin_metric\n{self.metric}\nend_metric"

    ## Variables
    def generate_variables_section(self) -> str:
        pieces: List[str] = [str(len(self.sas_vars))]
        for v in self.sas_vars:
            pieces.append(self.generate_variable_str(v))
        return "\n".join(pieces)

    def generate_variable_str(self, v: SasVar) -> str:
        pieces: List[str] = ["begin_variable", v.nm, str(v.axiom_layer), str(v.range)]
        for val in v.vals:
            pieces.append(val)
        pieces.append("end_variable")
        return "\n".join(pieces)

    ## Mutexes
    def generate_mutexes_section(self) -> str:
        pieces: List[str] = [str(len(self.mutexes))]
        pieces.extend([self.generate_mutex_str(m) for m in self.mutexes])
        return "\n".join(pieces)

    def generate_mutex_str(self, m: SasMutex) -> str:
        pieces: List[str] = ["begin_mutex_group"]
        pieces.append(str(len(m.facts)))
        # raise NotImplementedError
        for f in m.facts:
            i_var = self.sas_vars.index(f.var)
            # i_val = f.var.vals.index(f.val)
            pieces.append(f"{i_var} {f.val}")
        pieces.append("end_mutex_group")
        return "\n".join(pieces)

    ## Initial State
    def generate_initial_state_section(self) -> str:
        pieces: List[str] = ["begin_state"]
        # pieces.extend([self.var_val_pair2sas_str(p) for p in self.initial_state.var_value_pairs])
        pieces.extend([str(p.val) for p in self.initial_state.var_value_pairs])
        pieces.append("end_state")
        return "\n".join(pieces)

    ## Goals
    def generate_goal_section(self) -> str:
        pieces: List[str] = ["begin_goal", str(len(self.goal.var_value_pairs))]
        pieces.extend([self.var_val_pair2sas_str(p) for p in self.goal.var_value_pairs])
        pieces.append("end_goal")
        return "\n".join(pieces)

    def generate_operators_section(self) -> str:
        pieces: List[str] = [str(len(self.operators))]
        pieces.extend([self.generate_operator_str(o) for o in self.operators])
        return "\n".join(pieces)

    ## Operators
    def generate_operator_str(self, o: SasOperator) -> str:
        pieces: List[str] = ["begin_operator", o.nm, str(len(o.prevail))]
        # Add prevail conditions
        pieces.extend([self.var_val_pair2sas_str(p) for p in o.prevail])

        # Add effects
        pieces.append(str(len(o.effects)))
        pieces.extend([self.effect2sas_str(e) for e in o.effects])

        # Add cost
        pieces.append(str(o.cost))
        pieces.append("end_operator")
        return "\n".join(pieces)

    def effect2sas_str(self, e: SasEffect) -> str:
        pieces: List[str] = [str(len(e.cond))]
        # Effect conditions
        pieces.extend([self.var_val_pair2sas_str(p) for p in e.cond])
        # Affected var
        pieces.append(str(self.sas_vars.index(e.affected_var)))
        # Affected var condition
        if e.pre is None:
            pieces.append("-1")
        else:
            pieces.append(str(e.affected_var.vals.index(e.pre)))
        # Result value
        pieces.append(str(e.post))
        return " ".join(pieces)

    ## Axioms
    def generate_axioms_section(self) -> str:
        pieces: List[str] = [str(len(self.axioms))]
        pieces.extend([self.axiom2sas_str(a) for a in self.axioms])
        return "\n".join(pieces)

    def axiom2sas_str(self, a: SasAxiom) -> str:
        pieces: List[str] = ["begin_rule", str(len(a.cond))]
        # Conditions
        pieces.extend([self.var_val_pair2sas_str(p) for p in a.cond])
        # Affected var
        i_var = self.sas_vars.index(a.affected_var)
        # i_val_old = a.affected_var.vals.index(a.affected_var_condition)
        # i_val_new = a.affected_var.vals.index(a.result_val)
        pieces.append(f"{i_var} {a.pre} {a.post}")
        pieces.append("end_rule")
        return "\n".join(pieces)

    # Check parse
    def check_parse(self) -> bool:
        return self.generate_sas() == self.s_sas

    # Converting to scopeable representation
    def to_fd(self) -> fd.SASTask:
        # Variables
        ranges = [v.range for v in self.sas_vars]
        axiom_layers = [v.axiom_layer for v in self.sas_vars]
        value_names = [list(v.vals) for v in self.sas_vars]
        variables = fd.SASVariables(ranges, axiom_layers, value_names)

        # Mutexes
        mutexes = [fd.SASMutexGroup(m.facts) for m in self.mutexes]

        # Init
        init = fd.SASInit([p.val for p in self.initial_state.var_value_pairs])

        # Goal
        goal = fd.SASGoal(self.goal.var_value_pairs)

        # Operators
        operators = []
        for op in self.operators:
            pre_post = []
            for e in op.effects:
                pre_as_int = self.sas_vars[e.var].lookup(e.pre)
                pre_post.append((e.var, pre_as_int, e.post, e.cond))
            operators.append(fd.SASOperator(op.nm, op.prevail, pre_post, op.cost))

        # Axioms
        axioms = []
        for ax in self.axioms:
            axioms.append(fd.SASAxiom(ax.cond, (ax.var, ax.post)))

        # Metric
        metric = self.metric

        sas_task = fd.SASTask(variables, mutexes, init, goal, operators, axioms, metric)
        return sas_task


def test():
    repo_root = "../../.."
    # pth = "../../../gripper-painting.sas"
    pth_sas_dir = f"{repo_root}/generated_sas"
    os.makedirs(pth_sas_dir, exist_ok=True)
    pth_sas_in = f"{pth_sas_dir}/gripper-painting.sas"
    cmd_s = f"python {repo_root}/scoping/downward_translate/translate_and_scope.py {repo_root}/examples/gripper-painting-domain/domain.pddl {repo_root}/examples/gripper-painting-domain/prob04.pddl --sas-file {pth_sas_in} --scope True"
    os.system(cmd_s)

    parser = SasParser(pth=pth_sas_in)
    parser.parse()

    def add_pre_extension(s: str, s_suffix: str) -> str:
        s_split = s.split(".")
        s_split = s_split[:-1] + [s_suffix] + s_split[-1:]
        return ".".join(s_split)

    s_sas_out = parser.generate_sas()
    with open(add_pre_extension(pth_sas_in, "regen"), "w") as f:
        f.write(s_sas_out)

    print(s_sas_out == parser.s_sas)
