"""Parcours en largeur (BFS) – partie B du sujet."""
import time
from collections import deque

from core.node import Node
from search.common import SearchResult, success


def bfs(problem, prune_deadlocks=True, max_nodes=1_500_000):
    """BFS. prune_deadlocks élimine les états où une caisse est sur une case morte :
    élagage admissible (aucune solution optimale n'est perdue) qui divise
    l'espace par un facteur énorme sur les niveaux à 4+ caisses."""
    t0 = time.perf_counter()
    root = Node(problem)
    if root.state.isGoal():
        return success("BFS", root, 0, 1, 1, t0, time.perf_counter())

    frontier = deque([root])          # file FIFO
    seen = {root.state}               # frontière + explorés
    expanded, generated, max_front = 0, 1, 1

    while frontier:
        node = frontier.popleft()
        expanded += 1
        for action, state in node.state.successorFunction():
            if state in seen:
                continue
            if prune_deadlocks and state.is_deadlock():
                continue
            child = Node(state, node, action, node.g + 1)
            generated += 1
            if state.isGoal():        # test du but à la génération
                return success("BFS", child, expanded, generated,
                               max_front, t0, time.perf_counter())
            seen.add(state)
            frontier.append(child)
        max_front = max(max_front, len(frontier))
        if generated > max_nodes:
            return SearchResult("BFS", "limit", expanded=expanded, generated=generated,
                                max_frontier=max_front, time=time.perf_counter() - t0)

    return SearchResult("BFS", "no_solution", expanded=expanded, generated=generated,
                        max_frontier=max_front, time=time.perf_counter() - t0)
