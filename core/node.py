"""Modélisation du nœud de l'arbre de recherche (partie A.2 du sujet)."""


class Node:
    def __init__(self, state, parent=None, action=None, g=0):
        self.state = state      # instance de SokobanPuzzle
        self.parent = parent    # nœud parent
        self.action = action    # action appliquée au parent pour obtenir ce nœud
        self.g = g              # coût du chemin (coût d'un pas = 1)
        self.f = None

    def setF(self, h):
        self.f = self.g + h
        return self.f

    def getPath(self):
        """Liste des états, de l'état initial jusqu'à ce nœud."""
        node, path = self, []
        while node is not None:
            path.append(node.state)
            node = node.parent
        return path[::-1]

    def getSolution(self):
        """Liste des actions, de l'état initial jusqu'à ce nœud."""
        node, actions = self, []
        while node.parent is not None:
            actions.append(node.action)
            node = node.parent
        return actions[::-1]
