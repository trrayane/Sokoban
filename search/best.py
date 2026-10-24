"""Sélection automatique de la meilleure heuristique A*."""
from concurrent.futures import ThreadPoolExecutor

from search.astar import AStar


class BestAStar:
    @staticmethod
    def search(problem, **kwargs):
        heuristics = (AStar.h1, AStar.h2, AStar.h3)

        def run(heuristic):
            return heuristic, AStar.search(problem, heuristic=heuristic, **kwargs)

        with ThreadPoolExecutor(max_workers=len(heuristics)) as pool:
            results = list(pool.map(run, heuristics))
        heuristic, best = min(results, key=BestAStar._rank)
        best.algo = f"A* best ({heuristic.__name__})"
        return best

    @staticmethod
    def _rank(item):
        heuristic, result = item
        if result.status != "ok":
            return (1, -result.expanded, heuristic.__name__)
        return (0, result.cost, result.expanded, result.time, heuristic.__name__)
