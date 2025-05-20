from browser import bind, window, document
from browser.local_storage import storage

import json
import io

from scoping.options import ScopingOptions
from scoping.task import ScopingTask
from scoping.sas_parser import SasParser
from scoping.visualization import TaskGraph
from scoping.core import scope


# DOM elements (accessed by `id` attribute in index.html)
UPLOAD_BTN = document["upload_file"]
DOWNLOAD_BTN = document["download_file"]
ENABLE_CAUSAL_LINKS = document["enable_causal_links"]
ENABLE_MERGING = document["enable_merging"]
ENABLE_FACT_BASED = document["enable_fact_based"]
ENABLE_FORWARD_PASS = document["enable_forward_pass"]
ENABLE_LOOP = document["enable_loop"]
VISUALIZE = document["visualize"]
VISUALIZE_BACK = document["visualize_back"]


# Global objects (remember to access these with the `global` keyword in functions)
sas_parser = SasParser(s_sas="")
sas_task = None
graph = None
scoping_options = ScopingOptions(
    enable_causal_links=False,
    enable_merging=False,
    enable_forward_pass=False,
    enable_loop=False
)
layer_count = 0 # actual/total number of layers in the graph
visible_layers = 1 # number of layers currently in the graph (nodes that are bunched up on the left/right without any links adjacent to them are not considered) -- lines up with the number of "visualize"-"visualize back" button clicks


def main():
    set_toggle_content(ENABLE_CAUSAL_LINKS, scoping_options.enable_causal_links)
    set_toggle_content(ENABLE_MERGING, scoping_options.enable_merging)
    set_toggle_content(ENABLE_FACT_BASED, scoping_options.enable_fact_based)
    set_toggle_content(ENABLE_FORWARD_PASS, scoping_options.enable_forward_pass)
    set_toggle_content(ENABLE_LOOP, scoping_options.enable_loop)


def visualize(step_back=False):
    global graph
    global layer_count
    global visible_layers

    if layer_count > 0 and visible_layers > layer_count:
        if not step_back:
            # prevents "next"-ing a graph when it is already fully built
            return

    if step_back:
        visible_layers -= 2

    if visible_layers <= 1:
        VISUALIZE_BACK.disabled = True # toggle the `disabled` attribute of this button in the DOM to `true`
    else:
        VISUALIZE_BACK.disabled = False

    if visible_layers >= layer_count:
        VISUALIZE.disabled = True
    else:
        VISUALIZE.disabled = False

    visible_layers += 1


@bind(UPLOAD_BTN, "input")
def file_read(ev):
    global layer_count

    def onload(event):
        DOWNLOAD_BTN.style.display = "inline"
        DOWNLOAD_BTN.attrs["download"] = file.name

        scoped_task, layers = read_sas(event.target.result) # creates scoped task and graph data
        write_json(layers)

        f = io.StringIO()
        scoped_task.to_sas().output(f)
        document['sas_content'].value = f.getvalue() # saves scoped task SAS to the DOM (for downloading purposes, can also be displayed in the DOM)

        VISUALIZE.disabled = False

    file = UPLOAD_BTN.files[0]
    reader = window.FileReader.new()
    reader.readAsText(file)
    reader.bind("load", onload)


def read_sas(sas_file):
    global sas_task
    global graph
    global layer_count

    # Read uploaded .sas file
    sas_parser.s_sas = sas_file
    sas_parser.parse()
    sas_task = sas_parser.to_fd()

    # Run scoping
    scoping_task = ScopingTask.from_sas(sas_task)

    # Build graph for visualization
    graph = TaskGraph(scoping_task, scoping_options)
    scoped_task = scope(scoping_task, scoping_options)
    graph.layers = [l for l in graph.layers if l]
    layer_count = len(graph.layers)

    return scoped_task, graph.layers


def update_sas():
    # This function is useful when the enable/disable buttons are clicked (e.g. enable forward pass)
    # Recreates the scoped task and graph data, saves the new scoped task SAS in the DOM, and resets the layer counter

    global visible_layers

    scoped_task, layers = read_sas(document['sas_content'].value)
    write_json(layers)

    f = io.StringIO()
    scoped_task.to_sas().output(f)
    document['sas_content'].value = f.getvalue()
    visible_layers = 1


@bind(DOWNLOAD_BTN, "mousedown")
def mousedown(ev):
    content = window.encodeURIComponent(document['sas_content'].value)
    DOWNLOAD_BTN.attrs["href"] = "data:text/plain," + content


@bind(ENABLE_CAUSAL_LINKS, "click")
def toggle_causal_links(ev):
    scoping_options.enable_causal_links = not scoping_options.enable_causal_links
    set_toggle_content(ENABLE_CAUSAL_LINKS, scoping_options.enable_causal_links)
    update_sas()
    VISUALIZE.disabled = False


@bind(ENABLE_MERGING, "click")
def toggle_merging(ev):
    scoping_options.enable_merging = not scoping_options.enable_merging
    set_toggle_content(ENABLE_MERGING, scoping_options.enable_merging)
    update_sas()
    VISUALIZE.disabled = False


@bind(ENABLE_FACT_BASED, "click")
def toggle_fact_based(ev):
    scoping_options.enable_fact_based = not scoping_options.enable_fact_based
    set_toggle_content(ENABLE_FACT_BASED, scoping_options.enable_fact_based)
    update_sas()
    VISUALIZE.disabled = False


@bind(ENABLE_FORWARD_PASS, "click")
def toggle_forward_pass(ev):
    scoping_options.enable_forward_pass = not scoping_options.enable_forward_pass
    set_toggle_content(ENABLE_FORWARD_PASS, scoping_options.enable_forward_pass)
    update_sas()
    VISUALIZE.disabled = False


@bind(ENABLE_LOOP, "click")
def toggle_loop(ev):
    scoping_options.enable_loop = not scoping_options.enable_loop
    set_toggle_content(ENABLE_LOOP, scoping_options.enable_loop)
    update_sas()
    VISUALIZE.disabled = False


@bind(VISUALIZE, "click")
def run_visualize(ev):
    visualize()
    if VISUALIZE.textContent == "Visualize":
        # so that this runs only once
        VISUALIZE.textContent = ">"
        VISUALIZE_BACK.textContent = "<"
        VISUALIZE_BACK.hidden = False


@bind(VISUALIZE_BACK, "click")
def run_visualize_backwards(ev):
    visualize(step_back=True)


def set_toggle_content(btn, flag):
    # Just frontend stuff. Controls what is rendered as the button text whenever that button is clicked.
    opt = " ".join(btn.textContent.split()[1:])
    btn.textContent = f"Disable {opt}" if flag else f"Enable {opt}"


def write_json(layers):
    data = {"nodes": [], "links": [], "is_forward": None} # graph data to be saved in localStorage and then read in `main.js`
    node_names = [] # auxiliary var for building `data`

    for i in range(len(layers)):
        layer = layers[i]
        for node in layer:
            if node.name not in node_names:
                node_names.append(node.name)
                precondition = list(map(lambda tup: " ".join(str(x) for x in tup), node.precondition))
                effect = list(map(lambda tup: " ".join(str(x) for x in tup), node.effect))
                data["nodes"].append(
                    {"id": node.name, "group": i, "precondition": precondition, "effect": effect}
                )
                for p in node.parents:
                    data["links"].append({"source": p.name, "target": node.name})

    for op in sas_task.operators:
        if op.name not in node_names:
            node_names.append(op.name)
            data["nodes"].append({"id": op.name, "group": len(layers)})

    data["is_forward"] = scoping_options.enable_forward_pass

    storage["scoping_data"] = json.dumps(data)
