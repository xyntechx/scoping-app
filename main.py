from browser import bind, window, document, html
from browser.local_storage import storage

import json
import io

from scoping.options import ScopingOptions
from scoping.task import ScopingTask
from scoping.sas_parser import SasParser
from scoping.visualization import TaskGraph
from scoping.core import scope


# DOM elements
UPLOAD_BTN = document["upload_file"]
DOWNLOAD_BTN = document["download_file"]
ENABLE_CAUSAL_LINKS = document["enable_causal_links"]
ENABLE_MERGING = document["enable_merging"]
ENABLE_FACT_BASED = document["enable_fact_based"]
ENABLE_FORWARD_PASS = document["enable_forward_pass"]
ENABLE_LOOP = document["enable_loop"]
VISUALIZE = document["visualize"]
VISUALIZE_BACK = document["visualize_back"]


# Objects
sas_parser = SasParser(s_sas="")
sas_task = None
graph = None
scoping_options = ScopingOptions(
    enable_causal_links=False,
    enable_merging=False,
    enable_forward_pass=False,
    enable_loop=False
)
layer_count = 0
visible_layers = 1


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
            return

    if step_back:
        visible_layers -= 2

    if visible_layers <= 1:
        VISUALIZE_BACK.disabled = True
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
        """Triggered when file is read. The FileReader instance is
        event.target.
        The file content, as text, is the FileReader instance's "result"
        attribute."""
        DOWNLOAD_BTN.style.display = "inline"
        DOWNLOAD_BTN.attrs["download"] = file.name

        scoped_task, layers = read_sas(event.target.result)
        write_json(layers)

        f = io.StringIO()
        scoped_task.to_sas().output(f)
        document['sas_content'].value = f.getvalue()

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


@bind(DOWNLOAD_BTN, "mousedown")
def mousedown(ev):
    """Create a "data URI" to set the downloaded file content
    Cf. https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/Data_URIs
    """
    content = window.encodeURIComponent(document['sas_content'].value)
    DOWNLOAD_BTN.attrs["href"] = "data:text/plain," + content


@bind(ENABLE_CAUSAL_LINKS, "click")
def toggle_causal_links(ev):
    scoping_options.enable_causal_links = not scoping_options.enable_causal_links
    set_toggle_content(ENABLE_CAUSAL_LINKS, scoping_options.enable_causal_links)


@bind(ENABLE_MERGING, "click")
def toggle_merging(ev):
    scoping_options.enable_merging = not scoping_options.enable_merging
    set_toggle_content(ENABLE_MERGING, scoping_options.enable_merging)


@bind(ENABLE_FACT_BASED, "click")
def toggle_fact_based(ev):
    scoping_options.enable_fact_based = not scoping_options.enable_fact_based
    set_toggle_content(ENABLE_FACT_BASED, scoping_options.enable_fact_based)


@bind(ENABLE_FORWARD_PASS, "click")
def toggle_forward_pass(ev):
    scoping_options.enable_forward_pass = not scoping_options.enable_forward_pass
    set_toggle_content(ENABLE_FORWARD_PASS, scoping_options.enable_forward_pass)


@bind(ENABLE_LOOP, "click")
def toggle_loop(ev):
    scoping_options.enable_loop = not scoping_options.enable_loop
    set_toggle_content(ENABLE_LOOP, scoping_options.enable_loop)


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
    opt = " ".join(btn.textContent.split()[1:])
    btn.textContent = f"Disable {opt}" if flag else f"Enable {opt}"


def write_json(layers):
    data = {"nodes": [], "links": []}
    node_names = []

    for i in range(len(layers)):
        layer = layers[i]
        for node in layer:
            if node.name not in node_names:
                node_names.append(node.name)
                data["nodes"].append({"id": node.name, "group": i})
                for p in node.parents:
                    data["links"].append({"source": p.name, "target": node.name})

    for op in sas_task.operators:
        if op.name not in node_names:
            node_names.append(op.name)
            data["nodes"].append({"id": op.name, "group": len(layers)})

    storage["scoping_data"] = json.dumps(data)
