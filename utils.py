from datetime import datetime


def get_time_difference(start_time: str, end_time: str) -> float:
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

def get_trip_times(trip):
    vals = [time[:2] for time in trip]
    return set(vals)