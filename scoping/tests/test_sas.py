#!%cd ~/dev/downward/src/translate
#
import io

import sas_tasks as fd
from scoping.sas_parser import SasParser
from scoping.task import ScopingTask


def test_sas_parsing():
    sas_path = "../../benchmarks/basic/gripper/prob01.sas"
    with open(sas_path, "r") as f:
        sas_input = f.read()
    sas_input = sas_input.strip()

    parser = SasParser(pth=sas_path)
    parser.parse()
    sas_task: fd.SASTask = parser.to_fd()
    f = io.StringIO()
    sas_task.output(f)
    sas_output = f.getvalue()

    for input_line, output_line in zip(sas_input.splitlines(), sas_output.splitlines()):
        assert input_line.strip() == output_line.strip()

    print(sas_input)
    print()
    print(sas_output)


def test_sas_conversion():
    sas_path = "../../benchmarks/basic/gripper/prob01.sas"
    parser = SasParser(pth=sas_path)
    parser.parse()
    sas_task: fd.SASTask = parser.to_fd()
    scoping_task: ScopingTask = ScopingTask.from_sas(sas_task)
    converted_sas = scoping_task.to_sas()
    assert sas_task == converted_sas


# %%
test_sas_conversion()

print("All tests passed.")
