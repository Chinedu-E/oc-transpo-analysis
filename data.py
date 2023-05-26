import requests
import pandas as pd
from typing import Literal


class Data:
    routes = pd.read_csv("./transit/routes.txt")
    trips = pd.read_csv("./transit/trips.txt")
    stop_times = pd.read_csv("./transit/stop_times.txt")
    stops = pd.read_csv("./transit/stops.txt")
    calender  = pd.read_csv("./transit/calendar.txt")
    calender_dates = pd.read_csv("./transit/calendar_dates.txt")
    shapes = pd.read_csv("./transit/shapes.txt")
    longest_trips = pd.read_csv("./transit/longest_trips.csv")

    def __init__(self, lazy=False):
        ...

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