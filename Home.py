import streamlit as st
from streamlit_folium import st_folium
import folium
from data import Data
import pandas as pd
import numpy as np
import altair as alt


st.set_page_config(layout="wide")


@st.cache
def get_locations():
    df = data.stops.sample(750)
    return df[["stop_lat", "stop_lon"]].values


def plot_riders():
    df = pd.read_csv("./transit/riders.csv")
    df["Ridership - Conventional"] = pd.to_numeric(df["Ridership - Conventional"].str.replace(",", ""))
    df["Year"] = df["Year"].astype(str)

    chart = alt.Chart(df, title="Total bus and train riders", height=450).mark_line().encode(
        x='Month',
        y='Ridership - Conventional',
        color='Year'
    )
    point = chart.mark_point()
    return (chart+point).interactive()


def plot_bus_performance():
    df = pd.read_csv("./transit/performance.csv")
    df["on-time"] = df["on-time"].str.replace("%", "").astype(float)
    df["Year"] = df["Year"].astype(str)
    chart = alt.Chart(df, title="Bus on-time percentage", height=450).mark_line().encode(
        x=alt.X('Month'),
        y=alt.Y('on-time',scale=alt.Scale(zero=False)),
        color=alt.Color('Year')
    )
    point = chart.mark_point()
    chart += point
    return chart.interactive()


def plot_wait_times():
    df = pd.read_csv("./transit/excess_wait_time.csv")
    df["Year"] = df["Year"].astype(str)
    chart = alt.Chart(df, title="Excess wait times (mins)", height=450).mark_line().encode(
        x='Month',
        y='wait_time',
        color='Year'
    )
    point = chart.mark_point()
    return (chart+point).interactive()


def plot_longest_trip_time(n=10):
    df = data.longest_trips
    df.sort_values("trip_time", ascending=False)
    df = pd.concat([df.iloc[:n], df.iloc[-n:]])
    chart = alt.Chart(df, title="Buses with longest trip times").mark_bar().encode(
        y=alt.Y("heading", sort = alt.EncodingSortField(
                    field="trip_time",
                    order="ascending"  # The order to sort in
                ), title="Trip time"),
        x='trip_time',
        color=alt.Color("route_id", legend=alt.Legend(title="Bus Line"))
    )
    return (chart).interactive()


def plot_most_stops(n=10):
    df = data.longest_trips
    df.sort_values("n", ascending=False)
    df = pd.concat([df.iloc[:n], df.iloc[-n:]])
    chart = alt.Chart(df, title="Buses with the most stops").mark_bar().encode(
        x=alt.X("n", title="Bus Number"),
        y=alt.Y("heading", sort = alt.EncodingSortField(
                    field="n",
                    order="ascending"  # The order to sort in
                ), title="Number of Stops"),
        color=alt.Color("route_id", legend=alt.Legend(title="Bus Line"))
    )
    return (chart).interactive()


@st.cache
def get_most_stops(n):
    seen = []
    max_stops = []
    for stop_n in reversed(data.stop_times["stop_sequence"].unique()):
        df = data.stop_times[data.stop_times["stop_sequence"] == stop_n]
        for trip_id in df["trip_id"].values:
            bus = data.trips[data.trips["trip_id"] == trip_id]["route_id"].values[0]
            if bus not in seen:
                seen.append(bus)
                max_stops.append(stop_n)
        if len(seen) >= n:
            break
    df = pd.DataFrame({"Bus": seen, "Number of Stops": max_stops})
    df["Bus"] = df["Bus"].apply(data.get_short_name)
    return df


def plot_longest():
    chart = alt.Chart(data.longest_trips, title="Scatter plot of distance travelled vs number of stops").mark_point().encode(
        y="n",
        x="distance(km)"
    )
    return chart.interactive()


def get_longest():
    df = pd.read_csv("longest_trips.csv")
    return df


def render_map():
    locations = get_locations()
    m = folium.Map(location=[45.4215, -75.6972], tiles="cartodbpositron", zoom_start=13)

    for loc in locations:
        folium.Marker(loc, icon=folium.Icon(icon="bus", prefix='fa')).add_to(m)

    st_data = st_folium(m, width=1025)


def show_general():
    st.altair_chart(plot_riders(), use_container_width=True)
    st.altair_chart(plot_bus_performance(), use_container_width=True)
    st.altair_chart(plot_wait_times(), use_container_width=True)
    st.altair_chart(plot_longest_trip_time(), use_container_width=True)
    st.altair_chart(plot_most_stops(), use_container_width=True)
    st.altair_chart(plot_longest(), use_container_width=True)

@st.cache
def get_oc_transpo_stats():
    performance_df = pd.read_csv("./transit/performance.csv")
    performance_df["on-time"] = performance_df["on-time"].str.replace("%", "").astype(float)
    performance = {}

    performance["label"] = "% on-time buses (2022)"
    performance["value"] = f'{np.round(performance_df[performance_df["Year"] == 2022]["on-time"].mean(), 2)}%'
    performance["delta"] = f'{np.round(performance_df[performance_df["Month"] == "December"]["on-time"].pct_change().values[-1]*100, 2)}%'

    wait_time_df = pd.read_csv("./transit/excess_wait_time.csv")
    wait_time = {}
    wait_time["label"] = "Average wait time (minutes)"
    wait_time["value"] = np.round(wait_time_df[wait_time_df["Year"] == 2022]["wait_time"].mean(), 2)
    wait_time["delta"] = f'{np.round(wait_time_df[wait_time_df["Month"] == "December"]["wait_time"].pct_change().values[-1]*100, 2)}%'

    riders_df = pd.read_csv("./transit/riders.csv")
    riders_df["Ridership - Conventional"] = riders_df["Ridership - Conventional"].str.replace(",", "").astype(int)
    riders = {}
    riders["label"] = "Average number of riders (2022)"
    riders["value"] = int(riders_df["Ridership - Conventional"].mean())
    riders["delta"] = f'{np.round(riders_df[riders_df["Month"] == "December"]["Ridership - Conventional"].pct_change().values[-1]*100, 2)}%'

    return [performance, wait_time, riders]

data = Data()


st.title('OC Transpo Data Analysis')

render_map()

stats = get_oc_transpo_stats()
col1, col2, col3 = st.columns(3)
col1.metric("Total Number of lines", "193")
col3.metric("Number of Bus stops", str(len(data.stops)))

col1, col2, col3 = st.columns(3)
col1.metric(**stats[0])
col2.metric(**stats[1])
col3.metric(**stats[2])

"---"


show_general()



