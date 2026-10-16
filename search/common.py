"""Structure de résultat commune à tous les algorithmes de recherche."""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SearchResult:
    algo: str
    status: str = "no_solution"            # 'ok' | 'limit' | 'no_solution'
    solution: Optional[List[str]] = None   # liste d'actions
    path: Optional[list] = None            # liste d'états (pour la simulation)
    cost: Optional[int] = None             # coût de la solution (nb de pas)
    expanded: int = 0                      # nœuds développés ("étapes")
    generated: int = 0                     # nœuds générés
    max_frontier: int = 0                  # taille max de la frontière
    time: float = 0.0                      # secondes


def success(algo, node, expanded, generated, max_frontier, t0, now):
    return SearchResult(
        algo=algo, status="ok",
        solution=node.getSolution(), path=node.getPath(), cost=node.g,
        expanded=expanded, generated=generated,
        max_frontier=max_frontier, time=now - t0,
    )
