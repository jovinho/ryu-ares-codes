import networkx as nx

class TopologyService:
    class __TopologyService:
        def __init__(self):
            self.net = nx.DiGraph()
            self.nodes = {}
            self.links = {}

        def __str__(self):
            return repr(self)

    instance = None

    def __init__(self):
        if not TopologyService.instance:
            TopologyService.instance = TopologyService.__TopologyService()

    def __getinstance__(self):
        return self.instance

    def __getattr__(self, name):
        return getattr(self.instance, name)

