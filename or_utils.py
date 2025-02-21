
import osmnx as ox


def create_data_model(location_series, vehicle_df, depot_location, scale=1):
    """Stores the data for the problem."""
    data = {}
    data["locations"] = [(index[1], index[0]) for index, row in location_series.items()]
    data["locations"].insert(0, depot_location)

    data["num_vehicles"] = int(vehicle_df["number_of_vehicles"].sum())
    data["depot"] = 0
    data["demands"] = location_series.apply(lambda x:int(round(x*scale))).tolist()
    data["demands"].insert(0,0)
    data["vehicle_capacities"] = []
    for _, row in vehicle_df.iterrows():
        data["vehicle_capacities"].extend([row["capacity"]*scale for _ in range(row["number_of_vehicles"])]) 
    return data


def compute_euclidean_distance_matrix(locations):
    """Creates callback to return distance between points."""
    distances = {}
    for from_counter, from_node in enumerate(locations):
        distances[from_counter] = {}
        for to_counter, to_node in enumerate(locations):
            if from_counter == to_counter:
                distances[from_counter][to_counter] = 0
            else:
                # Euclidean distance
                distances[from_counter][to_counter] = int(
                    # math.hypot((from_node[0] - to_node[0]), (from_node[1] - to_node[1]))
                    ox.distance.great_circle(from_node[1], from_node[0], to_node[1], to_node[0])
                )
    return distances


def compute_shortest_path_distance_matrix(locations, G):
    """Creates callback to return distance between points."""
    distances = {}
    for from_counter, from_node in enumerate(locations):
        origin_node = ox.distance.nearest_nodes(G, from_node[0], from_node[1])
        distances[from_counter] = {}
        for to_counter, to_node in enumerate(locations):
            dest_node = ox.distance.nearest_nodes(G, to_node[0], to_node[1])
            if from_counter == to_counter:
                distances[from_counter][to_counter] = 0
            else:
                path = ox.routing.shortest_path(G, origin_node, dest_node)
                distances[from_counter][to_counter] = int(
                    ox.routing.route_to_gdf(G,path)["length"].sum()
                )
    return distances

def print_solution(data, manager, routing, solution, scale=1):
    """Prints solution on console."""
    print(f"Objective: {solution.ObjectiveValue()}")
    total_distance = 0
    total_load = 0
    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        plan_output = f"Route for vehicle {vehicle_id}:\n"
        route_distance = 0
        route_load = 0
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            route_load += data["demands"][node_index]
            plan_output += f" {node_index} Load({route_load / scale}) -> "
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_distance += routing.GetArcCostForVehicle(
                previous_index, index, vehicle_id
            )
        plan_output += f" {manager.IndexToNode(index)} Load({route_load / scale})\n"
        plan_output += f"Distance of the route: {route_distance}m\n"
        plan_output += f"Load of the route: {route_load / scale}\n"
        print(plan_output)
        total_distance += route_distance
        total_load += route_load
    print(f"Total distance of all routes: {total_distance}m")
    print(f"Total load of all routes: {total_load / scale}")