"""
The module creates an html file with three layers
of the closest, the farthest and all locations.
"""

import sys
import argparse
from functools import lru_cache
import folium
import pandas
from geopy.geocoders import ArcGIS, Nominatim
from geopy.distance import geodesic


arcgis = ArcGIS(timeout=10)
nominatim = Nominatim(timeout=10, user_agent="htrtrrfr")
geocoders = [arcgis, nominatim]


def open_file(path):
    """
    The function reads a file by givern path
    and returns a list with lines.
    """
    with open(path, "r", encoding="utf-8") as file:
        lst = file.readlines()
    return lst


def filter_lines(lst, year):
    """
    Filters lines from the list by the year.
    Writes the result in file.
    """
    locations = []
    for line in lst:
        if year in line:
            new_line = address_finder(line)
            if new_line not in locations:
                locations.append(new_line)
    data = {'locations': locations}
    data_fr = pandas.DataFrame(data)
    data_fr.to_csv("locations_short.csv", index=False)


@lru_cache(maxsize=None)
def geocode(address):
    """
    Returns coordinates using the address.
    >>> geocode("Chicago, Illinois, USA")
    (41.884250000000065, -87.63244999999995)
    """
    i = 0
    try:
        while i < len(geocoders):
            location = geocoders[i].geocode(address)
            if location is not None:
                return location.latitude, location.longitude
            else:
                i += 1
    except TypeError:
        print(sys.exc_info()[0])
        return ['null', 'null']
    return ['null', 'null']


def address_finder(line: str):
    """
    Finds an adress from the line.
    """
    line = line.split("\t")

    if "(" in line[-1] and ")" in line[-1]:
        return line[-2]
    return line[-1]


def get_coordinates():
    """
    Using the locations_short.csv file
    the functions finds coordinates and writes them in
    """
    data = pandas.read_csv("locations_short.csv")
    locations = data["locations"]
    latitudes = []
    longitudes = []
    for location in locations:
        result = geocode(location)
        latitudes.append(result[0])
        longitudes.append(result[1])
    data["latitudes"] = latitudes
    data["longitudes"] = longitudes
    data.to_csv("locations_short.csv", index=False)


def distance_geopy(lat_1, lat_2, lon_1, lon_2):
    """
    Returns distaance between two locations.
    >>> distance_geopy(48.314775,47.499720000000075, 25.082925, 19.055080000000032)
    459.5282889206637
    """
    first_location = (lat_1, lon_1)
    second_location = (lat_2, lon_2)
    return geodesic(first_location, second_location).km


def distance_operator(lat_1, lon_1):
    """
    Calculates distances between locations from a csv file
    and lat_1, lon_2. Writes the result into the file.
    """
    data = pandas.read_csv("locations_short.csv")
    latitudes = data["latitudes"]
    longitudes = data["longitudes"]
    distances = []
    for lat, lon in zip(latitudes, longitudes):
        distance = distance_geopy(lat_1, lat, lon_1, lon)
        distances.append(distance)
    data["distances"] = distances
    data.to_csv("locations_short.csv", index=False)
    data = pandas.read_csv("locations_short.csv")
    sorted_df = data.sort_values(by=["distances"])
    sorted_df.to_csv("locations_short.csv", index=False)


def create_html(lat, lon, year):
    """
    Creates a html file with the three layers.
    """
    data = pandas.read_csv("locations_short.csv")
    latitudes = data["latitudes"]
    longitudes = data["longitudes"]
    locations = data["locations"]

    my_map = folium.Map(location=[lat, lon], zoom_start=4)
    fg_1 = folium.FeatureGroup(name=f"10 closest locations in {year}")
    for lat, lon, loc in zip(latitudes[0:10], longitudes[0:10], locations[0:10]):
        mark = f"Location: {loc}\nLatitude: {str(round(lat, 6))}\nLongitude: {str(round(lon, 6))}"
        fg_1.add_child(folium.Marker(
            location=[lat, lon], popup=mark, icon=folium.Icon()))

    fg_2 = folium.FeatureGroup(name=f"10 farthest locations in {year}")
    for lat, lon, loc in zip(latitudes[-10:], longitudes[-10:], locations[-10:]):
        mark = f"Location: {loc}\nLatitude: {str(round(lat, 6))}\nLongitude: {str(round(lon, 6))}"
        fg_2.add_child(folium.Marker(
            location=[lat, lon], popup=mark, icon=folium.Icon(color="pink")))

    fg_3 = folium.FeatureGroup(name=f"All locations in {year}")
    for lat, lon, loc in zip(latitudes, longitudes, locations):
        mark = f"Location: {loc}\nLatitude: {str(round(lat, 6))}\nLongitude: {str(round(lon, 6))}"
        fg_3.add_child(folium.Marker(
            location=[lat, lon], popup=mark, icon=folium.Icon(color="green")))

    my_map.add_child(fg_3)
    my_map.add_child(fg_1)
    my_map.add_child(fg_2)
    my_map.add_child(folium.LayerControl())
    my_map.save(f'Map_{year}.html')


def parse_args():
    """
    Returns arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("year", type=str)
    parser.add_argument("latitude", type=float)
    parser.add_argument("longitude", type=float)
    parser.add_argument("path", type=str)
    return parser.parse_args()


def main():
    """
    Operates functions.
    """
    args = parse_args()
    filter_lines(open_file(args.path), args.year)
    get_coordinates()
    distance_operator(args.latitude, args.longitude)
    create_html(args.latitude, args.longitude, args.year)


if __name__ == "__main__":
    main()
    import doctest
    doctest.testmod()
