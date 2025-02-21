
import matplotlib.pyplot as plt
import contextily as cx
from itertools import cycle


def plot_routes(data, manager, routing, solution):
    """Plots the routes on a graph."""
    fig, ax = plt.subplots(figsize=(7,7))
    color_cycle = cycle(plt.rcParams['axes.prop_cycle'].by_key()['color'])
    depot_location = data["locations"][data["depot"]]
    ax.scatter(depot_location[0], depot_location[1], c='black', marker='s', label='Depot')

    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        route_x = [] 
        route_y = [] 
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            location = data["locations"][node_index]
            route_x.append(location[0])  
            route_y.append(location[1])  
            plt.text(location[0], location[1], f'C{node_index}')
            index = solution.Value(routing.NextVar(index))
        route_x.append(depot_location[0])
        route_y.append(depot_location[1])
        vehicle_color = next(color_cycle)
        ax.plot(route_x, route_y, '-o', color=vehicle_color, label=f'Vehicle {vehicle_id}')
        
    cx.add_basemap(ax, crs="EPSG:4326", source=cx.providers.OpenStreetMap.Mapnik, attribution=False, alpha=0.7)
    ax.axis("equal")
    ax.axis("off")
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.set_title('Vehicle Routing Problem')
    fig.legend()
    fig.tight_layout()
    plt.show()
