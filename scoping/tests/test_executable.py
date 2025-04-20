#!%cd ~/dev/downward/src/translate
#
from scoping.core import scope_sas
from scoping.options import ScopingOptions


scoping_options = ScopingOptions(0, 0, 0, 0, 0, write_output_file=False)


def test_gripper():
    sas_path = "../../benchmarks/basic/gripper/prob01.sas"
    scope_sas(sas_path, scoping_options)


def test_airport():
    sas_path = "../../benchmarks/basic/airport/p01-airport1-p1.sas"
    scope_sas(sas_path, scoping_options)


def test_agricola():
    sas_path = "../../benchmarks/basic/agricola-opt18-strips/p01.sas"
    scope_sas(sas_path, scoping_options)


def test_dummy_unsolvable():
    sas_path = "../../benchmarks/basic/mystery/prob07.sas"
    scope_sas(sas_path, scoping_options)


def test_pruning_value_names():
    sas_path = "../../benchmarks/basic/parcprinter-08-strips/p01.sas"
    scope_sas(sas_path, scoping_options=ScopingOptions(0, 0, 1, 0, 0, False))


def test_large_itertools_product():
    sas_path = "../../benchmarks/basic/tidybot-opt11-strips/p02.sas"
    scope_sas(sas_path, scoping_options=ScopingOptions(1, 1, 1, 1, 1, False))


def test_movie():
    sas_path = "../../benchmarks/basic/movie/prob01.sas"
    scope_sas(sas_path, scoping_options=ScopingOptions(1, 1, 1, 1, 1, False))


def test_floortile():
    sas_path = "../../benchmarks/basic/floortile-opt11-strips/opt-p01-001.sas"
    scope_sas(sas_path, scoping_options=ScopingOptions(1, 1, 1, 1, 0, True))


# %%
test_gripper()
test_airport()
test_agricola()
test_dummy_unsolvable()
test_pruning_value_names()
# test_large_itertools_product()
test_movie()
test_floortile()

print("All tests passed.")
