import pandas as pd
import matplotlib.pyplot as plt
import osmnx as ox
from pathlib import Path
import contextily as cx

class Customer:
    def __init__(self, id, order_id, latitude, longitude, demand):
        self.id = id
        self.order_id = order_id
        self.latitude = latitude
        self.longitude = longitude
        self.demand = demand
        self.visited = False

class Vehicle:
    def __init__(self, type, capacity):
        self.type = type
        self.capacity = capacity
        self.route = []
        self.total_distance = 0
        self.total_demand = 0

class Depot(Customer):
    def __init__(self, latitude, longitude):
        super().__init__(id=0, order_id=0,latitude=latitude, longitude=longitude, demand=0)

class DeliveryProblem:
    def __init__(self, depot, customers, vehicles):
        self.depot = depot
        self.customers = customers
        self.vehicles = vehicles

    def euclidean_distance(self, customer1, customer2):
        return ox.distance.great_circle(customer1.latitude, customer1.longitude, customer2.latitude, customer2.longitude) 

    def nearest_neighbor(self, vehicle, unvisited_customers):
        current_location = self.depot
        while vehicle.total_demand < vehicle.capacity and unvisited_customers:
            min_distance = float('inf')
            nearest_customer = None
            for customer in unvisited_customers:
                if vehicle.total_demand + customer.demand <= vehicle.capacity:
                    distance = self.euclidean_distance(current_location, customer)
                    if distance < min_distance:
                        min_distance = distance
                        nearest_customer = customer
            if nearest_customer is None:
                break  
            vehicle.route.append(nearest_customer)
            vehicle.total_distance += min_distance
            vehicle.total_demand += nearest_customer.demand
            nearest_customer.visited = True
            current_location = nearest_customer
            unvisited_customers.remove(nearest_customer)

         # Returning to depot after visiting customers
        if vehicle.route:
            vehicle.total_distance += self.euclidean_distance(current_location, self.depot)
    
    def optimize_routes(self):
        unvisited_customers = set(self.customers)  # Keep track of unvisited customers
        while unvisited_customers:
            for vehicle in self.vehicles:
                self.nearest_neighbor(vehicle, unvisited_customers)
                if not unvisited_customers:
                    break

    def print_routes(self):
        total_distance = sum(vehicle.total_distance for vehicle in self.vehicles)
        
        print(f"Total Distance = {total_distance:.2f} m")

        for i, vehicle in enumerate(self.vehicles, 1):
            print(f"Vehicle {i} (Type {vehicle.type}):")
            print(f"Round Trip Distance: {vehicle.total_distance:.3f} m, Demand: {vehicle.total_demand}")
            print("Depot -> ", end="")
            for j, customer in enumerate(vehicle.route):
                if j > 0:  # If not the first customer, calculate distance from the previous customer
                    distance = self.euclidean_distance(vehicle.route[j - 1], customer)
                else:  # For the first customer, calculate distance from the depot
                    distance = self.euclidean_distance(self.depot, customer)
                print(f"C{customer.id} ({distance:.3f} km) -> ", end="")
            # After the last customer, print the distance back to the depot
            if vehicle.route:
                distance_back_to_depot = self.euclidean_distance(vehicle.route[-1], self.depot)
                print(f"Depot ({distance_back_to_depot:.3f} km)")

def plot_depot(depot):
    plt.plot(depot.longitude, depot.latitude, 'ks', markersize=10, label='Depot')
    plt.text(depot.longitude, depot.latitude, ' Depot', verticalalignment='bottom', horizontalalignment='right')

def plot_customers(customers):
    for customer in customers:
        plt.plot(customer.longitude, customer.latitude, 'bo', markersize=5)
        plt.text(customer.longitude, customer.latitude, f' C{customer.id}', verticalalignment='bottom', horizontalalignment='right')

def plot_vehicle_route(vehicle, depot, route_color, route_label):
    route_lngs, route_lats = [depot.longitude], [depot.latitude]  
    for customer in vehicle.route:
        route_lngs.append(customer.longitude)
        route_lats.append(customer.latitude)
    route_lngs.append(depot.longitude)  
    route_lats.append(depot.latitude)
    plt.plot(route_lngs, route_lats, route_color, label=route_label)

def plot_routes(vehicles, depot, customers, optimized=False):
    fig, ax = plt.subplots(figsize=(10,7))
    plot_depot(depot)
    plot_customers(customers)

    # Plot the routes for each vehicle
    for vehicle in vehicles:
        if optimized:
            plot_vehicle_route(vehicle, depot, '-o', f'Vehicle {vehicle.type} Optimized')
        else:
            plot_vehicle_route(vehicle, depot, 'r--o', f'Vehicle {vehicle.type} Initial')

    
    cx.add_basemap(ax, crs="EPSG:4326", source=cx.providers.OpenStreetMap.Mapnik, attribution=False, alpha=0.7)
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.title('Delivery Routes Before and After Optimization')
    plt.legend()
    plt.show()

def main():
   # Read customer data from an Excel file
    customer_path = Path("data//customer_info.csv")
    customer_data = pd.read_csv(customer_path)

    # Define depot
    depot = Depot(latitude=customer_data["latitude"].iloc[0], longitude=customer_data["longitude"].iloc[0])
    
    customer_data = customer_data.iloc[1:]
    
    locaiton_to_customer = customer_data.groupby(["latitude", "longitude"])["customer_id"].unique().to_dict()
    locaiton_to_order = customer_data.groupby(["latitude", "longitude"])["order_id"].unique().to_dict()
    location_series = customer_data.groupby(["latitude", "longitude"])["demand"].sum()

    # Create customers from the Excel data
    customers = []
    for index, demand in location_series.items():
        customer_id = locaiton_to_customer[index]
        order_id = locaiton_to_order[index]
        customers.append(Customer(id=customer_id, order_id=order_id, latitude=index[0], longitude=index[1], demand=demand))
    
    vehicle_path = Path("data//vehicle_info.csv")
    vehicle_df = pd.read_csv(vehicle_path)

    # Create vehicles based on the specified numbers
    vehicles = []
    for _, vehicle_type in vehicle_df.iterrows():
        for _ in range(vehicle_type["number_of_vehicles"]):
            vehicles.append(Vehicle(type=vehicle_type["vehicle_type"], capacity=vehicle_type["capacity"]))
        
    print("Number of vehicles ", len(vehicles))
    # Create delivery problem instance
    problem = DeliveryProblem(depot, customers, vehicles)

    # Solve and print routes
    problem.optimize_routes()
    problem.print_routes()

    # Second call - after optimization
    plot_routes(vehicles, depot, customers, optimized=True)

if __name__ == "__main__":
    main()