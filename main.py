from browser import bind, window, document

from scoping.actions import VarValAction
from scoping.factset import FactSet
from scoping.options import ScopingOptions
from scoping.task import ScopingTask
from scoping.core import scope
from scoping.sas_parser import SasParser


# DOM elements
UPLOAD_BTN = document["upload_file"]
DOWNLOAD_BTN = document["download_file"]
ENABLE_CAUSAL_LINKS = document["enable_causal_links"]
ENABLE_MERGING = document["enable_merging"]
ENABLE_FACT_BASED = document["enable_fact_based"]
ENABLE_FORWARD_PASS = document["enable_forward_pass"]
ENABLE_LOOP = document["enable_loop"]
VISUALIZE = document["visualize"]

# Objects
sas_parser = SasParser(s_sas="")
sas_task_wrapper = [None]
scoping_options = ScopingOptions()


def main():
    document <= "this is main()"
    set_toggle_content(ENABLE_MERGING, scoping_options.enable_merging)


def visualize(sas_task):
    document <= "tis is visualize()"

    scoping_task = ScopingTask.from_sas(sas_task)
    scoped_task = scope(scoping_task, scoping_options)
    scoped_task.dump()

    document <= "tis is visualize() make task"


@bind(UPLOAD_BTN, "input")
def file_read(ev):
    def onload(event):
        """Triggered when file is read. The FileReader instance is
        event.target.
        The file content, as text, is the FileReader instance's "result"
        attribute."""
        document['sas_content'].value = event.target.result

        DOWNLOAD_BTN.style.display = "inline"
        DOWNLOAD_BTN.attrs["download"] = file.name

        sas_task_wrapper[0] = read_sas(event.target.result)

        VISUALIZE.disabled = False

    file = UPLOAD_BTN.files[0]
    reader = window.FileReader.new()
    reader.readAsText(file)
    reader.bind("load", onload)


def read_sas(sas_file):
    # Read uploaded .sas file
    sas_parser.s_sas = sas_file
    sas_parser.parse()
    sas_task = sas_parser.to_fd()
    # sas_task.dump()
    return sas_task


@bind(DOWNLOAD_BTN, "mousedown")
def mousedown(ev):
    """Create a "data URI" to set the downloaded file content
    Cf. https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/Data_URIs
    """
    content = window.encodeURIComponent(document['sas_content'].value)
    # set attribute "href" of save link
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
    visualize(sas_task_wrapper[0])


def set_toggle_content(btn, flag):
    opt = " ".join(btn.textContent.split()[1:])
    btn.textContent = f"Disable {opt}" if flag else f"Enable {opt}"
