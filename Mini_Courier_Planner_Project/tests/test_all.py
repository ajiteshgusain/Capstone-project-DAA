"""Run with:  python -m unittest discover -s tests -v"""
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from courier import verification as V
from courier.data_io import load_problem
from courier.graph import (dijkstra, expand_route, held_karp, nearest_neighbor_tour,
                           reconstruct_path, stop_distances, tour_length)
from courier.knapsack import knapsack_dp
from courier.models import Graph, Parcel
from courier.planner import plan_all_trips, plan_trip
from courier.sorting import SORTERS, parcel_key, prioritise

DATA = Path(__file__).resolve().parents[1] / "data"


class TestSorting(unittest.TestCase):
    def test_all_sorters_match_reference(self):
        trials, res = V.check_sorting(100)
        for name, passed in res.items():
            self.assertEqual(passed, trials, name)

    def test_order_rule(self):
        ps = [Parcel("A", 1, 1, 5, 1), Parcel("B", 1, 5, 5, 1), Parcel("C", 1, 1, 2, 1)]
        self.assertEqual([p.pid for p in prioritise(ps)], ["C", "B", "A"])

    def test_empty_and_single(self):
        for fn in SORTERS.values():
            self.assertEqual(fn([]), [])
            p = [Parcel("A", 1, 1, 1, 1)]
            self.assertEqual(fn(p), p)

    def test_merge_sort_is_stable(self):
        ps = [Parcel("A", 1, 3, 4, 1), Parcel("B", 1, 3, 4, 1)]
        self.assertEqual(SORTERS["merge"](ps, key=lambda p: p.deadline_h), ps)


class TestKnapsack(unittest.TestCase):
    def test_textbook_example(self):
        r = knapsack_dp([1, 3, 4, 5], [1, 4, 5, 7], 7)
        self.assertEqual(r.best_value, 9)
        self.assertEqual(r.chosen, [1, 2])

    def test_matches_bruteforce(self):
        trials, ok, _ = V.check_knapsack(150)
        self.assertEqual(trials, ok)

    def test_zero_capacity_and_oversize(self):
        self.assertEqual(knapsack_dp([5], [10], 0).best_value, 0)
        self.assertEqual(knapsack_dp([9], [10], 5).chosen, [])


class TestGraph(unittest.TestCase):
    def test_dijkstra_small(self):
        g = Graph()
        for u, v, w in [(0, 1, 4), (0, 2, 1), (2, 1, 2), (1, 3, 1), (2, 3, 5)]:
            g.add_edge(u, v, w)
        d, p = dijkstra(g, 0)
        self.assertEqual(d, {0: 0, 1: 3, 2: 1, 3: 4})
        self.assertEqual(reconstruct_path(p, 0, 3), [0, 2, 1, 3])

    def test_negative_weight_rejected(self):
        with self.assertRaises(ValueError):
            Graph().add_edge(0, 1, -1)

    def test_dijkstra_vs_floyd_warshall(self):
        trials, ok = V.check_dijkstra(15)
        self.assertEqual(trials, ok)

    def test_disconnected_graph_detected(self):
        g = Graph(); g.add_edge(0, 1, 1); g.add_node(2)
        with self.assertRaises(ValueError):
            stop_distances(g, [0, 2])

    def test_tsp_properties(self):
        trials, valid, bounded, improved, _avg, _mx = V.check_tsp(20)
        self.assertEqual((valid, bounded, improved), (trials, trials, trials))


class TestPipeline(unittest.TestCase):
    def test_small_sample_known_answer(self):
        prob = load_problem(DATA / "small.json")
        trip = plan_trip(prob, prob.parcels)
        self.assertEqual(sorted(p.pid for p in trip.loaded),
                         ["P01", "P03", "P05", "P08", "P09", "P10"])
        self.assertEqual(trip.knapsack.best_value, 361)
        self.assertEqual(trip.knapsack.total_weight, 25)
        self.assertLessEqual(trip.knapsack.total_weight, prob.capacity)
        self.assertEqual(trip.tour, [0, 1, 3, 5, 6, 0])
        self.assertEqual(trip.route, [0, 1, 3, 5, 6, 5, 3, 2, 0])
        self.assertEqual(trip.route_km, 37.0)
        self.assertEqual(trip.route[0], 0)
        self.assertEqual(trip.route[-1], 0)

    def test_route_length_equals_sum_of_edges(self):
        prob = load_problem(DATA / "small.json")
        trip = plan_trip(prob, prob.parcels)
        w = {(u, v): c for u, v, c in prob.graph.edges()}
        w.update({(v, u): c for (u, v), c in list(w.items())})
        total = sum(w[(a, b)] for a, b in zip(trip.route, trip.route[1:]))
        self.assertTrue(math.isclose(total, trip.route_km, abs_tol=1e-9))

    def test_all_trips_cover_every_parcel_once(self):
        prob = load_problem(DATA / "medium.json")
        trips, bad = plan_all_trips(prob)
        ids = [p.pid for t in trips for p in t.loaded]
        self.assertEqual(sorted(ids + [p.pid for p in bad]), sorted(p.pid for p in prob.parcels))
        self.assertEqual(len(ids), len(set(ids)))
        for t in trips:
            self.assertLessEqual(sum(p.weight for p in t.loaded), prob.capacity)

    def test_oversize_parcel_reported(self):
        prob = load_problem(DATA / "small.json")
        prob.parcels.append(Parcel("BIG", prob.capacity + 1, 5, 1, 1))
        trips, bad = plan_all_trips(prob)
        self.assertEqual([p.pid for p in bad], ["BIG"])


if __name__ == "__main__":
    unittest.main()
