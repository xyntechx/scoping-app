import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";
import "https://esm.sh/d3-transition";

const NODE_CONFIG = { shape: "rect", width: 20, height: 20, radius: 6 };
const LABEL_OFFSET = { x: 10, y: 10 };
const CANVAS = { width: 1000, height: 600 };
const DURATION = { normal: 1000, exit: 500 };

let visibleLayers = -1;
let xPositionScale;

// Utility functions
const createXScale = (nodes, isForward) => {
    const [min, max] = d3.extent(nodes, d => d.group);
    const domain = isForward ? [min, max] : [max, min];
    return d3.scaleLinear().domain(domain).range([CANVAS.width * 0.2, CANVAS.width * 0.8]);
};

const getSourceTarget = (link, nodes) => {
    const source = typeof link.source === "object" ? link.source : nodes.find(n => n.id === link.source);
    const target = typeof link.target === "object" ? link.target : nodes.find(n => n.id === link.target);
    return { source, target };
};

const positionLink = (link, nodes, useOld = false) => {
    const { source, target } = getSourceTarget(link, nodes);
    if (!source || !target) return { x1: 0, y1: 0, x2: 0, y2: 0 };

    const sx = useOld ? source.oldX : source.x;
    const sy = useOld ? source.oldY : source.y;
    const tx = useOld ? target.oldX : target.x;
    const ty = useOld ? target.oldY : target.y;

    const dx = tx - sx, dy = ty - sy;
    const dist = Math.sqrt(dx * dx + dy * dy);

    return {
        x1: sx, y1: sy,
        x2: dist === 0 ? tx : tx - (dx * 14) / dist,
        y2: dist === 0 ? ty : ty - (dy * 14) / dist
    };
};

const setupSVG = () => {
    const svg = d3.create("svg")
        .attr("width", CANVAS.width).attr("height", CANVAS.height)
        .attr("viewBox", [0, 0, CANVAS.width, CANVAS.height])
        .attr("style", "max-width: 100%; height: auto; background: #e5e5e5")
        .attr("id", "networkDiv");

    svg.append("defs").append("marker")
        .attr("id", "arrowhead").attr("viewBox", "0 -5 10 10")
        .attr("refX", 20).attr("refY", 0).attr("markerWidth", 6).attr("markerHeight", 6)
        .attr("orient", "auto").append("path")
        .attr("d", "M0,-5L10,0L0,5").attr("fill", "#999");

    return svg;
};

const createDragBehavior = (simulation) => d3.drag()
    .on("start", event => {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        event.subject.fx = event.subject.x;
        event.subject.fy = event.subject.y;
    })
    .on("drag", event => {
        event.subject.fx = xPositionScale(event.subject.group);
        event.subject.fy = event.y;
    })
    .on("end", event => {
        if (!event.active) simulation.alphaTarget(0);
        event.subject.fx = xPositionScale(event.subject.group);
        event.subject.fy = null;
    });

const tick = (linkSelection, nodeSelection, labelSelection) => {
    const nodes = nodeSelection.data();

    nodes.forEach(node => {
        node.x = node.visible ? xPositionScale(node.group) : node.xPos;
        node.y = Math.max(50, Math.min(CANVAS.height - 50, node.y));
    });

    linkSelection.each(function (d) {
        const pos = positionLink(d, nodes);
        d3.select(this).attr("x1", pos.x1).attr("y1", pos.y1).attr("x2", pos.x2).attr("y2", pos.y2);
    });

    nodeSelection.attr("x", d => d.x).attr("y", d => d.y);
    labelSelection.attr("x", d => d.x).attr("y", d => d.y - LABEL_OFFSET.y);
};

const updateSelection = (selection, data, keyFn, enterFn, updateFn) => {
    const update = selection.data(data, keyFn);
    update.exit().transition().duration(DURATION.exit).style("opacity", 0).remove();
    const enter = enterFn(update.enter());
    updateFn(enter.merge(update));
    return enter.merge(update);
};

const createNetwork = (data) => {
    const links = data.links.map(d => ({ ...d }));
    const nodes = data.nodes.map(d => ({ ...d }));

    xPositionScale = createXScale(nodes, data.is_forward);
    nodes.forEach(node => {
        node.x = xPositionScale(node.group);
        node.y = CANVAS.height / 2 + (Math.random() - 0.5) * CANVAS.height * 0.5;
    });

    const svg = setupSVG();

    const linkSelection = svg.append("g").attr("stroke", "#999").attr("stroke-opacity", 0.6)
        .selectAll().data(links).join("line")
        .attr("stroke-width", d => Math.sqrt(d.value || 1))
        .attr("marker-end", "url(#arrowhead)");

    const nodeSelection = svg.append("g").selectAll().data(nodes).join(NODE_CONFIG.shape)
        .attr("rx", NODE_CONFIG.radius).attr("ry", NODE_CONFIG.radius)
        .attr("width", NODE_CONFIG.width).attr("height", NODE_CONFIG.height)
        .attr("fill", "#fff").on("click", (e, d) => drawNodeDetails(d));

    const labelSelection = svg.append("g").attr("class", "labels")
        .selectAll("text").data(nodes).join("text")
        .attr("text-anchor", "middle").attr("font-size", 10).attr("dy", "0.3em")
        .text(d => d.id);

    nodeSelection.append("title").text(d => d.id);

    const simulation = d3.forceSimulation(nodes)
        .force("link", d3.forceLink(links).id(d => d.id).distance(100))
        .force("charge", d3.forceManyBody().strength(-100))
        .force("center", d3.forceCenter(CANVAS.width / 2, CANVAS.height / 2))
        .force("x", d3.forceX(d => xPositionScale(d.group)).strength(1))
        .force("y", d3.forceY(CANVAS.height / 2).strength(0.1))
        .force("collision", d3.forceCollide(25))
        .on("tick", () => tick(linkSelection, nodeSelection, labelSelection));

    nodeSelection.call(createDragBehavior(simulation));
    return svg.node();
};

const updateNetwork = (data) => {
    const links = data.links.map(d => ({ ...d }));
    const nodes = data.nodes.map(d => ({ ...d }));

    // Get current positions and update node positions
    const currentNodes = {};
    d3.select("#networkDiv").select("g:nth-of-type(2)").selectAll(NODE_CONFIG.shape)
        .each(function (d) {
            if (d?.id) {
                currentNodes[d.id] = { x: +d3.select(this).attr("x"), y: +d3.select(this).attr("y") };
            }
        });

    xPositionScale = createXScale(nodes, data.is_forward);
    nodes.forEach(node => {
        const current = currentNodes[node.id];
        node.oldX = current?.x ?? CANVAS.width / 2;
        node.oldY = current?.y ?? CANVAS.height / 2;
        node.y = current?.y ?? CANVAS.height / 2 + (Math.random() - 0.5) * CANVAS.height * 0.5;
        node.x = node.visible ? xPositionScale(node.group) : node.xPos;
    });

    const svg = d3.select("#networkDiv");

    // Update links
    updateSelection(
        svg.select("g:nth-of-type(1)").selectAll("line"),
        links,
        d => `${d.source.id || d.source}-${d.target.id || d.target}`,
        enter => {
            const enterSelection = enter.append("line")
                .attr("stroke", "#999").attr("stroke-opacity", 0.6)
                .attr("stroke-width", d => Math.sqrt(d.value || 1))
                .attr("marker-end", "url(#arrowhead)");

            // Set initial positions for animation
            enterSelection.each(function (d) {
                const pos = positionLink(d, nodes, true);
                d3.select(this).attr("x1", pos.x1).attr("y1", pos.y1).attr("x2", pos.x2).attr("y2", pos.y2);
            });

            return enterSelection;
        },
        selection => {
            const transition = selection.transition().duration(DURATION.normal).attr("stroke-opacity", 0.6);

            // Animate to final positions
            transition.attr("x1", d => {
                const { source } = getSourceTarget(d, nodes);
                return source ? source.x : 0;
            })
                .attr("y1", d => {
                    const { source } = getSourceTarget(d, nodes);
                    return source ? source.y : 0;
                })
                .attr("x2", d => {
                    const pos = positionLink(d, nodes);
                    return pos.x2;
                })
                .attr("y2", d => {
                    const pos = positionLink(d, nodes);
                    return pos.y2;
                });
        }
    );

    // Update nodes
    updateSelection(
        svg.select("g:nth-of-type(2)").selectAll(NODE_CONFIG.shape),
        nodes,
        d => d.id,
        enter => enter.append(NODE_CONFIG.shape)
            .attr("width", 0).attr("height", 0).attr("fill", "#fff")
            .attr("x", d => d.oldX || 0).attr("y", d => d.oldY || CANVAS.height / 2)
            .on("click", (e, d) => drawNodeDetails(d))
            .call(sel => sel.append("title").text(d => d.id)),
        selection => selection.transition().duration(DURATION.normal)
            .attr("width", NODE_CONFIG.width).attr("height", NODE_CONFIG.height)
            .attr("x", d => d.x).attr("y", d => d.y)
    );

    // Update labels
    updateSelection(
        svg.select("g.labels").selectAll("text"),
        nodes,
        d => d.id,
        enter => enter.append("text")
            .attr("text-anchor", "middle").attr("font-size", 10).attr("dy", "0.3em")
            .attr("opacity", 0).text(d => d.id),
        selection => selection.transition().duration(DURATION.normal).attr("opacity", 1)
            .attr("x", d => d.x + LABEL_OFFSET.x).attr("y", d => d.y - LABEL_OFFSET.y)
    );
};

const drawNodeDetails = (node) => {
    const svg = d3.create("svg")
        .attr("width", 300).attr("height", 215).attr("viewBox", [0, 0, 300, 215])
        .attr("style", "max-width: 100%; height: auto; background: transparent;")
        .attr("id", "nodeDetailsText");

    const preconditions = node.precondition.map(p => `(${p.split(" ")[0]},${p.split(" ")[1]})`);
    const effects = node.effect.map(e => `(${e.split(" ")[0]},${e.split(" ")[1]})`);

    svg.append("foreignObject").attr("width", 300).attr("height", 300)
        .append("xhtml:div")
        .style("background-color", "#efefef").style("border", "solid")
        .style("border-width", "1px").style("border-radius", "5px")
        .style("padding", "10px").style("width", "300px").style("height", "300px")
        .html(`<p>${node.id}</p><p>Preconditions:</p><p>${preconditions}</p><p>Effects:</p><p>${effects}</p>`);

    const container = document.getElementById("nodeDetails");
    const existing = document.getElementById("nodeDetailsText");
    if (existing) container.removeChild(existing);
    container.append(svg.node());
};

const drawNetwork = ({ stepBack }) => {
    const isNew = visibleLayers === -1;
    stepBack ? visibleLayers-- : visibleLayers++;
    if (visibleLayers < -1) visibleLayers = -1;

    const data = JSON.parse(window.localStorage.getItem("scoping_data"));
    const visibleNodes = data.nodes.filter(n => n.group <= visibleLayers).map(n => n.id);

    data.links = data.links.filter(l => visibleNodes.includes(l.source) && visibleNodes.includes(l.target));
    data.nodes.forEach(node => {
        node.visible = visibleNodes.includes(node.id);
        if (!node.visible) node.xPos = data.is_forward ? 970 : 30;
    });

    const container = document.getElementById("container");
    const networkDiv = document.getElementById("networkDiv");

    if (isNew && !networkDiv) container.append(createNetwork(data));
    else updateNetwork(data);
};

// Event handlers
document.getElementById("visualize").onclick = () => drawNetwork({ stepBack: false });
document.getElementById("visualize_back").onclick = () => drawNetwork({ stepBack: true });
document.getElementById("enable_forward_pass").onclick = () => (visibleLayers = -1);
