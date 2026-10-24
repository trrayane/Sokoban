from search.astar import AStar
from search.best import BestAStar
from search.bfs import BFS
from search.dfs import DFS


def _astar(name, heuristic):
    def search(problem, **kwargs):
        result = AStar.search(problem, heuristic=heuristic, **kwargs)
        result.algo = name
        return result
    return search


ALGORITHMS = {
    "BFS": BFS.search,
    "DFS": DFS.search,
    "A* h1": _astar("A* h1", AStar.h1),
    "A* h2": _astar("A* h2", AStar.h2),
    "A* h3": _astar("A* h3", AStar.h3),
    "A* best": BestAStar.search,
}
