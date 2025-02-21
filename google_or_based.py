import pandas as pd
from pathlib import Path
from or_utils import create_data_model, compute_euclidean_distance_matrix, print_solution, compute_shortest_path_distance_matrix
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from visualization import plot_routes


customer_path = Path("data//customer_info.csv")
vehicle_path = Path("data//vehicle_info.csv")

SCALE = 1000

customer_df = pd.read_csv(customer_path)
vehicle_df = pd.read_csv(vehicle_path)


home_lat, home_lon = customer_df["latitude"].iloc[0], customer_df["longitude"].iloc[0]

locaiton_to_customer = customer_df.groupby(["latitude", "longitude"])["customer_id"].unique().to_dict()
location_series = customer_df.groupby(["latitude", "longitude"])["demand"].sum()


data = create_data_model(location_series, vehicle_df, (home_lon, home_lat), scale=1000)
distance_matrix = compute_euclidean_distance_matrix(data["locations"])


# Create the routing index manager.
manager = pywrapcp.RoutingIndexManager(
    len(distance_matrix), data["num_vehicles"], data["depot"]
)

# Create Routing Model.
routing = pywrapcp.RoutingModel(manager)


def distance_callback(from_index, to_index):
    """Returns the distance between the two nodes."""
    # Convert from routing variable Index to distance matrix NodeIndex.
    from_node = manager.IndexToNode(from_index)
    to_node = manager.IndexToNode(to_index)
    return distance_matrix[from_node][to_node]

transit_callback_index = routing.RegisterTransitCallback(distance_callback)
routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

def demand_callback(from_index):
    """Returns the demand of the node."""
    # Convert from routing variable Index to demands NodeIndex.
    from_node = manager.IndexToNode(from_index)
    return data["demands"][from_node]

demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)

routing.AddDimensionWithVehicleCapacity(
    demand_callback_index,
    0,  # null capacity slack
    data["vehicle_capacities"],  # vehicle maximum capacities
    False,  # start cumul to zero
    "Capacity",
)

# Setting first solution heuristic.
search_parameters = pywrapcp.DefaultRoutingSearchParameters()
search_parameters.first_solution_strategy = (
    routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
)
search_parameters.local_search_metaheuristic = (
    routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
)
search_parameters.time_limit.FromSeconds(1)

# Solve the problem.
solution = routing.SolveWithParameters(search_parameters)

# Print solution on console.
if solution:
    print_solution(data, manager, routing, solution, scale=SCALE)
    plot_routes(data, manager, routing, solution)
