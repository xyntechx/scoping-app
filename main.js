// Global variables
let simulation;
let canvas, context;
let networkData = null;
let visibleLayers = -1;
let maxLayers = 0;
let nodes = [];
let links = [];
let transform = d3.zoomIdentity;

const width = 1000;
const height = 600;
const nodeRadius = 6;
const leftClusterX = 80; // Position for invisible nodes to cluster

// Initialize
function init() {
    canvas = d3.select("#networkCanvas");
    context = canvas.node().getContext("2d");

    // Setup zoom and drag
    canvas.call(d3.zoom().scaleExtent([0.1, 4]).on("zoom", zoomed));

    canvas.on("click", handleCanvasClick);
}

function zoomed(event) {
    transform = event.transform;
    drawNetwork();
}

function handleCanvasClick(event) {
    const [mouseX, mouseY] = d3.pointer(event);
    const [x, y] = transform.invert([mouseX, mouseY]);

    // Find clicked node (both visible and invisible nodes are clickable)
    const clickedNode = nodes.find((node) => {
        const dx = x - node.x;
        const dy = y - node.y;
        return Math.sqrt(dx * dx + dy * dy) < nodeRadius + 5;
    });

    if (clickedNode) {
        showNodeDetails(clickedNode);
    }
}

// Helper function to check if a node has any connections
function hasConnections(nodeId, links) {
    return links.some(
        (link) =>
            link.source === nodeId ||
            link.target === nodeId ||
            (typeof link.source === "object" && link.source.id === nodeId) ||
            (typeof link.target === "object" && link.target.id === nodeId)
    );
}

function loadData() {
    networkData = JSON.parse(window.localStorage.getItem("scoping_data"));

    maxLayers = Math.max(...networkData.nodes.map((n) => n.group));
    visibleLayers = -1;

    // Reset nodes array to trigger initialization
    nodes = [];

    updateButtons();
    updateLayerStatus();

    // Initialize the network
    createNetwork();
}

function createNetwork() {
    if (!networkData) return;

    // If this is the first time, initialize nodes with positions
    if (nodes.length === 0) {
        nodes = networkData.nodes.map((d, index) => {
            // Check if this node has any connections
            const isIsolated = !hasConnections(d.id, networkData.links);

            // Start all nodes in the left cluster
            return {
                ...d,
                x: leftClusterX + (Math.random() - 0.5) * 60,
                y: height / 2 + (Math.random() - 0.5) * height * 0.6,
                visible: d.group <= visibleLayers,
                isolated: isIsolated, // Mark nodes that have no connections
            };
        });
    } else {
        // Update visibility status for existing nodes
        nodes.forEach((node) => {
            node.visible = node.group <= visibleLayers;
            // Update isolation status in case data changed
            node.isolated = !hasConnections(node.id, networkData.links);
        });
    }

    // Create links between all nodes (including invisible ones)
    links = networkData.links.map((d) => ({
        source: nodes.find((n) => n.id === d.source),
        target: nodes.find((n) => n.id === d.target),
    }));

    // Create simulation with all nodes
    if (simulation) simulation.stop();

    simulation = d3
        .forceSimulation(nodes)
        .force(
            "link",
            d3
                .forceLink(links)
                .id((d) => d.id)
                .strength((d) => {
                    // Weaker links for invisible nodes
                    return d.source.visible && d.target.visible ? 0.6 : 0.1;
                })
                .distance((d) => {
                    // Shorter distances for invisible nodes
                    return d.source.visible && d.target.visible ? 80 : 20;
                })
        )
        .force(
            "charge",
            d3.forceManyBody().strength((d) => {
                // Weaker repulsion for invisible or isolated nodes
                return d.visible && !d.isolated ? -200 : -50;
            })
        )
        .force(
            "x",
            d3
                .forceX((d) => {
                    // Isolated nodes stay on the left regardless of visibility
                    if (d.isolated || !d.visible) {
                        return leftClusterX;
                    } else {
                        // Visible connected nodes: positioned based on layer (right to left)
                        return width * (0.9 - (0.8 * d.group) / maxLayers);
                    }
                })
                .strength((d) => {
                    // Strong positioning for isolated nodes to keep them clustered
                    if (d.isolated) return 3.0;
                    return d.visible ? 2.5 : 2.0;
                })
        )
        .force(
            "y",
            d3.forceY(height / 2).strength((d) => {
                // Stronger vertical centering for isolated nodes
                if (d.isolated) return 1.0;
                // Weaker vertical centering for visible connected nodes to allow spreading
                return d.visible ? 0.1 : 0.8;
            })
        )
        .force(
            "collision",
            d3.forceCollide((d) => {
                // Smaller collision radius for isolated nodes to pack them tighter
                if (d.isolated) return nodeRadius + 2;
                // Larger collision radius for connected nodes for better spacing
                return d.visible ? nodeRadius + 8 : nodeRadius + 1;
            })
        )
        .force("sameLayerRepulsion", () => {
            // Custom force for same-layer node repulsion (only for connected nodes)
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
                        // Apply repulsion within 150px
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

    // Restart the simulation with higher alpha for smooth transitions
    simulation.alpha(0.8).restart();
}

function drawNetwork() {
    context.save();
    context.clearRect(0, 0, width, height);
    context.translate(transform.x, transform.y);
    context.scale(transform.k, transform.k);

    // Draw links (only between visible nodes)
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

    // Draw arrowheads (only for visible links)
    context.fillStyle = "#666";
    links.forEach((link) => {
        if (link.source.visible && link.target.visible) {
            drawArrowhead(context, link.source, link.target);
        }
    });

    // Draw all nodes (visible and invisible)
    nodes.forEach((node) => {
        // Node circle
        context.beginPath();
        context.arc(node.x, node.y, nodeRadius, 0, 2 * Math.PI);

        if (node.visible && !node.isolated) {
            // Visible connected nodes: full color and opacity
            context.fillStyle = getNodeColor(node.group);
            context.globalAlpha = 1.0;
        } else if (node.isolated) {
            // Isolated nodes: slightly different styling
            context.fillStyle = "#888"; // Gray color for isolated nodes
            context.globalAlpha = node.visible ? 0.8 : 0.6;
        } else {
            // Invisible nodes: same color but reduced opacity
            context.fillStyle = getNodeColor(node.group);
            context.globalAlpha = 0.7;
        }

        context.fill();
        context.strokeStyle = node.visible ? "#333" : "#555";
        context.lineWidth = node.visible ? 2 : 1.5;
        context.stroke();

        // Node label (for both visible and invisible nodes)
        context.globalAlpha = node.visible ? 1.0 : 0.8;
        context.fillStyle = "#333";
        context.font = "11px Arial";
        context.textAlign = "center";
        context.fillText(node.id, node.x, node.y - nodeRadius - 5);
    });

    context.globalAlpha = 1.0; // Reset alpha
    context.restore();
}

function drawArrowhead(context, source, target) {
    const dx = target.x - source.x;
    const dy = target.y - source.y;
    const angle = Math.atan2(dy, dx);
    const length = Math.sqrt(dx * dx + dy * dy);

    // Position arrowhead at edge of target node (pointing left)
    const arrowX = target.x - (dx * nodeRadius) / length;
    const arrowY = target.y - (dy * nodeRadius) / length;

    const arrowLength = 10;
    const arrowWidth = 0.4;

    context.beginPath();
    context.moveTo(arrowX, arrowY);
    context.lineTo(
        arrowX - arrowLength * Math.cos(angle - arrowWidth),
        arrowY - arrowLength * Math.sin(angle - arrowWidth)
    );
    context.lineTo(
        arrowX - arrowLength * Math.cos(angle + arrowWidth),
        arrowY - arrowLength * Math.sin(angle + arrowWidth)
    );
    context.closePath();
    context.fill();
}

function getNodeColor(group) {
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
}

function stepForward() {
    if (visibleLayers < maxLayers) {
        visibleLayers++;

        // Smoothly transition newly visible nodes
        createNetwork();
        updateButtons();
        updateLayerStatus();
    }
}

function stepBack() {
    if (visibleLayers >= 0) {
        visibleLayers--;

        // Smoothly transition nodes back to cluster
        createNetwork();
        updateButtons();
        updateLayerStatus();
    }
}

function updateButtons() {
    document.getElementById("visualize_back").disabled = visibleLayers < 0;
    document.getElementById("visualize").disabled =
        visibleLayers >= maxLayers || !networkData;
}

function updateLayerStatus() {
    const status = document.getElementById("layerStatus");
    if (!networkData) {
        status.textContent = "No data loaded";
        return;
    }

    const visibleNodes = nodes.filter((n) => n.visible).length;
    const totalNodes = nodes.length;
    const isolatedNodes = nodes.filter((n) => n.isolated).length;

    status.innerHTML = `
                <strong>Current Layer:</strong> ${visibleLayers + 1} / ${
        maxLayers + 1
    }<br>
                <p><strong>Visible Nodes:</strong> ${visibleNodes} / ${totalNodes}</p>
                <p><strong>Isolated Nodes:</strong> ${isolatedNodes}</p>
                <p><strong>Direction:</strong> ${
                    networkData.is_forward ? "Forward" : "Backward"
                }</p>
            `;
}

function showNodeDetails(node) {
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
}

const load = () => {
    init();
    updateButtons();
    loadData();
};
