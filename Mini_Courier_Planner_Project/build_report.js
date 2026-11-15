// Builds Mini_Courier_Planner_Report.docx from real measured data (outputs/report_data.json)
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun, HeadingLevel,
  AlignmentType, WidthType, BorderStyle, ShadingType, LevelFormat, PageBreak, Footer, PageNumber,
  TableOfContents,
} = require("docx");

const D = JSON.parse(fs.readFileSync("outputs/report_data.json", "utf8"));
const FONT = "Arial", W = 9638; // content width (A4, 2 cm margins)
const NAVY = "1F4E79";

const run = (t, o = {}) => new TextRun({ text: t, font: FONT, size: 21, ...o });
const P = (t, o = {}) => new Paragraph({ spacing: { after: 120, line: 276 },
  alignment: o.align, children: Array.isArray(t) ? t : [run(t, o.run || {})], ...(o.p || {}) });
const B = (t) => new Paragraph({ numbering: { reference: "bul", level: 0 }, spacing: { after: 60 },
  children: Array.isArray(t) ? t : [run(t)] });
const N = (t) => new Paragraph({ numbering: { reference: "num", level: 0 }, spacing: { after: 60 },
  children: Array.isArray(t) ? t : [run(t)] });
const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun({ text: t, font: FONT })] });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun({ text: t, font: FONT })] });
const bold = (t) => run(t, { bold: true });
const mono = (t) => new Paragraph({ spacing: { after: 0 }, shading: { type: ShadingType.CLEAR, fill: "F2F2F2" },
  children: [new TextRun({ text: t, font: "Courier New", size: 18 })] });
const code = (lines) => lines.map(mono);
const gap = () => new Paragraph({ spacing: { after: 80 }, children: [] });

const border = { style: BorderStyle.SINGLE, size: 4, color: "BBBBBB" };
const borders = { top: border, bottom: border, left: border, right: border };
function table(headers, rows, widths, opts = {}) {
  const total = widths.reduce((a, b) => a + b, 0);
  const cell = (txt, w, head, i) => new TableCell({
    width: { size: w, type: WidthType.DXA }, borders,
    shading: head ? { type: ShadingType.CLEAR, fill: NAVY } : (opts.zebra && i % 2 ? { type: ShadingType.CLEAR, fill: "F5F8FB" } : undefined),
    margins: { top: 50, bottom: 50, left: 90, right: 90 },
    children: [new Paragraph({ alignment: opts.center ? AlignmentType.CENTER : AlignmentType.LEFT,
      children: [new TextRun({ text: String(txt), font: FONT, size: opts.size || 18, bold: head,
        color: head ? "FFFFFF" : undefined })] })],
  });
  return new Table({
    width: { size: total, type: WidthType.DXA }, columnWidths: widths,
    rows: [new TableRow({ tableHeader: true, children: headers.map((h, i) => cell(h, widths[i], true, 0)) }),
      ...rows.map((r, ri) => new TableRow({ cantSplit: true, children: r.map((c, i) => cell(c, widths[i], false, ri)) }))],
  });
}
function img(key, widthPx = 620, caption) {
  const [path, w, h] = D.img[key];
  const out = [new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 80, after: 40 }, keepNext: !!caption,
    children: [new ImageRun({ type: "png", data: fs.readFileSync(path),
      transformation: { width: widthPx, height: Math.round(widthPx * h / w) },
      altText: { title: key, description: caption || key, name: key } })] })];
  if (caption) out.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 160 },
    children: [run(caption, { italics: true, size: 18, color: "555555" })] }));
  return out;
}
const f = (x, d = 2) => Number(x).toFixed(d);

// ---------- derived tables ----------
const sizesS = [...new Set(D.sorting.map(r => r.n))];
const sortTbl = sizesS.map(n => {
  const g = a => { const r = D.sorting.find(x => x.n === n && x.algorithm === a); return r ? f(r.ms, 2) : "—"; };
  return [n, g("merge"), g("quick"), g("heap"), g("insertion"), g("timsort")];
});
const pats = ["random", "already sorted", "reverse sorted"];
const patTbl = ["merge", "quick", "heap", "insertion", "timsort"].map(a =>
  [a, ...pats.map(p => f(D.patterns.find(x => x.algorithm === a && x.input === p).ms, 2))]);
const pipe = D.pipe;
const pipeTbl = pipe.map(r => [r.dataset, r.nodes, r.parcels, r.capacity_kg, r.parcels_loaded, r.stops,
  f(r.route_km, 1), f(r.trip_total_ms, 3), r.trips_for_all_parcels]);
const stepTbl = pipe.map(r => [r.dataset, f(r.sort_ms, 3), f(r.knapsack_ms, 3), f(r.dijkstra_ms, 3), f(r.tsp_nn_ms, 3), f(r.two_opt_ms, 3)]);
const tspTbl = D.tsp.map(r => [r.k_stops, f((r.nn_avg_ratio - 1) * 100, 1) + " %", f((r.nn_max_ratio - 1) * 100, 1) + " %",
  f((r["2opt_avg_ratio"] - 1) * 100, 2) + " %", f((r["2opt_max_ratio"] - 1) * 100, 1) + " %"]);
const gfn = (s, n) => D.graph.find(x => x.step === s && x.size === String(n));
const share = r => { const t = +r.sort_ms + +r.knapsack_ms + +r.dijkstra_ms + +r.tsp_nn_ms + +r.two_opt_ms;
  return { k: (100 * r.knapsack_ms / t).toFixed(0), d: (100 * r.dijkstra_ms / t).toFixed(0), s: (100 * r.sort_ms / t).toFixed(0) }; };
const shL = share(pipe[2]);
const bf20 = D.kn_bf[D.kn_bf.length - 1];
const REVINS = f(D.patterns.find(x => x.algorithm === 'insertion' && x.input === 'reverse sorted').ms, 0);
const ins5000 = D.sorting.find(x => x.n === "5000" && x.algorithm === "insertion");
const mer5000 = D.sorting.find(x => x.n === "5000" && x.algorithm === "merge");

const kids = [];
const add = (...x) => x.flat().forEach(e => kids.push(e));

// ================= COVER =================
add(
  new Paragraph({ spacing: { before: 1200, after: 120 }, alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "K.R. Mangalam University, Gurugram, Haryana", font: FONT, size: 30, bold: true, color: NAVY })] }),
  new Paragraph({ spacing: { after: 600 }, alignment: AlignmentType.CENTER,
    children: [run("School of Engineering & Technology", { size: 24, color: "555555" })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 120 },
    children: [new TextRun({ text: "CAPSTONE ASSIGNMENT", font: FONT, size: 26, bold: true })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 120 },
    children: [new TextRun({ text: "Mini-Courier Planner", font: FONT, size: 56, bold: true, color: NAVY })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 700 },
    children: [run("Sorting + Dynamic Programming + Dijkstra + TSP Approximation in one Python application", { size: 24, italics: true })] }),
  table(["Item", "Details"], [
    ["Course Title & Code", "Design & Analysis of Algorithms (ETCCDA302)"],
    ["Programme", "B.Tech CSE & Specializations"],
    ["Faculty Name", "Dr. Shweta Agarwal"],
    ["COs covered", "CO1, CO2, CO3, CO4 (Bloom's Level L5 - Create / Evaluate)"],
    ["Assessment type", "Coding-based capstone (100 marks, scaled to 10)"],
    ["Submission mode", "File upload / GitHub repository link (Zosima)"],
    ["Student name", "______________________________"],
    ["Roll number / Section", "______________________________"],
    ["Date of submission", "______________________________"],
  ], [3000, 6638], { size: 20 }),
  new Paragraph({ children: [new PageBreak()] }),
);

// ================= TOC =================
add(H1("Contents"),
  table(["Section", "Title", "Marks"], [
    ["", "Executive Summary and marks map", ""],
    ["1", "Phase 1 - Courier Problem Design and Planning", "20"],
    ["2", "Phase 2 - Package Prioritisation and Box Filling", "20"],
    ["3", "Phase 3 - Route Maker and Graph Processing", "20"],
    ["4", "Phase 4 - Performance Testing and Optimization", "20"],
    ["5", "Phase 5 - Final Report and Demonstration (results, structure, how to run, limitations)", "20"],
    ["A", "Appendix A - Complexity summary", ""],
    ["B", "Appendix B - Viva preparation (questions and short answers)", ""],
  ], [1200, 7238, 1200], { zebra: true, size: 20 }),
  new Paragraph({ children: [new PageBreak()] }));

// ================= 0. SUMMARY =================
add(H1("Executive Summary"),
  P("The Mini-Courier Planner is an integrated Python prototype that, given a list of parcels and a road network of delivery points, " +
    "decides (1) in which order parcels are handled, (2) which parcels fit in one van trip, (3) the real shortest road distance between every " +
    "pair of stops, and (4) the order in which the stops are visited. Each decision is made by one of the algorithms from the first four lab " +
    "assessments, and the runtime of every component is measured on small, medium and large datasets."),
  table(["Stage", "Algorithm used", "Complexity", "Result on the small sample"], [
    ["Prioritise parcels", "Merge sort (stable)", "O(n log n)", "P01, P05, P03, P10, P08, P06, P02, P04, P09, P07"],
    ["Fill the van", "0/1 Knapsack - Dynamic Programming", "O(n·W)", `${D.loaded.length} parcels, value ${D.best_value}, ${D.weight}/25 kg`],
    ["Shortest paths", "Dijkstra with a binary heap", "O((V+E) log V) per source", "Depot → each stop distances and paths"],
    ["Visiting order", "Nearest-neighbour TSP (+ 2-opt)", "O(k²)", `${D.tour.join(" → ")}, ${D.km} km`],
  ], [1800, 2600, 1900, 3338], { zebra: true }),
  gap(),
  P([bold("Headline results. "), run(
    `On the 1,000-parcel dataset one trip is planned in about ${f(pipe[2].trip_total_ms, 1)} ms and all 27 trips in about ${f(pipe[2].all_trips_ms, 0)} ms. ` +
    `Dynamic programming found the optimum in 200/200 random checks against brute force, Dijkstra matched Floyd-Warshall on 40/40 random graphs, ` +
    `and the nearest-neighbour route was on average only 4.7 % longer than the exact optimum (2-opt reduced this to under 0.5 %).`)]),
  H2("Marks map: where to find the evidence"),
  table(["Phase", "Marks", "Where in this report", "Where in the code / outputs"], [
    ["1  Design and Planning", "20", "Section 1", "courier/models.py, data/*.json, outputs/charts/design_flow.png"],
    ["2  Prioritisation and Box Filling", "20", "Section 2", "courier/sorting.py, courier/knapsack.py, screenshots 01-02"],
    ["3  Route Maker and Graph Processing", "20", "Section 3", "courier/graph.py, screenshot 03, route maps"],
    ["4  Performance Testing", "20", "Section 4", "run_benchmarks.py, outputs/*.csv, outputs/charts/*"],
    ["5  Report and Demonstration", "20", "Sections 5-6, Appendix", "this report, README.md, main.py, screenshots 04-07"],
  ], [2900, 800, 2100, 3838], { zebra: true }),
  new Paragraph({ children: [new PageBreak()] }));

// ================= PHASE 1 =================
add(H1("1. Phase 1 - Courier Problem Design and Planning"),
  H2("1.1 Problem definition"),
  P("A courier depot owns one van with a limited load capacity. Every morning it holds more parcels than the van can carry. " +
    "The planner must answer four connected questions:"),
  N("Which parcels should be handled first? (deadlines and priorities)"),
  N("Which subset of parcels should be loaded in this trip so that the most valuable parcels are delivered without exceeding the van capacity?"),
  N("How far apart are the customers on the real road network? (the roads are sparse, so two customers are rarely joined directly)"),
  N("In which order should the customers of this trip be visited so that the van returns to the depot after the shortest possible drive?"),
  P("Parcels that do not fit are left for the next trip, and the process repeats until nothing deliverable remains."),
  H2("1.2 Assumptions"),
  B("One van, capacity W kg (integer). Parcel weights are integer kilograms so they can index the DP table."),
  B("The road network is undirected with non-negative distances in km (required by Dijkstra)."),
  B("The van starts and ends every trip at the depot (node 0), drives at a constant 40 km/h and spends 5 minutes at every stop."),
  B("A parcel is delivered at its destination node; several parcels may share one destination (they cost one stop)."),
  B("A parcel is either loaded completely or not at all (0/1 knapsack - parcels cannot be split)."),
  H2("1.3 Data design"),
  P([bold("Parcel attributes. "), run("These are stored in an immutable dataclass (courier/models.py).")]),
  table(["Attribute", "Type", "Meaning"], [
    ["pid", "string", "Unique parcel id, e.g. P01 (also the final sorting tie-breaker)"],
    ["weight", "int (kg)", "Knapsack weight"],
    ["priority", "int 1-5", "5 = most important customer / service level"],
    ["deadline_h", "float (hours)", "Latest acceptable delivery time after the van leaves"],
    ["destination", "int", "Node id of the customer in the road graph"],
    ["value (derived)", "int", "10 × priority + (24 − deadline_h) if deadline < 24 h → knapsack profit. An important and urgent parcel is the most valuable to load."],
  ], [1900, 1600, 6138], { zebra: true }),
  gap(),
  P([bold("Graph format. "), run("The road network is an undirected weighted graph stored as an adjacency list " +
    "{node: [(neighbour, distance_km), …]}. An adjacency list needs O(V+E) memory, which suits sparse road maps, and lets Dijkstra scan the " +
    "neighbours of a node in time proportional to its degree. Dataset files are JSON with the keys nodes, edges, parcels and vehicle settings; " +
    "CSV copies of the parcel and edge lists are provided for easy viewing.")]),
  table(["Dataset file", "Nodes", "Roads", "Parcels", "Capacity", "Purpose"], [
    ["data/small.json", "8", "13", "10", "25 kg", "Hand-made (Gurugram place names) - can be traced by hand in the viva"],
    ["data/medium.json", "30", "59", "100", "100 kg", "Generated, seed 11 - moderate size, 8 trips"],
    ["data/large.json", "120", "230", "1,000", "300 kg", "Generated, seed 21 - stress test, 27 trips"],
  ], [2200, 800, 800, 900, 1000, 3938], { zebra: true }),
  H2("1.4 Algorithm selection and justification"),
  table(["Task", "Chosen", "Alternatives considered", "Why chosen"], [
    ["Prioritise parcels", "Merge sort", "Quick, heap, insertion sort", "Guaranteed O(n log n) for every input, stable, easy to trace. Quick sort has an O(n²) worst case, heap sort is not stable, insertion sort is O(n²)."],
    ["Select parcels for a trip", "0/1 Knapsack DP", "Greedy by value/weight, brute force", "Greedy is fast but not optimal (it lost to DP on 49 of 200 random instances); brute force is O(2ⁿ). DP is exact in O(nW)."],
    ["Distances between stops", "Dijkstra (heap)", "Bellman-Ford, Floyd-Warshall", "All weights are non-negative, so Dijkstra is the fastest; Floyd-Warshall is O(V³) and computes pairs we never need."],
    ["Visiting order", "Nearest neighbour (+ 2-opt)", "Brute force, Held-Karp DP", "TSP is NP-hard. Exact methods explode beyond ~12 stops; nearest neighbour is O(k²) and, measured here, within a few percent of optimal."],
  ], [1700, 1500, 2100, 4338], { zebra: true, size: 17 }),
  H2("1.5 How the algorithms work together"),
  ...img("design_flow", 640, "Figure 1 - System design: data flow between the algorithms"),
  P("The sorted list is the input order of the knapsack, so when several optimal packings exist, the trace-back keeps the earlier (more urgent) parcels. " +
    "The knapsack output decides the set of stops, Dijkstra turns that set into a distance table, and the TSP heuristic turns the table into a visiting order " +
    "that is finally expanded into the real road path and checked against the deadlines. Left-over parcels re-enter the pipeline for the next trip."),
  H2("1.6 Route-planning logic (pseudocode)"),
  ...code([
    "plan_trip(problem, parcels):",
    "    ordered  = merge_sort(parcels, key = (deadline, -priority, id))",
    "    chosen   = knapsack_dp(weights(ordered), values(ordered), capacity)",
    "    stops    = unique destinations of chosen parcels",
    "    dist     = { s : dijkstra(graph, s) for s in [depot] + stops }",
    "    tour     = nearest_neighbour(dist, depot, stops)      # depot ... depot",
    "    tour     = two_opt(tour, dist)                        # optional",
    "    route    = replace each leg by its Dijkstra road path",
    "    schedule = arrival time = distance / speed + service time per stop",
    "    return chosen, tour, route, schedule",
  ]),
  new Paragraph({ children: [new PageBreak()] }));

// ================= PHASE 2 =================
add(H1("2. Phase 2 - Package Prioritisation and Box Filling"),
  H2("2.1 Sorting parcels (merge sort)"),
  P("Parcels are ordered by earliest deadline first; for equal deadlines the higher priority comes first; the parcel id breaks remaining ties. " +
    "The key is the tuple (deadline_h, −priority, pid). Merge sort splits the list in halves, sorts each half recursively and merges them in linear time. " +
    "The recurrence T(n) = 2T(n/2) + O(n) gives O(n log n) in the best, average and worst case, using O(n) extra space. The merge uses a strict “<” " +
    "so equal keys keep their original order (stability)."),
  P([bold("Result on the small dataset"), run(" (10 parcels, capacity 25 kg):")]),
  table(["#", "Parcel", "kg", "Priority", "Deadline (h)", "Dest.", "Value"],
    D.sorted.map(r => r.map(String)), [600, 1200, 800, 1300, 1700, 1000, 1000], { center: true, zebra: true }),
  gap(),
  P("P01 and P05 share the 2-hour deadline and the same priority 5, so the id decides. P03 and P10 share deadline 3 h and priority 4, again ordered by id. " +
    "The output equals Python's built-in sorted() on 200 of 200 random lists for every one of the five implemented sorters (see Section 4.4)."),
  ...img("01_phase2_sorting", 600, "Screenshot 1 - Console output of the sorting step (python main.py)"),
  H2("2.2 Choosing the parcels for one trip (0/1 knapsack, dynamic programming)"),
  P([bold("Definition. "), run("Let weight wᵢ = parcel kg, value vᵢ = priority-and-urgency score, capacity W = 25 kg. "),
    run("T[i][w] is the best total value obtainable from the first i parcels (in priority order) with capacity w:")]),
  ...code([
    "T[0][w] = 0                                         for every w",
    "T[i][w] = T[i-1][w]                                 if w_i > w   (parcel i does not fit)",
    "T[i][w] = max( T[i-1][w],  T[i-1][w - w_i] + v_i )  otherwise    (skip it / load it)",
  ]),
  gap(),
  P("The answer is T[n][W]. To find which parcels were loaded the program walks backwards from T[n][W]: if T[i][w] ≠ T[i-1][w] then parcel i was loaded " +
    "and w decreases by wᵢ. Time is O(n·W) = 10 × 25 = 250 cell updates here; memory is O(n·W) for the table (a one-row O(W) version is also provided " +
    "for when only the value is needed)."),
  ...img("02_phase2_knapsack_dp_table", 640, "Screenshot 2 - Complete DP table T[i][w] and the packing plan"),
  P([bold("Packing plan. "), run(`The optimum value is ${D.best_value}, loading ${D.loaded.join(", ")} (${D.weight} kg of 25 kg, van completely full). ` +
    `Parcels ${D.left.join(", ")} wait for the next trip. All five parcels with deadlines ≤ 4 h are loaded; the 9 kg, 10-hour parcel P07 is left behind, which is the intended behaviour.`)]),
  P([bold("Why DP and not greedy? "), run("A greedy rule (best value per kg first) can fill the van with light parcels and waste capacity. On 200 random instances it was strictly worse than DP on 49 of them, whereas DP matched exhaustive search on all 200.")]),
  new Paragraph({ children: [new PageBreak()] }));

// ================= PHASE 3 =================
add(H1("3. Phase 3 - Route Maker and Graph Processing"),
  H2("3.1 Customer graph"),
  P("The small dataset has 8 nodes (depot + 7 customer areas) and 13 undirected roads. It is sparse on purpose: for example the depot has no direct road to " +
    "Cyber Hub (node 3), so the program must discover that the shortest way is 0 → 2 → 3. Edge lists are in data/small_edges.csv."),
  H2("3.2 Dijkstra's algorithm - individual shortest paths"),
  P("Dijkstra keeps a tentative distance for every node, repeatedly settles the nearest unsettled node (taken from a binary min-heap) and relaxes its outgoing edges. " +
    "Stale heap entries are skipped (lazy deletion). A predecessor array allows the real path to be rebuilt. Complexity: O((V+E) log V) per source. " +
    "Negative weights are rejected when an edge is added, because Dijkstra is not correct for them."),
  P([bold("Shortest paths from the depot to the stops of this trip:")]),
  table(["Stop", "Customer", "Distance (km)", "Shortest path"],
    D.dijkstra.map(r => [r[0], r[1], f(r[2], 1), r[3]]), [900, 2800, 1700, 4238], { center: false, zebra: true }),
  gap(),
  P("Dijkstra is then run from every stop, which produces the complete stop-to-stop distance table used by the route heuristic. " +
    "Unreachable stops are detected and reported as a disconnected graph."),
  H2("3.3 Nearest-neighbour TSP approximation - overall route"),
  P("Starting at the depot, the van always drives to the closest unvisited stop (using the Dijkstra distances; ties go to the smaller node id) and finally returns to the depot. " +
    "This needs O(k²) time for k stops and runs in a fraction of a millisecond on the sample. The optional 2-opt step reverses any segment of the tour whose reversal shortens it."),
  table(["Quantity", "Value"], [
    ["Stop order", D.tour.join(" → ")],
    ["Real road route", D.route.join(" → ")],
    ["Route length", `${f(D.km, 1)} km`],
    ["Driving + service time", `${f(D.hours, 2)} h`],
    ["Exact optimum (Held-Karp)", "37.0 km  (the heuristic route is optimal here)"],
  ], [3000, 6638], { zebra: true }),
  gap(),
  P("The road route passes through nodes 5 and 3 twice because the shortest way back from MG Road (node 6) to the depot is 6 → 5 → 3 → 2 → 0 (18 km); this repeated passing is a property of the sparse road graph, not an error."),
  P([bold("Delivery schedule and deadline check:")]),
  table(["Node", "Customer", "Arrival (h)", "Earliest deadline (h)", "Status", "Parcels"],
    D.deliveries.map(r => [r[0], r[1], f(r[2], 2), f(r[3], 1), r[4], r[5]]), [800, 2300, 1300, 2000, 1100, 2138], { zebra: true }),
  ...img("03_phase3_dijkstra_route", 640, "Screenshot 3 - Dijkstra output and final route sequence"),
  ...img("route_small", 520, "Figure 2 - Route map of the small dataset (blue square = depot, green = delivery stops, red arrows = driven route)"),
  new Paragraph({ children: [new PageBreak()] }));

// ================= PHASE 4 =================
add(H1("4. Phase 4 - Performance Testing and Optimization"),
  H2("4.1 Test method"),
  P("All timings use Python's time.perf_counter(), garbage collection disabled while timing, and the best of at least five repetitions (the usual timeit convention, which removes operating-system noise). " +
    "Inputs are reproducible (fixed random seeds). Absolute milliseconds depend on the computer; the growth trend is what matters."),
  H2("4.2 Test cases"),
  table(["Dataset", "Nodes", "Parcels", "Capacity (kg)", "Loaded", "Stops", "Route (km)", "One trip (ms)", "Trips for all parcels"],
    pipeTbl, [1100, 800, 900, 1100, 900, 800, 1100, 1300, 1638], { center: true, zebra: true, size: 17 }),
  gap(),
  H2("4.3 Runtime of the major steps"),
  table(["Dataset", "Merge sort (ms)", "Knapsack DP (ms)", "Dijkstra all stops (ms)", "Nearest neighbour (ms)", "2-opt (ms)"],
    stepTbl, [1300, 1500, 1600, 1900, 1900, 1438], { center: true, zebra: true }),
  ...img("pipeline_steps", 560, "Figure 3 - Runtime of each major step on the three datasets (log scale)"),
  ...img("pipeline_share", 560, "Figure 4 - Share of the total planning time by step"),
  P([bold("Findings. "), run(`On the large dataset the knapsack DP takes about ${shL.k} % of the trip-planning time and Dijkstra about ${shL.d} %, ` +
    `while sorting takes only ${shL.s} %. The nearest-neighbour step is negligible (under 1 ms). Every step grows smoothly from the small to the large input, as predicted by its complexity.`)]),

  H2("4.4 Algorithm-level comparisons"),
  P([bold("(a) Sorting algorithms"), run(" - time in ms, random input:")]),
  table(["n", "Merge", "Quick", "Heap", "Insertion", "Timsort (built-in)"], sortTbl, [1300, 1600, 1600, 1600, 1800, 1738], { center: true, zebra: true }),
  ...img("sorting_runtime", 520, "Figure 5 - Sorting runtime versus n (log-log). Insertion sort bends away upwards (quadratic)."),
  P(`At n = 5,000 insertion sort needs ${f(ins5000.ms, 0)} ms against ${f(mer5000.ms, 1)} ms for merge sort - about ${f(ins5000.ms / mer5000.ms, 0)} times slower - and the gap widens as n grows. ` +
    "Merge, quick and heap sort are close (all Θ(n log n)); merge sort is chosen because it is stable and has no bad input. The built-in Timsort is fastest only because it is written in C; it is shown as a reference."),
  P([bold("Effect of the input order at n = 2,000"), run(" (ms):")]),
  table(["Algorithm", "Random", "Already sorted", "Reverse sorted"], patTbl, [2600, 2300, 2400, 2338], { center: true, zebra: true }),
  gap(),
  P(`Insertion sort is excellent on sorted input (O(n)) but ${REVINS} ms on reverse-sorted data (O(n²)). Merge sort's time barely changes with the input order - the predictability that justifies choosing it.`),
  P([bold("(b) Knapsack - dynamic programming vs brute force")]),
  table(["Parcels n", "Capacity W", "DP (ms)", "Brute force (ms)"], D.kn_bf.map(r => [r.n, r.capacity, f(r.dp_ms, 3), f(r.bruteforce_ms, 2)]),
    [2000, 2200, 2400, 3038], { center: true, zebra: true }),
  ...img("knapsack_dp_vs_bruteforce", 480, "Figure 6 - DP versus brute force (log scale on the time axis)"),
  P(`Brute force doubles roughly every time n grows by one; at n = 20 it needs ${f(bf20.bruteforce_ms, 0)} ms while DP needs ${f(bf20.dp_ms, 3)} ms. ` +
    "For the 1,000-parcel dataset brute force would be impossible (2¹⁰⁰⁰ subsets), but DP finishes in about 15 ms."),
  ...img("knapsack_scaling", 460, "Figure 7 - DP time grows linearly with n for a fixed capacity (O(n·W)); the 1-D version is roughly 30-45 % faster"),
  P([bold("(c) Graph processing")]),
  ...img("dijkstra_runtime", 440, "Figure 8 - Dijkstra, one source: time grows almost linearly with the number of nodes"),
  ...img("route_steps_runtime", 460, "Figure 9 - Route construction versus number of stops k on a 400-node graph"),
  P(`Running Dijkstra from every stop (k runs) dominates route construction: ${f(gfn("dijkstra_from_all_stops", 160).ms, 1)} ms for 160 stops against ${f(gfn("nearest_neighbour", 160).ms, 2)} ms for nearest neighbour and ${f(gfn("two_opt", 160).ms, 1)} ms for 2-opt. ` +
    "Nearest neighbour is quadratic in k but its constant is tiny."),
  P([bold("(d) Quality of the TSP approximation"), run(" - difference from the exact optimum (Held-Karp), 25 random instances per k:")]),
  table(["Stops k", "NN average", "NN worst", "NN + 2-opt average", "NN + 2-opt worst"], tspTbl, [1400, 2000, 2000, 2200, 2038], { center: true, zebra: true }),
  ...img("tsp_quality", 480, "Figure 10 - Average tour length relative to the optimum (1.0 = optimal)"),
  P("Nearest neighbour is typically 3-9 % above optimal (worst observed 35 %); adding 2-opt brings the average to under 0.5 % at the cost of a little time."),
  ...img("route_medium", 520, "Figure 11 - First trip of the medium dataset after 2-opt (17 stops, 666.8 km)"),
  H2("4.5 Correctness evidence"),
  ...D.correct.slice(2).map(l => mono(l)),
  gap(),
  P("The 16 unit tests (python -m unittest discover -s tests -v) also cover edge cases: empty and one-element lists, stability, zero capacity, parcels heavier than the van, negative edge weights, " +
    "disconnected graphs, and a complete known-answer test of the small dataset."),
  ...img("07_correctness_and_runtime", 620, "Screenshot 7 - Correctness report and pipeline runtime summary"),
  ...img("06_unit_tests", 600, "Screenshot 6 - Unit test run (all tests pass)"),
  H2("4.6 Optimization suggestions for future work"),
  table(["Observed bottleneck", "Suggested improvement", "Expected benefit"], [
    ["Knapsack DP is the biggest step on the large dataset (~63 %)", "Use the 1-D table when only the value is needed, or NumPy vectorised rows; for very large W use FPTAS scaling or branch-and-bound.", "1-D version already measured 30-45 % faster; NumPy gives order-of-magnitude gains."],
    ["Dijkstra is run once per stop (k runs)", "Run Dijkstra only from stops not yet cached across trips; use A* or bidirectional search; or precompute all-pairs once per day and reuse for every trip.", "Removes repeated work across the 27 trips of the large dataset."],
    ["Nearest neighbour is sometimes 20-35 % off optimal", "Always apply 2-opt / Or-opt, or use Christofides (1.5-approximation) when a guarantee is needed.", "Measured: average error drops from ~5 % to < 0.5 %."],
    ["Routing ignores deadlines (it only checks them afterwards)", "Deadline-aware insertion heuristic or time-window TSP; visit stops with the tightest deadline first.", "Guarantees on-time delivery for urgent parcels."],
    ["Single vehicle, one trip at a time", "Multi-vehicle assignment (vehicle routing problem), cluster stops by area with k-means before routing.", "Shorter total distance and faster completion."],
    ["Pure-Python implementation", "Move hot loops to NumPy/Cython or reimplement in C++.", "10-100× faster for the 1,000+ parcel cases."],
  ], [2800, 4000, 2838], { zebra: true, size: 17 }),
  new Paragraph({ children: [new PageBreak()] }));

// ================= PHASE 5 =================
add(H1("5. Phase 5 - Final Report and Demonstration"),
  H2("5.1 Explanation of the results"),
  B([bold("Prioritisation: "), run("urgent and important parcels (deadline ≤ 4 h) come first in the list, so they receive the best chance of being loaded.")]),
  B([bold("Packing: "), run(`the DP fills the 25 kg van exactly with 6 parcels worth ${D.best_value} points. No other combination of parcels within 25 kg has a higher total (verified by brute force).`)]),
  B([bold("Routing: "), run("the van visits Sector 14 → Cyber Hub → Golf Course Rd → MG Road and returns, 37 km in total, and every parcel arrives before its deadline (4/4 stops on time). Held-Karp confirms that 37 km is the true optimum for these stops.")]),
  B([bold("Scaling: "), run("1,000 parcels on a 120-node network are planned into 27 van trips in about a quarter of a second; one trip takes ~24 ms.")]),
  H2("5.2 Output evidence for medium and large datasets"),
  ...img("04_medium_all_trips", 600, "Screenshot 4 - Medium dataset: all 8 trips planned (python main.py --dataset data/medium.json --all-trips --two-opt)"),
  ...img("05_large_all_trips", 600, "Screenshot 5 - Large dataset: 1,000 parcels in 27 trips"),
  P("Note: the screenshots are rendered directly from the real console output of the commands shown. The raw text of every run is saved in outputs/logs/."),
  H2("5.3 Project structure"),
  ...code([
    "mini_courier_planner/",
    "  main.py                 command-line demo (full trace)",
    "  run_benchmarks.py       Phase 4 runtime tests -> outputs/*.csv, outputs/charts/*.png",
    "  make_screenshots.py     renders console output as screenshots",
    "  generate_data.py        creates the 3 datasets in data/",
    "  courier/                models.py  data_io.py  sorting.py  knapsack.py",
    "                          graph.py  planner.py  generator.py  verification.py  charts.py",
    "  tests/test_all.py       16 unit tests",
    "  data/                   small / medium / large  (.json + .csv)",
    "  outputs/                charts, screenshots, logs, CSV result tables",
    "  Mini_Courier_Planner_Report.docx / .pdf     this report",
  ]),
  gap(),
  H2("5.4 How to run (Python 3.9 or newer)"),
  ...code([
    "pip install -r requirements.txt                  # only matplotlib + Pillow, for charts",
    "python generate_data.py                          # (optional) recreate the datasets",
    "python main.py                                   # small sample, full trace with DP table",
    "python main.py --dataset data/medium.json --all-trips --two-opt",
    "python main.py --dataset data/large.json  --all-trips --two-opt --no-table",
    "python main.py --sorter quick --plot outputs/charts/route.png",
    "python run_benchmarks.py                         # all runtime tests + charts (~1 minute)",
    "python make_screenshots.py                       # console screenshots",
    "python -m unittest discover -s tests -v          # unit tests",
  ]),
  gap(),
  P("To run on an unseen dataset, create a JSON file in the same format as data/small.json and pass it with --dataset."),
  H2("5.5 Limitations"),
  B("Nearest neighbour does not guarantee optimality, and deadlines are checked after routing instead of constrained during routing."),
  B("Knapsack needs integer weights; DP memory is O(n·W), which is large for very big capacities."),
  B("The road network is undirected and static - no traffic, one-way streets or time-dependent travel times."),
  B("Timings come from one machine and one Python interpreter and should be read as trends, not absolute values."),
  H2("5.6 Conclusion"),
  P("The prototype shows how different algorithm-design paradigms cooperate in one system: divide and conquer (merge sort) orders the work, dynamic programming makes an optimal selection, " +
    "a greedy algorithm (Dijkstra) finds exact shortest paths, and a greedy heuristic with local search approximates an NP-hard routing problem. " +
    "The experiments confirm the theoretical complexities, show where the time is spent, and give clear directions for optimization."),
  new Paragraph({ children: [new PageBreak()] }));

// ================= APPENDIX =================
add(H1("Appendix A - Complexity summary"),
  table(["Algorithm", "Time", "Space", "Notes"], [
    ["Merge sort", "O(n log n) always", "O(n)", "Stable"],
    ["Quick sort (random pivot)", "O(n log n) expected, O(n²) worst", "O(log n)", "Not stable"],
    ["Heap sort", "O(n log n) always", "O(1)", "Not stable"],
    ["Insertion sort", "O(n²) worst, O(n) best", "O(1)", "Stable, good for almost-sorted data"],
    ["0/1 Knapsack DP", "O(n·W)", "O(n·W); O(W) value only", "Pseudo-polynomial"],
    ["Dijkstra (binary heap)", "O((V+E) log V)", "O(V)", "Non-negative weights only"],
    ["Nearest-neighbour TSP", "O(k²)", "O(k)", "Heuristic - no constant guarantee"],
    ["2-opt", "O(k²) per pass", "O(k)", "Local search"],
    ["Held-Karp (benchmark only)", "O(k²·2ᵏ)", "O(k·2ᵏ)", "Exact, k ≤ ~12"],
    ["Whole trip", "O(n log n + nW + k(V+E) log V + k²)", "O(nW + k²)", "Dominated by DP and Dijkstra"],
  ], [2500, 3000, 2000, 2138], { zebra: true }),
  H1("Appendix B - Viva preparation (questions and short answers)"),
  table(["Question", "Answer"], [
    ["Why merge sort and not quick sort?", "Merge sort is O(n log n) for every input and stable. Quick sort can degrade to O(n²) and is not stable."],
    ["Trace the knapsack table for 3 parcels.", "Fill row by row: if the parcel does not fit copy the cell above, else take max(above, value + cell above at w − weight). Then trace back from T[n][W]."],
    ["How do you know which parcels were chosen?", "Walk back from T[n][W]: if T[i][w] ≠ T[i−1][w], parcel i is in the knapsack and w decreases by its weight."],
    ["What is the time and space complexity of the DP?", "O(nW) time and O(nW) space; O(W) space if only the best value is needed."],
    ["Why is the DP called pseudo-polynomial?", "Its running time depends on the numeric value of W, not on the number of bits needed to write W."],
    ["Why can't Dijkstra handle negative edges?", "It assumes a settled node can never be improved later; a negative edge breaks this. Use Bellman-Ford instead."],
    ["Why run Dijkstra from every stop?", "The roads are sparse; to compare stops the heuristic needs true shortest distances between all pairs of stops."],
    ["Is nearest neighbour optimal? How good is it?", "No. TSP is NP-hard. Here it averages ~5 % above optimal (worst observed 35 %); 2-opt reduces this to under 0.5 %."],
    ["What does the heap do in Dijkstra?", "It returns the nearest unsettled node in O(log V), giving O((V+E) log V) overall."],
    ["Why does the benchmark show DP so much faster than brute force?", "Brute force checks 2ⁿ subsets; DP reuses overlapping sub-problems and does n·W updates."],
    ["How would you handle a parcel heavier than the van?", "It can never be loaded. The planner reports it as undeliverable (tested)."],
    ["How would you change the value of a parcel?", "Edit the Parcel.value property in courier/models.py; no other code changes."],
    ["How would you add deadline-aware routing?", "Replace nearest neighbour by an insertion heuristic that rejects insertions causing a late arrival (time-window TSP)."],
  ], [3500, 6138], { zebra: true, size: 17 }),
);

const doc = new Document({
  creator: "Student", title: "Mini-Courier Planner - Capstone Report",
  styles: {
    default: { document: { run: { font: FONT, size: 21 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: FONT, color: NAVY }, paragraph: { spacing: { before: 280, after: 160 }, keepNext: true, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 25, bold: true, font: FONT, color: "2E75B6" }, paragraph: { spacing: { before: 220, after: 100 }, keepNext: true, outlineLevel: 1 } },
    ],
  },
  numbering: { config: [
    { reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] },
    { reference: "num", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 540, hanging: 360 } } } }] },
  ] },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [run("Mini-Courier Planner - DAA Capstone (ETCCDA302)  |  Page ", { size: 16, color: "777777" }),
        new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 16, color: "777777" })] })] }) },
    children: kids,
  }],
});
Packer.toBuffer(doc).then(b => { fs.writeFileSync("Mini_Courier_Planner_Report.docx", b); console.log("written"); });
