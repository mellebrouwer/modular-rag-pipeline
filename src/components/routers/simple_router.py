from src.components.routers.base_router import BaseRouter
from src.models import Destination, Query, RoutingTable


# BasicRouter Implementation
class SimpleRouter(BaseRouter):
    def __init__(self):
        pass

    def run(self, queries: list[Query]) -> RoutingTable:
        routing_table = RoutingTable(routes={})
        routes = routing_table.routes

        for query in queries:
            # Example logic for determining the destination
            if "search the web for" in query.text.lower():
                destination = Destination.WEB_SEARCH
            elif "search the relational database for" in query.text.lower():
                destination = Destination.RELATIONAL_DB
            else:
                destination = Destination.RETRIEVER

            # Add the query to the corresponding destination
            if destination not in routes:
                routes[destination] = []
            routes[destination].append(query)

        return routing_table
