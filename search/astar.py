"""Recherche A* avec les heuristiques h1, h2 et h3."""
import heapq
import itertools
import time

from core.node import Node
from search.common import SearchResult, success


class AStar:
    @staticmethod
    def h1(state):
        return len(state.boxes - state.layout.targets)

    @staticmethod
    def h2(state):
        return 2 * AStar.h1(state) + AStar.h3(state)

    @staticmethod
    def h3(state):
        targets = state.layout.targets
        total = 0
        for (br, bc) in state.boxes:
            if (br, bc) in targets:
                continue
            total += min(abs(br - tr) + abs(bc - tc) for (tr, tc) in targets)
        return total

    @staticmethod
    def search(problem, prune_deadlocks=True, max_nodes=1_500_000, heuristic=None):
        if heuristic is None:
            heuristic = AStar.h3
        t0 = time.perf_counter()
        root = Node(problem)
        root.setF(heuristic(root.state))
        counter = itertools.count()
        frontier = [(root.f, next(counter), root)]
        best_g = {root.state: 0}
        expanded, generated, max_front = 0, 1, 1

        while frontier:
            _, _, node = heapq.heappop(frontier)
            if node.g > best_g.get(node.state, float("inf")):
                continue
            if node.state.isGoal():
                return success("A*", node, expanded, generated, max_front,
                               t0, time.perf_counter())
            expanded += 1
            for action, state in node.state.successorFunction():
                if prune_deadlocks and state.is_deadlock():
                    continue
                g = node.g + 1
                if g < best_g.get(state, float("inf")):
                    best_g[state] = g
                    child = Node(state, node, action, g)
                    child.setF(heuristic(state))
                    generated += 1
                    heapq.heappush(frontier, (child.f, next(counter), child))
            max_front = max(max_front, len(frontier))
            if generated > max_nodes:
                return SearchResult("A*", "limit", expanded=expanded, generated=generated,
                                    max_frontier=max_front, time=time.perf_counter() - t0)

        return SearchResult("A*", "no_solution", expanded=expanded, generated=generated,
                            max_frontier=max_front, time=time.perf_counter() - t0)
