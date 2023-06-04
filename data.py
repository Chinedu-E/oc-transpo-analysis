import requests
import pandas as pd
import numpy as np
from typing import Literal

import utils as U

class Data:
    

    def __init__(self, lazy=False):
        self.routes = pd.read_csv("./transit/routes.txt")
        self.trips = pd.read_csv("./transit/trips.txt")
        self.stop_times = pd.read_csv("./transit/stop_times.txt")
        self.stops = pd.read_csv("./transit/stops.txt")
        self.calender  = pd.read_csv("./transit/calendar.txt")
        self.calender_dates = pd.read_csv("./transit/calendar_dates.txt")
        self.shapes = pd.read_csv("./transit/shapes.txt")
        self.longest_trips = pd.read_csv("./transit/longest_trips.csv")

    def get_bus_trips(self, route_id: str, direction: Literal["0", "1"]) -> pd.DataFrame:
        trips = self.trips[(self.trips["route_id"] == route_id) & (self.trips["direction_id"] == int(direction))]
        return trips

    def get_stop_times(self, trip_id: str) -> pd.DataFrame:
        stops = self.stop_times[self.stop_times["trip_id"] == trip_id]
        return stops

    def get_stop_name(self, stop_id: str) -> str:
        stop_name = self.stops[self.stops["stop_id"] == stop_id]["stop_name"].values[0]
        return stop_name

    def get_short_name(self, route_id: str):
        name = self.routes[self.routes["route_id"] == route_id]["route_short_name"].values[0]
        return name

    def get_headings(self, bus: str):
        route_id = self.routes[self.routes["route_short_name"] == bus]["route_id"].values[0]
        headings = self.trips[self.trips.route_id == route_id]["trip_headsign"]
        return headings.unique()

    def get_stops(self, bus: str, heading: str):
        longest_df = self.longest_trips
        longest = longest_df[(longest_df["heading"] == heading) & (longest_df["route_id"] == str(bus))]
        direction = self.trips[self.trips.trip_id == longest.longest_trip.values[0]]
        direction_shape = self.shapes[self.shapes["shape_id"] == direction.shape_id.values[0]][["shape_pt_lat", "shape_pt_lon"]].values
        stop_ids = self.stop_times[self.stop_times["trip_id"] == direction["trip_id"].values[0]]["stop_id"].values
        stops_coords = [self.stops[self.stops["stop_id"] == stop_id][["stop_lat", "stop_lon"]].values
                        for stop_id in stop_ids]
        stop_names = [self.get_stop_name(stop_id) for stop_id in stop_ids]
        return direction_shape, stops_coords, stop_names

    def get_trip_stops(self, trip_id: str):
        trip_stops = self.stop_times[self.stop_times["trip_id"] == trip_id]
        return trip_stops

    def get_service_id(self, day: str):
        return self.calender[self.calender[day] == 1]["service_id"].values

    def get_avg_trip_time(self, heading, service):
        time_data = []
        service_ids = self.get_service_id(service)
        for service_id in service_ids:
            trips = self.trips[(self.trips["service_id"] == service_id) & (self.trips["trip_headsign"] == heading)]
            stop_times = [
                U.get_total_trip_time(self.get_trip_stops(trip_id)) for trip_id in trips["trip_id"].values[-5:]
                ]
            time_data += stop_times
        return np.array(time_data)

    def get_avg_time_bw_stops(self, heading: str, service: str):
        time_data = []
        service_ids = self.get_service_id(service)
        for service_id in service_ids:
            trips = self.trips[(self.trips["service_id"] == service_id) & (self.trips["trip_headsign"] == heading)]
            for trip in trips["trip_id"].values[-5:]:
                stop = self.get_trip_stops(trip)
                time_str = stop["arrival_time"].values
                for i in range(1, len(time_str)):
                    diff = U.get_time_difference(time_str[i-1], time_str[i])
                    time_data.append(diff)
        return np.array(time_data)

    
    def get_daily_time(self, trip_id):
        time_data = {}
        trip = self.stop_times[self.stop_times["trip_id"] == trip_id]
        times = U.get_trip_times(trip["arrival_time"].values)
        
        for time in times:
            dt = trip[trip.arrival_time.str.startswith(time)]
            if dt.iloc[0]["stop_sequence"] != 1:
                continue
            trip_time = U.get_total_trip_time(dt)
            time_data[time] = trip_time
        return time_data