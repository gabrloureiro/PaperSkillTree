
function getLayoutedElements(nodes, edges) {
  const adj = {};
  const revAdj = {};
  nodes.forEach(n => {
    adj[n.id] = [];
    revAdj[n.id] = [];
  });
  edges.forEach(e => {
    adj[e.source].push(e.target);
    revAdj[e.target].push(e.source);
  });

  const rank = {};
  function getRank(id) {
    if (rank[id] !== undefined) return rank[id];
    if (adj[id].length === 0) return rank[id] = 0;
    let maxChildRank = 0;
    adj[id].forEach(childId => {
      maxChildRank = Math.max(maxChildRank, getRank(childId));
    });
    return rank[id] = 1 + maxChildRank;
  }
  nodes.forEach(n => getRank(n.id));

  // Find all paths
  let allPaths = [];
  function findPaths(u, currentPath) {
    if (adj[u].length === 0) {
      allPaths.push([...currentPath]);
      return;
    }
    // Limit path search if too many?
    if (allPaths.length > 1000) return; 
    adj[u].forEach(v => {
      currentPath.push(v);
      findPaths(v, currentPath);
      currentPath.pop();
    });
  }
  nodes.forEach(n => {
    if (revAdj[n.id].length === 0) findPaths(n.id, [n.id]);
  });
  allPaths.sort((a, b) => b.length - a.length);

  const nodePositions = {}; // id -> {col, row}
  const occupied = new Set(); // "col,row"

  function isOccupied(col, row) {
    return occupied.has(`${col},${row}`);
  }

  function markOccupied(col, row) {
    occupied.add(`${col},${row}`);
  }

  allPaths.forEach(path => {
    // Process path from end to start (sink to source)
    for (let i = path.length - 1; i >= 0; i--) {
      const id = path[i];
      if (nodePositions[id]) continue;

      const col = rank[id];
      // Try to match row of successor if exists
      let preferredRow = 0;
      if (i < path.length - 1) {
        preferredRow = nodePositions[path[i+1]].row;
      }

      let row = preferredRow;
      let found = false;
      // Search: preferredRow, preferredRow+1, preferredRow-1, ...
      for (let offset = 0; offset < 100; offset++) {
        for (let sign of [1, -1]) {
          let r = preferredRow + offset * sign;
          if (offset === 0 && sign === -1) continue;
          if (!isOccupied(col, r)) {
            row = r;
            found = true;
            break;
          }
        }
        if (found) break;
      }

      nodePositions[id] = { col, row };
      markOccupied(col, row);

      // Edge occupancy logic
      if (i < path.length - 1) {
        const nextId = path[i+1];
        const nextPos = nodePositions[nextId];
        // Mark columns between curr col and next col
        // For smoothstep: jump is at midpoint.
        const c1 = col;
        const c2 = nextPos.col;
        const r1 = row;
        const r2 = nextPos.row;
        const mid = Math.floor((c1 + c2) / 2);

        // From c1 to mid+1: row r1
        for (let c = c1 - 1; c > mid; c--) markOccupied(c, r1);
        // At mid: vertical jump r1 to r2
        for (let r = Math.min(r1, r2); r <= Math.max(r1, r2); r++) markOccupied(mid, r);
        // From mid-1 to c2: row r2
        for (let c = mid - 1; c > c2; c--) markOccupied(c, r2);
      }
    }
  });

  // Convert to return format
  const maxRank = Math.max(...Object.values(rank), 0);
  return nodes.map(n => ({
    ...n,
    position: {
      x: (maxRank - nodePositions[n.id].col) * 300,
      y: nodePositions[n.id].row * 150
    }
  }));
}
