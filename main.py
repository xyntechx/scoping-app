from browser import bind, window, document, html

from scoping.options import ScopingOptions
from scoping.task import ScopingTask
from scoping.sas_parser import SasParser
from scoping.visualization import TaskGraph


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
GRAPH_CONTAINER = document["graph_container"]


# Objects
sas_parser = SasParser(s_sas="")
sas_task = None
graph = None
scoping_options = ScopingOptions(enable_forward_pass=False, enable_loop=False)
layer_count = 0
visible_layers = 1


def main():
    set_toggle_content(ENABLE_MERGING, scoping_options.enable_merging)


def visualize(step_back=False):
    global graph
    global layer_count
    global visible_layers

    if layer_count > 0 and visible_layers > layer_count:
        if not step_back:
            return

    for i in range(min(visible_layers - 1, layer_count)):
        # Clear container if it contains subcontainers
        del document[f"graph_subcontainer_{i}"]

    if step_back:
        visible_layers -= 2

    for i in range(min(visible_layers, layer_count)):
        layer = graph.layers[i]
        if layer:
            draw_subcontainer(i)
        for node in layer:
            draw_node(i, node)

    if visible_layers <= 1:
        VISUALIZE_BACK.disabled = True
    else:
        VISUALIZE_BACK.disabled = False

    if visible_layers >= layer_count:
        VISUALIZE.disabled = True
    else:
        VISUALIZE.disabled = False

    visible_layers += 1


def draw_subcontainer(idx):
    GRAPH_CONTAINER <= html.DIV(id=f"graph_subcontainer_{idx}", style={"display": "flex", "align-items": "center", "justify-content": "center", "flex-direction": "column", "row-gap": "1rem", "margin": "0", "padding": "0"})


def draw_node(idx, op):
    name = html.P(op.name, style={"font-weight": "bold", "margin": "0"})
    op_div = html.DIV(id=f"op {name}", style={"display": "flex", "align-items": "center", "justify-content": "center", "flex-direction": "column", "gap": "0", "border": "1px solid black", "border-radius": "1rem", "padding": "1rem", "min-width": "100px", "margin": "0"})

    op_div <= name
    op_div <= html.HR(style={"width": "100%"})
    if not op.precondition:
        op_div <= html.BR()
    for precond in op.precondition:
        op_div <= html.P(f"('{precond[0]}', {precond[1]})", style={"margin": "0"})
    if op.effect:
        op_div <= html.HR(style={"width": "100%"})
    for eff in op.effect:
        op_div <= html.P(f"('{eff[0]}', {eff[1]})", style={"margin": "0"})

    SUBCONTAINER = document[f"graph_subcontainer_{idx}"]
    SUBCONTAINER <= op_div


@bind(UPLOAD_BTN, "input")
def file_read(ev):
    global layer_count

    def onload(event):
        """Triggered when file is read. The FileReader instance is
        event.target.
        The file content, as text, is the FileReader instance's "result"
        attribute."""
        document['sas_content'].value = event.target.result

        DOWNLOAD_BTN.style.display = "inline"
        DOWNLOAD_BTN.attrs["download"] = file.name

        read_sas(event.target.result)

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
    graph.layers = [l for l in graph.layers if l]
    layer_count = len(graph.layers)


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
