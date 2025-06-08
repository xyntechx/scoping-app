let simulation;
let canvas, context;
let networkData = null;
let visibleLayers = -1;
let maxLayers = 0;
let nodes = [];
let links = [];
let transform = d3.zoomIdentity;
let isLoad = true;

const width = 1000;
const height = 600;
const nodeRadius = 6;

const init = () => {
    canvas = d3.select("#networkCanvas");
    context = canvas.node().getContext("2d");
    canvas.call(d3.zoom().scaleExtent([0.1, 4]).on("zoom", zoomed));
    canvas.on("click", handleCanvasClick);
};

const zoomed = (event) => {
    transform = event.transform;
    drawNetwork();
};

const handleCanvasClick = (event) => {
    const [mouseX, mouseY] = d3.pointer(event);
    const [x, y] = transform.invert([mouseX, mouseY]);

    const clickedNode = nodes.find((node) => {
        const dx = x - node.x;
        const dy = y - node.y;
        return Math.sqrt(dx * dx + dy * dy) < nodeRadius + 5;
    });

    if (clickedNode) {
        showNodeDetails(clickedNode);
    }
};

const hasConnections = (nodeId, links) => {
    return links.some(
        (link) =>
            link.source === nodeId ||
            link.target === nodeId ||
            (typeof link.source === "object" && link.source.id === nodeId) ||
            (typeof link.target === "object" && link.target.id === nodeId)
    );
};

const getClusterX = () => {
    console.log(networkData.is_forward);
    return networkData && networkData.is_forward ? width - 80 : 80;
};

const getNodeX = (node) => {
    if (node.isolated || !node.visible) {
        return getClusterX();
    }

    if (networkData.is_forward) {
        return width * (0.1 + (0.8 * node.group) / maxLayers);
    } else {
        return width * (0.9 - (0.8 * node.group) / maxLayers);
    }
};

const loadData = () => {
    networkData = JSON.parse(window.localStorage.getItem("scoping_data"));

    maxLayers = Math.max(...networkData.nodes.map((n) => n.group));
    visibleLayers = -1;

    nodes = [];
    updateButtons();
    createNetwork();
};

const createNetwork = () => {
    if (!networkData) return;

    const clusterX = getClusterX();

    if (nodes.length === 0) {
        nodes = networkData.nodes.map((d, index) => {
            return {
                ...d,
                x: clusterX + (Math.random() - 0.5) * 60,
                y: height / 2 + (Math.random() - 0.5) * height * 0.6,
                visible: d.group <= visibleLayers,
                isolated: !hasConnections(d.id, networkData.links),
            };
        });
    } else {
        nodes.forEach((node) => {
            node.visible = node.group <= visibleLayers;
            node.isolated = !hasConnections(node.id, networkData.links);
        });
    }

    links = networkData.links.map((d) => ({
        source: nodes.find((n) => n.id === d.source),
        target: nodes.find((n) => n.id === d.target),
    }));

    if (simulation) simulation.stop();

    simulation = d3
        .forceSimulation(nodes)
        .force(
            "link",
            d3
                .forceLink(links)
                .id((d) => d.id)
                .strength((d) => {
                    return d.source.visible && d.target.visible ? 0.6 : 0.1;
                })
                .distance((d) => {
                    return d.source.visible && d.target.visible ? 80 : 20;
                })
        )
        .force(
            "charge",
            d3.forceManyBody().strength((d) => {
                return d.visible && !d.isolated ? -200 : -50;
            })
        )
        .force(
            "x",
            d3
                .forceX((d) => getNodeX(d))
                .strength((d) => {
                    if (d.isolated) return 3.0;
                    return d.visible ? 2.5 : 2.0;
                })
        )
        .force(
            "y",
            d3.forceY(height / 2).strength((d) => {
                if (d.isolated) return 1.0;
                return d.visible ? 0.1 : 0.8;
            })
        )
        .force(
            "collision",
            d3.forceCollide((d) => {
                if (d.isolated) return nodeRadius + 2;
                return d.visible ? nodeRadius + 8 : nodeRadius + 1;
            })
        )
        .force("sameLayerRepulsion", () => {
            nodes.forEach((nodeA) => {
                if (!nodeA.visible || nodeA.isolated) return;

                nodes.forEach((nodeB) => {
                    if (
                        !nodeB.visible ||
                        nodeB.isolated ||
                        nodeA === nodeB ||
                        nodeA.group !== nodeB.group
                    )
                        return;

                    const dx = nodeB.x - nodeA.x;
                    const dy = nodeB.y - nodeA.y;
                    const distance = Math.sqrt(dx * dx + dy * dy);

                    if (distance < 150) {
                        const force = ((150 - distance) / distance) * 0.3;
                        const fx = dx * force;
                        const fy = dy * force;

                        nodeA.vx -= fx;
                        nodeA.vy -= fy;
                        nodeB.vx += fx;
                        nodeB.vy += fy;
                    }
                });
            });
        })
        .on("tick", drawNetwork);

    simulation.alpha(0.8).restart();
};

const drawNetwork = () => {
    context.save();
    context.clearRect(0, 0, width, height);
    context.translate(transform.x, transform.y);
    context.scale(transform.k, transform.k);

    context.beginPath();
    context.strokeStyle = "#999";
    context.lineWidth = 1.5;
    links.forEach((link) => {
        if (link.source.visible && link.target.visible) {
            context.moveTo(link.source.x, link.source.y);
            context.lineTo(link.target.x, link.target.y);
        }
    });
    context.stroke();

    context.fillStyle = "#666";
    links.forEach((link) => {
        if (link.source.visible && link.target.visible) {
            drawArrowhead(context, link.source, link.target);
        }
    });

    nodes.forEach((node) => {
        context.beginPath();
        context.arc(node.x, node.y, nodeRadius, 0, 2 * Math.PI);

        if (node.visible && !node.isolated) {
            context.fillStyle = getNodeColor(node.group);
            context.globalAlpha = 1.0;
        } else if (node.isolated) {
            context.fillStyle = "#888";
            context.globalAlpha = node.visible ? 0.8 : 0.6;
        } else {
            context.fillStyle = getNodeColor(node.group);
            context.globalAlpha = 0.7;
        }

        context.fill();
        context.strokeStyle = node.visible ? "#333" : "#555";
        context.lineWidth = node.visible ? 2 : 1.5;
        context.stroke();

        context.globalAlpha = node.visible ? 1.0 : 0.8;
        context.fillStyle = "#333";
        context.font = "11px Arial";
        context.textAlign = "center";
        context.fillText(node.id, node.x, node.y - nodeRadius - 5);
    });

    context.globalAlpha = 1.0;
    context.restore();
};

const drawArrowhead = (context, source, target) => {
    const dx = target.x - source.x;
    const dy = target.y - source.y;
    const angle = Math.atan2(dy, dx);
    const length = Math.sqrt(dx * dx + dy * dy);

    const arrowX = target.x - (dx * nodeRadius) / length;
    const arrowY = target.y - (dy * nodeRadius) / length;

    const arrowLength = 10;
    const arrowWidth = 0.4;

    context.beginPath();
    context.moveTo(arrowX, arrowY);

    if (networkData.is_forward) {
        context.lineTo(
            arrowX - arrowLength * Math.cos(angle - arrowWidth),
            arrowY - arrowLength * Math.sin(angle - arrowWidth)
        );
        context.lineTo(
            arrowX - arrowLength * Math.cos(angle + arrowWidth),
            arrowY - arrowLength * Math.sin(angle + arrowWidth)
        );
    } else {
        context.lineTo(
            arrowX - arrowLength * Math.cos(angle - arrowWidth),
            arrowY - arrowLength * Math.sin(angle - arrowWidth)
        );
        context.lineTo(
            arrowX - arrowLength * Math.cos(angle + arrowWidth),
            arrowY - arrowLength * Math.sin(angle + arrowWidth)
        );
    }

    context.closePath();
    context.fill();
};

const getNodeColor = (group) => {
    const colors = [
        "#ff6b6b",
        "#4ecdc4",
        "#45b7d1",
        "#96ceb4",
        "#feca57",
        "#ff9ff3",
        "#54a0ff",
    ];
    return colors[group % colors.length];
};

const stepForward = () => {
    if (isLoad) {
        loadData();
        isLoad = false;
    }

    if (visibleLayers < maxLayers) {
        visibleLayers++;

        createNetwork();
        updateButtons();
    }
};

const stepBack = () => {
    if (isLoad) {
        loadData();
        isLoad = false;
    }

    if (visibleLayers >= 0) {
        visibleLayers--;

        createNetwork();
        updateButtons();
    }
};

const updateButtons = () => {
    document.getElementById("prev").disabled = visibleLayers < 0;
    document.getElementById("next").disabled =
        visibleLayers >= maxLayers || !networkData;
};

const showNodeDetails = (node) => {
    const detailsDiv = document.getElementById("nodeDetails");
    const preconditions = node.precondition
        ? node.precondition.join(", ")
        : "None";
    const effects = node.effect ? node.effect.join(", ") : "None";

    detailsDiv.innerHTML = `
                <h4>${node.id}</h4>
                <p><strong>Preconditions:</strong><br>${preconditions}</p>
                <p><strong>Effects:</strong><br>${effects || "None"}</p>
            `;
};

const load = () => {
    init();
    updateButtons();
    loadData();
    isLoad = false;
};
