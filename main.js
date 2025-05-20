import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";
import "https://esm.sh/d3-transition"; // use .transition() for animations

const createNetwork = (data) => {
    // Initializes the D3 graph

    const width = 1000;
    const height = 600;

    const links = data.links.map((d) => ({ ...d }));
    const nodes = data.nodes.map((d) => ({ ...d }));

    let xPositionScale; // controls how the x position of each node is determined

    if (data.is_forward) {
        // when forward pass, nodes with lower group numbers lie more to the left (i.e. init and * are the leftmost nodes)
        xPositionScale = d3
            .scaleLinear()
            .domain([
                d3.min(nodes, (d) => d.group),
                d3.max(nodes, (d) => d.group),
            ])
            .range([width * 0.2, width * 0.8]);
    } else {
        // when backward pass, nodes with lower group numbers lie more to the right (i.e. goal is the rightmost node)
        xPositionScale = d3
            .scaleLinear()
            .domain([
                d3.max(nodes, (d) => d.group),
                d3.min(nodes, (d) => d.group),
            ])
            .range([width * 0.2, width * 0.8]);
    }

    nodes.forEach((node) => {
        // inits x and y positions of all nodes
        node.x = xPositionScale(node.group); // uses the xPositionScale function defined above
        node.y = height / 2 + (Math.random() - 0.5) * height * 0.5; // randomly initialized
    });

    const simulation = d3
        .forceSimulation(nodes)
        .force(
            "link",
            d3
                .forceLink(links)
                .id((d) => d.id)
                .distance(100)
        )
        .force("charge", d3.forceManyBody().strength(-100))
        .force("center", d3.forceCenter(width / 2, height / 2))
        .force("x", d3.forceX((d) => xPositionScale(d.group)).strength(1))
        .force("y", d3.forceY(height / 2).strength(0.1))
        .force("collision", d3.forceCollide(25))
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
        .attr("fill", (d) => "#fff")
        .on("click", (e, d) => drawNodeDetails(d));

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
        // more init code
        nodes.forEach((node) => {
            if (node.visible) {
                node.x = xPositionScale(node.group);
            } else {
                node.x = node.xPos;
            }
            node.y = Math.max(50, Math.min(height - 50, node.y));
        });

        // link starts at parent, ends at child
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
        event.subject.fx = xPositionScale(event.subject.group);
        event.subject.fy = event.y;
    }

    function dragended(event) {
        if (!event.active) simulation.alphaTarget(0);
        event.subject.fx = xPositionScale(event.subject.group);
        event.subject.fy = null;
    }

    return svg.node();
};

const updateNetwork = (data) => {
    // Updates the D3 graph whenever data is updated

    const width = 1000;
    const height = 600;

    const links = data.links.map((d) => ({ ...d }));
    const nodes = data.nodes.map((d) => ({ ...d }));

    // Gets nodes directly from DOM. Particularly interested in each of their x,y positions.
    const currentNodes = {};
    d3.select("#networkDiv")
        .select("g:nth-of-type(2)")
        .selectAll("circle")
        .each(function (d) {
            if (d && d.id) {
                currentNodes[d.id] = {
                    x: parseFloat(d3.select(this).attr("cx")),
                    y: parseFloat(d3.select(this).attr("cy")),
                };
            }
        });

    let xPositionScale; // same thing as in `createNetwork`

    if (data.is_forward) {
        xPositionScale = d3
            .scaleLinear()
            .domain([
                d3.min(nodes, (d) => d.group),
                d3.max(nodes, (d) => d.group),
            ])
            .range([width * 0.2, width * 0.8]);
    } else {
        xPositionScale = d3
            .scaleLinear()
            .domain([
                d3.max(nodes, (d) => d.group),
                d3.min(nodes, (d) => d.group),
            ])
            .range([width * 0.2, width * 0.8]);
    }

    nodes.forEach((node) => {
        // init code, useful for transitions (animations)
        if (currentNodes[node.id]) {
            node.oldX = currentNodes[node.id].x;
            node.oldY = currentNodes[node.id].y;
            node.y = currentNodes[node.id].y;
        } else {
            node.oldX = width / 2;
            node.oldY = height / 2;
            node.y = height / 2 + (Math.random() - 0.5) * height * 0.5;
        }

        // if the node is currently visible (i.e. has links adjacent to it; already part of graph) then its x position should follow its group's assigned x position. Otherwise, stay on the leftmost/rightmost side (depending on whether it's currently backward/forward pass).
        node.x = node.visible ? xPositionScale(node.group) : node.xPos;
    });

    const svg = d3.select("#networkDiv");

    const link = svg
        .select("g:nth-of-type(1)")
        .selectAll("line")
        .data(
            links,
            (d) => `${d.source.id || d.source}-${d.target.id || d.target}`
        );

    link.exit().transition().duration(500).attr("stroke-opacity", 0).remove();

    const linkEnter = link
        .enter()
        .append("line")
        .attr("stroke", "#999")
        .attr("stroke-opacity", 0)
        .attr("stroke-width", (d) => Math.sqrt(d.value || 1))
        .attr("marker-end", "url(#arrowhead)")
        .attr("x1", (d) => d.source.oldX || width / 2)
        .attr("y1", (d) => d.source.oldY || height / 2)
        .attr("x2", (d) => d.target.oldX || width / 2)
        .attr("y2", (d) => d.target.oldY || height / 2);

    linkEnter
        .merge(link)
        .transition()
        .duration(1000)
        .attr("stroke-opacity", 0.6)
        .attr("x1", (d) =>
            typeof d.source === "object"
                ? d.source.x
                : nodes.find((n) => n.id === d.source).x
        )
        .attr("y1", (d) =>
            typeof d.source === "object"
                ? d.source.y
                : nodes.find((n) => n.id === d.source).y
        )
        .attr("x2", (d) => {
            const source =
                typeof d.source === "object"
                    ? d.source
                    : nodes.find((n) => n.id === d.source);
            const target =
                typeof d.target === "object"
                    ? d.target
                    : nodes.find((n) => n.id === d.target);
            const dx = target.x - source.x;
            const dy = target.y - source.y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            return dist === 0 ? target.x : target.x - (dx * 14) / dist;
        })
        .attr("y2", (d) => {
            const source =
                typeof d.source === "object"
                    ? d.source
                    : nodes.find((n) => n.id === d.source);
            const target =
                typeof d.target === "object"
                    ? d.target
                    : nodes.find((n) => n.id === d.target);
            const dx = target.x - source.x;
            const dy = target.y - source.y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            return dist === 0 ? target.y : target.y - (dy * 14) / dist;
        });

    const node = svg
        .select("g:nth-of-type(2)")
        .selectAll("circle")
        .data(nodes, (d) => d.id);

    node.exit().transition().duration(500).attr("r", 0).remove();

    const nodeEnter = node
        .enter()
        .append("circle")
        .attr("r", 0)
        .attr("fill", "#fff")
        .attr("cx", (d) => d.oldX || 0)
        .attr("cy", (d) => d.oldY || height / 2)
        .on("click", (e, d) => drawNodeDetails(d));

    nodeEnter.append("title").text((d) => d.id);

    nodeEnter.call(
        d3
            .drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended)
    );

    nodeEnter
        .merge(node)
        .transition()
        .duration(1000)
        .attr("r", 20)
        .attr("cx", (d) => d.x)
        .attr("cy", (d) => d.y);

    const label = svg
        .select("g.labels")
        .selectAll("text")
        .data(nodes, (d) => d.id);

    label.exit().transition().duration(500).attr("opacity", 0).remove();

    const labelEnter = label
        .enter()
        .append("text")
        .attr("text-anchor", "middle")
        .attr("font-size", 10)
        .attr("dy", "0.3em")
        .attr("opacity", 0)
        .attr("x", (d) => d.oldX || 0)
        .attr("y", (d) => d.oldY - 30 || height / 2 - 30)
        .text((d) => d.id);

    labelEnter
        .merge(label)
        .transition()
        .duration(1000)
        .attr("opacity", 1)
        .attr("x", (d) => d.x)
        .attr("y", (d) => d.y - 30);

    function dragstarted(event) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        event.subject.fx = event.subject.x;
        event.subject.fy = event.subject.y;
    }

    function dragged(event) {
        event.subject.fx = xPositionScale(event.subject.group);
        event.subject.fy = event.y;
    }

    function dragended(event) {
        if (!event.active) simulation.alphaTarget(0);
        event.subject.fx = xPositionScale(event.subject.group);
        event.subject.fy = null;
    }
};

const nodeDetails = (node) => {
    // Creates the details box onClick of a node

    const width = 500;
    const height = 215;

    const svg = d3
        .create("svg")
        .attr("width", width)
        .attr("height", height)
        .attr("viewBox", [0, 0, width, height])
        .attr("style", "max-width: 100%; height: auto; background: #fff;")
        .attr("id", "nodeDetailsText");

    const info = svg
        .append("foreignObject")
        .attr("width", 300)
        .attr("height", 300)
        .attr("x", (width - 300) / 2)
        .attr("y", 0);

    const div = info
        .append("xhtml:div")
        .style("background-color", "#efefef")
        .style("border", "solid")
        .style("border-width", "1px")
        .style("border-radius", "5px")
        .style("padding", "10px")
        .style("width", 300)
        .style("height", 300)
        .html(
            `<p>${node.id}</p><p>Preconditions:</p><p>${node.precondition.map(
                (precond) =>
                    `(${precond.split(" ")[0]},${precond.split(" ")[1]})`
            )}</p><p>Effects:</p><p>${node.effect.map(
                (eff) => `(${eff.split(" ")[0]},${eff.split(" ")[1]})`
            )}</p>`
        );

    return svg.node();
};

const drawNodeDetails = (node) => {
    // Actually attaches the nodeDetails element to the DOM
    const elem = nodeDetails(node);
    const container = document.getElementById("nodeDetails");
    const nodeDetailsText = document.getElementById("nodeDetailsText");
    if (nodeDetailsText) container.removeChild(nodeDetailsText);
    container.append(elem);
};

const drawNetwork = ({ step_back }) => {
    // Actually attaches the graph (network) element to the DOM
    // Also reads localStorage and processes the graph data for rendering

    const isNew = visible_layers === -1;

    if (step_back) visible_layers--;
    else visible_layers++;

    if (visible_layers < -1) visible_layers = -1;

    const data = JSON.parse(window.localStorage.getItem("scoping_data"));

    const visible_nodes = data.nodes
        .filter((n) => n.group <= visible_layers)
        .map((n) => n.id);

    data.links = data.links.filter(
        (l) =>
            visible_nodes.includes(l.source) && visible_nodes.includes(l.target)
    );

    for (let i = 0; i < data.nodes.length; i++) {
        const name = data.nodes[i].id;
        if (!visible_nodes.includes(name)) {
            // if node currently not visible, set its x position to leftmost (if backward pass) or rightmost (if forward pass)
            data.nodes[i].visible = false;
            if (data.is_forward) data.nodes[i].xPos = 970;
            else data.nodes[i].xPos = 30;
        } else {
            data.nodes[i].visible = true;
        }
    }

    const container = document.getElementById("container");
    const networkDiv = document.getElementById("networkDiv");

    if (isNew && !networkDiv) container.append(createNetwork(data));
    else updateNetwork(data);
};

let visible_layers = -1;
document.getElementById("visualize").onclick = () =>
    drawNetwork({ step_back: false });
document.getElementById("visualize_back").onclick = () =>
    drawNetwork({ step_back: true });

document.getElementById("enable_forward_pass").onclick = () =>
    (visible_layers = -1);
