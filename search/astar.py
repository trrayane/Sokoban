"""Recherche A* avec les heuristiques h1, h2 et h3."""
import heapq
import itertools
import time
from collections import deque

from core.node import Node
from core.puzzle import ACTIONS
from search.common import SearchResult, success

_INF = float("inf")
_PUSH_MAPS = {}


class AStar:
    @staticmethod
    def h1(state):
        return len(state.boxes - state.layout.targets)

    @staticmethod
    def manhattan(state):
        targets = state.layout.targets
        total = 0
        for (br, bc) in state.boxes:
            if (br, bc) in targets:
                continue
            total += min(abs(br - tr) + abs(bc - tc) for (tr, tc) in targets)
        return total

    @staticmethod
    def h2(state):
        return 2 * AStar.h1(state) + AStar.manhattan(state)

    @staticmethod
    def _push_maps(layout):
        maps = _PUSH_MAPS.get(layout)
        if maps is not None:
            return maps
        maps = []
        for (tr, tc) in layout.targets:
            dist = {(tr, tc): 0}
            queue = deque([(tr, tc)])
            while queue:
                r, c = queue.popleft()
                d = dist[(r, c)]
                for dr, dc in ACTIONS.values():
                    br, bc = r - dr, c - dc
                    pr, pc = r - 2 * dr, c - 2 * dc
                    if (br, bc) not in layout.inside or (pr, pc) not in layout.inside:
                        continue
                    if (br, bc) not in dist:
                        dist[(br, bc)] = d + 1
                        queue.append((br, bc))
            maps.append(dist)
        _PUSH_MAPS[layout] = maps
        return maps

    @staticmethod
    def _assignment(dist):
        n = len(dist)
        if n == 0:
            return 0
        dp = [_INF] * (1 << n)
        dp[0] = 0
        for mask in range(1 << n):
            k = mask.bit_count()
            if k == n or dp[mask] == _INF:
                continue
            base = dp[mask]
            row = dist[k]
            for j in range(n):
                if not (mask >> j) & 1:
                    value = base + row[j]
                    nxt = mask | (1 << j)
                    if value < dp[nxt]:
                        dp[nxt] = value
        return dp[-1]

    @staticmethod
    def h3(state):
        boxes = list(state.boxes)
        maps = AStar._push_maps(state.layout)
        dist = [[m.get(box, _INF) for m in maps] for box in boxes]
        return AStar._assignment(dist)

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
