"""Recherche A* avec heuristique admissible (somme des distances caisse -> cible la plus proche)."""
import heapq
import itertools
import time

from core.node import Node
from search.common import SearchResult, success


def heuristic(state):
    targets = state.layout.targets
    total = 0
    for (br, bc) in state.boxes:
        if (br, bc) in targets:
            continue
        total += min(abs(br - tr) + abs(bc - tc) for (tr, tc) in targets)
    return total


def astar(problem, prune_deadlocks=True, max_nodes=1_500_000):
    t0 = time.perf_counter()
    root = Node(problem)
    counter = itertools.count()                       # départage les égalités
    frontier = [(heuristic(root.state), next(counter), root)]
    best_g = {root.state: 0}
    expanded, generated, max_front = 0, 1, 1

    while frontier:
        _, _, node = heapq.heappop(frontier)
        if node.g > best_g.get(node.state, float("inf")):
            continue                                  # entrée périmée
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
                generated += 1
                heapq.heappush(frontier, (g + heuristic(state), next(counter), child))
        max_front = max(max_front, len(frontier))
        if generated > max_nodes:
            return SearchResult("A*", "limit", expanded=expanded, generated=generated,
                                max_frontier=max_front, time=time.perf_counter() - t0)

    return SearchResult("A*", "no_solution", expanded=expanded, generated=generated,
                        max_frontier=max_front, time=time.perf_counter() - t0)
