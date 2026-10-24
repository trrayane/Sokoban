from search.astar import AStar
from search.bfs import BFS
from search.dfs import DFS

ALGORITHMS = {"BFS": BFS.search, "DFS": DFS.search, "A*": AStar.search}
