import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

const network = (data) => {
    const width = 928;
    const height = 600;

    const color = d3.scaleOrdinal(d3.schemeCategory10);

    const links = data.links.map((d) => ({ ...d }));
    const nodes = data.nodes.map((d) => ({ ...d }));

    const simulation = d3
        .forceSimulation(nodes)
        .force(
            "link",
            d3
                .forceLink(links)
                .id((d) => d.id)
                .distance(100)
        )
        .force("charge", d3.forceManyBody())
        .force("center", d3.forceCenter(width / 2, height / 2))
        .on("tick", ticked);

    const svg = d3
        .create("svg")
        .attr("width", width)
        .attr("height", height)
        .attr("viewBox", [0, 0, width, height])
        .attr("style", "max-width: 100%; height: auto; background: #e5e5e5")
        .attr("id", "networkDiv");

    svg.append("defs")
        .append("marker")
        .attr("id", "arrowhead")
        .attr("viewBox", "0 -5 10 10")
        .attr("refX", 20)
        .attr("refY", 0)
        .attr("markerWidth", 6)
        .attr("markerHeight", 6)
        .attr("orient", "auto")
        .append("path")
        .attr("d", "M0,-5L10,0L0,5")
        .attr("fill", "#999");

    const link = svg
        .append("g")
        .attr("stroke", "#999")
        .attr("stroke-opacity", 0.6)
        .selectAll()
        .data(links)
        .join("line")
        .attr("stroke-width", (d) => Math.sqrt(d.value || 1))
        .attr("marker-end", "url(#arrowhead)");

    const node = svg
        .append("g")
        .selectAll()
        .data(nodes)
        .join("circle")
        .attr("r", 20)
        .attr("fill", (d) => color(d.group));

    const label = svg
        .append("g")
        .attr("class", "labels")
        .selectAll("text")
        .data(nodes)
        .join("text")
        .attr("text-anchor", "middle")
        .attr("font-size", 10)
        .attr("dy", "0.3em")
        .text((d) => d.id);

    node.append("title").text((d) => d.id);

    node.call(
        d3
            .drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended)
    );

    function ticked() {
        link.attr("x1", (d) => d.source.x)
            .attr("y1", (d) => d.source.y)
            .attr("x2", (d) => {
                const dx = d.target.x - d.source.x;
                const dy = d.target.y - d.source.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                return dist === 0 ? d.target.x : d.target.x - (dx * 14) / dist;
            })
            .attr("y2", (d) => {
                const dx = d.target.x - d.source.x;
                const dy = d.target.y - d.source.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                return dist === 0 ? d.target.y : d.target.y - (dy * 14) / dist;
            });

        node.attr("cx", (d) => d.x).attr("cy", (d) => d.y);

        label.attr("x", (d) => d.x).attr("y", (d) => d.y - 30);
    }

    function dragstarted(event) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        event.subject.fx = event.subject.x;
        event.subject.fy = event.subject.y;
    }

    function dragged(event) {
        event.subject.fx = event.x;
        event.subject.fy = event.y;
    }

    function dragended(event) {
        if (!event.active) simulation.alphaTarget(0);
        event.subject.fx = null;
        event.subject.fy = null;
    }

    return svg.node();
};

const drawNetwork = ({ step_back }) => {
    if (step_back) visible_layers--;
    else visible_layers++;

    const data = JSON.parse(window.localStorage.getItem("scoping_data"));

    const visible_nodes = data.nodes
        .filter((n) => n.group <= visible_layers)
        .map((n) => n.id);
    data.links = data.links.filter(
        (l) =>
            visible_nodes.includes(l.source) && visible_nodes.includes(l.target)
    );

    const container = document.getElementById("container");
    const networkDiv = document.getElementById("networkDiv");
    if (networkDiv) container.removeChild(networkDiv);
    container.append(network(data));
};

let visible_layers = -1;
document.getElementById("visualize").onclick = () =>
    drawNetwork({ step_back: false });
document.getElementById("visualize_back").onclick = () =>
    drawNetwork({ step_back: true });
