class PathStore:
    def __init__(self):
        self.route = None
        self.eta_seconds = None

    def save(self, route, eta_seconds):
        self.route = route
        self.eta_seconds = eta_seconds

    def get_route(self):
        return self.route

    def get_eta(self):
        return self.eta_seconds
