"""Parcours en profondeur (DFS) avec détection des états déjà vus."""
import time

from core.node import Node
from search.common import SearchResult, success


def dfs(problem, prune_deadlocks=True, max_nodes=1_500_000):
    """DFS. prune_deadlocks élimine les états où une caisse est sur une case morte :
    élagage admissible (aucune solution n'est perdue car une caisse sur case
    morte ne peut plus jamais rejoindre une cible)."""
    t0 = time.perf_counter()
    root = Node(problem)
    if root.state.isGoal():
        return success("DFS", root, 0, 1, 1, t0, time.perf_counter())

    frontier = [root]                 # pile LIFO
    seen = {root.state}
    expanded, generated, max_front = 0, 1, 1

    while frontier:
        node = frontier.pop()
        expanded += 1
        for action, state in node.state.successorFunction():
            if state in seen:
                continue
            if prune_deadlocks and state.is_deadlock():
                continue
            child = Node(state, node, action, node.g + 1)
            generated += 1
            if state.isGoal():
                return success("DFS", child, expanded, generated,
                               max_front, t0, time.perf_counter())
            seen.add(state)
            frontier.append(child)
        max_front = max(max_front, len(frontier))
        if generated > max_nodes:
            return SearchResult("DFS", "limit", expanded=expanded, generated=generated,
                                max_frontier=max_front, time=time.perf_counter() - t0)

    return SearchResult("DFS", "no_solution", expanded=expanded, generated=generated,
                        max_frontier=max_front, time=time.perf_counter() - t0)
