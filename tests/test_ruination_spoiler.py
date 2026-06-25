"""Regression tests for the ruination spoiler-log parser / branch rebuilder.

Run with:  python -m unittest tests.test_ruination_spoiler
(from the repository root).
"""

import os
import unittest

import networkx as nx

from ruination_spoiler import parse_spoiler, build_branches
from ruination_spoiler.analyze import analyze_branch

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures",
                       "ruin_sample_spoiler.txt")


class RuinationSpoilerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.log = parse_spoiler(FIXTURE)
        cls.branches = build_branches(cls.log)

    def test_header_and_party(self):
        self.assertEqual(self.log.seed, "c0z37vr3vnc5")
        self.assertTrue(self.log.is_ruination())
        self.assertTrue(self.log.has_verbose)
        self.assertEqual(self.log.starting_party, ["GOGO", "LOCKE", "STRAGO"])

    def test_rewards_parsed(self):
        chars = {r.reward_name: r.branch for r in self.log.character_rewards}
        self.assertEqual(chars, {"TERRA": 2, "MOG": 0, "CYAN": 2})
        self.assertEqual(len(self.log.terminus_routes), 3)
        self.assertGreater(len(self.log.map_connections), 100)

    def test_three_branches(self):
        self.assertEqual([b.index for b in self.branches], [0, 1, 2])
        for b in self.branches:
            self.assertIn(b.hub, b.graph)
            self.assertIsNotNone(b.terminus)

    def test_branch1_fully_connected_no_softlock(self):
        # Branch 1 is the seed's reported concern: it should reconstruct with
        # every room reachable from the hub and back, terminus reachable.
        b1 = self.branches[1]
        g = b1.graph
        comp = nx.node_connected_component(g.to_undirected(), b1.hub)
        self.assertEqual(len(comp), g.number_of_nodes(),
                         "branch 1 should be fully connected")
        report = analyze_branch(b1)
        self.assertTrue(report.terminus_reachable)
        self.assertEqual(report.softlock_pockets, [])
        self.assertEqual(report.unreachable_rewards, [])

    def test_one_way_edges_are_directed(self):
        # Zozo has internal one-way drops; make sure they are modelled as
        # single-direction edges, not two-way.
        g = self.branches[1].graph
        oneways = [(u, v) for u, v, d in g.edges(data=True)
                   if d.get("kind") == "oneway"]
        self.assertTrue(oneways)
        for u, v in oneways:
            self.assertFalse(g.has_edge(v, u),
                             "one-way %s->%s must not have a reverse edge" % (u, v))


if __name__ == "__main__":
    unittest.main()
