from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium
import altair as alt

import utils as U
from data import Data

@st.cache
def get_all_lines():
    stops = data.routes["route_short_name"]
    return stops


def get_bus_stats(bus, heading):
    longest_df = data.longest_trips
    longest = longest_df[(longest_df["heading"] == heading) & (longest_df["route_id"] == str(bus))]
    trip_stops = data.stop_times[data.stop_times["trip_id"] == longest.longest_trip.values[0]]

    time_str = trip_stops["arrival_time"].values
    time_bw_stops = []
    for i in range(1, len(time_str)):
        diff = U.get_time_difference(time_str[i-1], time_str[i])
        time_bw_stops.append(diff)

    stats = {
        "total_stops": longest.n,
        "total_time": longest.trip_time,
        "avg_time_bw_stops": np.round(np.mean(time_bw_stops), 2)
        }
    return stats



def plot_trip_time_boxplot(bus, heading):
    route_id = data.routes[data.routes["route_short_name"] == bus]["route_id"].values[0]
    trips = data.trips[(data.trips.route_id == route_id) & (data.trips.trip_headsign == heading)]
    stop_times = [
       U.get_total_trip_time(data.get_trip_stops(trip_id)) for trip_id in trips["trip_id"].values
    ]
    df = pd.DataFrame(stop_times, columns=["stop_times"])
    df["bus"] = [f"{bus_line} - {direction}"] * len(stop_times)
    chart = alt.Chart(df).mark_boxplot(size=80).encode(
        x = "bus",
        y = alt.Y('stop_times:Q',scale=alt.Scale(zero=False)),
        ).properties(width=600)
    return chart






def plot_avg_trip_times(heading, granularity):
    if granularity == "weekly":
        saturday = data.get_avg_trip_time(heading, "saturday")
        sunday = data.get_avg_trip_time(heading, "sunday")
        weekday = data.get_avg_trip_time(heading, "monday")

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
        weekday = data.get_avg_time_bw_stops(heading, "monday")
        sat = data.get_avg_time_bw_stops(heading, "saturday")
        sun = data.get_avg_time_bw_stops(heading, "sunday")
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




def get_daily_time(trip_id):
    time_data = {}
    trip = data.stop_times[data.stop_times["trip_id"] == trip_id]
    times = U.get_trip_times(trip["arrival_time"].values)
    
    for time in times:
        dt = trip[trip.arrival_time.str.startswith(time)]
        if dt.iloc[0]["stop_sequence"] != 1:
            continue
        trip_time = U.get_total_trip_time(dt)
        time_data[time] = trip_time
    return time_data




def render_map(bus_line, heading):
    direction_shape, stops_coords, stop_names = data.get_stops(bus_line, heading)

    m = folium.Map()

    polyline = folium.PolyLine(direction_shape, color='blue', smooth_factor=2.0).add_to(m)

    for stop, stop_name in zip(stops_coords, stop_names):
        folium.Marker(stop, icon=folium.Icon(icon="bus", prefix='fa'), popup=stop_name, tooltip=stop_name).add_to(m)

    m.fit_bounds(polyline.get_bounds())
    return m


data = Data()
lines = get_all_lines()

bus_line = st.selectbox("Enter bus line", options=lines)

headings = data.get_headings(bus_line)
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


