from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st
from data import Data
import folium
from streamlit_folium import st_folium
import altair as alt

@st.cache
def get_all_lines():
    stops = data.routes["route_short_name"]
    return stops


def get_headings(bus):
    route_id = data.routes[data.routes["route_short_name"] == bus]["route_id"].values[0]
    headings = data.trips[data.trips.route_id == route_id]["trip_headsign"]
    return headings.unique()


def get_stops(bus: str, heading: str):
    longest_df = pd.read_csv("longest_trips.csv")
    longest = longest_df[(longest_df["heading"] == heading) & (longest_df["route_id"] == str(bus))]
    direction = data.trips[data.trips.trip_id == longest.longest_trip.values[0]]
    direction_shape = data.shapes[data.shapes["shape_id"] == direction.shape_id.values[0]][["shape_pt_lat", "shape_pt_lon"]].values
    stop_ids = data.stop_times[data.stop_times["trip_id"] == direction["trip_id"].values[0]]["stop_id"].values
    stops_coords = [data.stops[data.stops["stop_id"] == stop_id][["stop_lat", "stop_lon"]].values
                    for stop_id in stop_ids]
    stop_names = [data.get_stop_name(stop_id) for stop_id in stop_ids]
    return direction_shape, stops_coords, stop_names


def get_time_difference(start_time, end_time) -> float:
    if int(start_time[:2]) > 23:
        start_time = f"{int(start_time[:2])-24}{start_time[2:]}"
    if int(end_time[:2]) > 23:
        end_time = f"{int(end_time[:2])-24}{end_time[2:]}"

    t1 = datetime.strptime(start_time, "%H:%M:%S")
    t2 = datetime.strptime(end_time, "%H:%M:%S")
    delta = t2 - t1
    minutes = delta.total_seconds() / 60
    if minutes < 0:
        minutes += 24*60
    return minutes


def get_total_trip_time(trip):
    start, end = trip.iloc[0]["departure_time"], trip.iloc[-1]["arrival_time"]
    total_trip_time = get_time_difference(start, end)
    return total_trip_time


def get_longest_trip(trips):
    vals = [len(get_trip_stops(trip)) for trip in trips]
    return np.argmax(vals)


def get_bus_stats(bus, heading):
    longest_df = pd.read_csv("longest_trips.csv")
    longest = longest_df[(longest_df["heading"] == heading) & (longest_df["route_id"] == str(bus))]
    trip_stops = data.stop_times[data.stop_times["trip_id"] == longest.longest_trip.values[0]]

    time_str = trip_stops["arrival_time"].values
    time_bw_stops = []
    for i in range(1, len(time_str)):
        diff = get_time_difference(time_str[i-1], time_str[i])
        time_bw_stops.append(diff)

    stats = {
        "total_stops": longest.n,
        "total_time": longest.trip_time,
        "avg_time_bw_stops": np.round(np.mean(time_bw_stops), 2)
        }
    return stats


def get_trip_stops(trip_id):
    trip_stops = data.stop_times[data.stop_times["trip_id"] == trip_id]
    return trip_stops


def plot_trip_time_boxplot(bus, heading):
    route_id = data.routes[data.routes["route_short_name"] == bus]["route_id"].values[0]
    trips = data.trips[(data.trips.route_id == route_id) & (data.trips.trip_headsign == heading)]
    stop_times = [
       get_total_trip_time(get_trip_stops(trip_id)) for trip_id in trips["trip_id"].values
    ]
    df = pd.DataFrame(stop_times, columns=["stop_times"])
    df["bus"] = [f"{bus_line} - {direction}"] * len(stop_times)
    chart = alt.Chart(df).mark_boxplot(size=80).encode(
        x = "bus",
        y = alt.Y('stop_times:Q',scale=alt.Scale(zero=False)),
        ).properties(width=600)
    return chart


def get_service_id(day: str):
    return data.calender[data.calender[day] == 1]["service_id"].values


def get_avg_trip_time(heading, service):
    time_data = []
    service_ids = get_service_id(service)
    for service_id in service_ids:
        trips = data.trips[(data.trips["service_id"] == service_id) & (data.trips["trip_headsign"] == heading)]
        stop_times = [
            get_total_trip_time(get_trip_stops(trip_id)) for trip_id in trips["trip_id"].values[-5:]
            ]
        time_data += stop_times
    return np.array(time_data)


def get_avg_time_bw_stops(heading, service: str):
    time_data = []
    service_ids = get_service_id(service)
    for service_id in service_ids:
        trips = data.trips[(data.trips["service_id"] == service_id) & (data.trips["trip_headsign"] == heading)]
        for trip in trips["trip_id"].values[-5:]:
            stop = get_trip_stops(trip)
            time_str = stop["arrival_time"].values
            for i in range(1, len(time_str)):
                diff = get_time_difference(time_str[i-1], time_str[i])
                time_data.append(diff)
    return np.array(time_data)


def plot_avg_trip_times(heading, granularity):
    if granularity == "weekly":
        saturday = get_avg_trip_time(heading, "saturday")
        sunday = get_avg_trip_time(heading, "sunday")
        weekday = get_avg_trip_time(heading, "monday")

        sat_avg = np.mean(saturday)
        sun_avg = np.mean(sunday)
        weekday_avg = np.mean(weekday)

        df = pd.DataFrame({"Day": ["Weekday", "Saturday", "Sunday"], "Average Trip Time": [weekday_avg, sat_avg, sun_avg]})
        chart = alt.Chart(df).mark_bar().encode(
            y="Day",
            x="Average Trip Time",
            color="Day"
        ).properties(
            width=450,
            height=400,
        )
        return chart
        

    if granularity == "daily":
        
        df = pd.read_csv("hourly_average_trips.csv")
        df = df[df.heading == heading]
        df["time"] = df["time"].apply(lambda x: x-24 if x > 23 else x)
        df["day"] = df["day"].str.replace("monday", "weekday")
        chart = alt.Chart(df).mark_line().encode(
            x=alt.X("time:O", title="Hour of the day"),
            y="avg_trip_time",
            color="day"
        )
        point = chart.mark_point()
        chart += point
        return chart.interactive()


def plot_avg_time_bw_stops(heading, granularity):
    if granularity == "daily":
        ...
        
    if granularity == "weekly":
        weekday = get_avg_time_bw_stops(heading, "monday")
        sat = get_avg_time_bw_stops(heading, "saturday")
        sun = get_avg_time_bw_stops(heading, "sunday")
        sat_avg = np.mean(sat)
        sun_avg = np.mean(sun)
        weekday_avg = np.mean(weekday)
        df = pd.DataFrame({"Day": ["Weekday", "Saturday", "Sunday"], "stop_time": [weekday_avg, sat_avg, sun_avg]})
        chart = alt.Chart(df).mark_bar().encode(
            y=alt.Y("Day", title="Day", sort=alt.EncodingSortField(
                field="stop_time",
                order="ascending",
            )),
            x=alt.X("stop_time",title="Average Time Between Stops"),
            color="Day"
        ).properties(
            width=450,
            height=400,
        )
        return chart.interactive()


def get_avg_daily_trip_times(heading, service):
    time_data: dict[str, list] = {}
    service_ids = get_service_id(service)
    for service_id in service_ids:
        trips = data.trips[(data.trips["service_id"] == service_id) & (data.trips["trip_headsign"] == heading)]
        for trip in trips.trip_id.values:
            trip_time_data = get_daily_time(trip)
            for trip_time in trip_time_data:
                if trip_time in time_data:
                    time_data[trip_time].append(trip_time_data[trip_time])
                else:
                    time_data[trip_time] = [trip_time_data[trip_time]]
    return time_data


def get_daily_time(trip_id):
    time_data = {}
    trip = data.stop_times[data.stop_times["trip_id"] == trip_id]
    times = get_trip_times(trip["arrival_time"].values)
    
    for time in times:
        dt = trip[trip.arrival_time.str.startswith(time)]
        if dt.iloc[0]["stop_sequence"] != 1:
            continue
        print(dt)
        trip_time = get_total_trip_time(dt)
        time_data[time] = trip_time
    return time_data


def get_trip_times(trip):
    vals = [time[:2] for time in trip]
    return set(vals)


def render_map(bus_line, heading):
    direction_shape, stops_coords, stop_names = get_stops(bus_line, heading)

    m = folium.Map()

    polyline = folium.PolyLine(direction_shape, color='blue', smooth_factor=2.0).add_to(m)

    for stop, stop_name in zip(stops_coords, stop_names):
        folium.Marker(stop, icon=folium.Icon(icon="bus", prefix='fa'), popup=stop_name, tooltip=stop_name).add_to(m)

    m.fit_bounds(polyline.get_bounds())
    return m


data = Data()
lines = get_all_lines()

bus_line = st.selectbox("Enter bus line", options=lines)

headings = get_headings(bus_line)
direction = st.selectbox("Select bus trip", options=headings)


m = render_map(bus_line, direction)
st_data = st_folium(m, width=825)

stats = get_bus_stats(bus_line, direction)
cols = st.columns(3)

with cols[0]:
    st.metric("Number of Stops", stats["total_stops"])

with cols[1]:
    st.metric("Longest trip time (minutes)", int(stats["total_time"]))

with cols[2]:
    st.metric("Avg time between stops (minutes)", stats["avg_time_bw_stops"])

"---"

granularity = st.selectbox("Select granularity", options=["weekly", "daily"])

if granularity == "weekly":
    st.altair_chart(plot_avg_time_bw_stops(direction, granularity), True)
    
st.altair_chart(plot_avg_trip_times(direction, granularity), True)


