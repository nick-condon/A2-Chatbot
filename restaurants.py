import requests
import constants
import sqlite3
import json

# Code used to load restaurants into the restaurants table in the database.
# A decision has been made not to schedule this in this instance as the list is unlikely to change often
# Code is here for ability demonstration purposes only

# import the Google API Key
google_api = constants.api_geocoding
# base URL for the Google API
google_places_base_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?"
# base URL for locating a point of interest
google_places_location_base_url = "https://www.google.com/maps/search/?api=1&query=Google&query_place_id="

def load_restaurants():
    try:
        connection = sqlite3.connect('tourism.db')
        cur = connection.cursor()
        sql_locations_query = """SELECT * FROM places"""
        cur.execute(sql_locations_query)
        locations = cur.fetchall()
        cur.close()
        for location in locations:
            get_restaurants(location[1], location[2], location[3])
    except sqlite3.Error as error:
        print("Failed to read data from sqlite table", error)

def get_restaurants(location, latitude, longitude):
    resp = requests.get(google_places_base_url
                        + "location="
                        + str(latitude) + ','
                        + str(longitude)
                        + "&radius=5000"
                        + "&type=restaurant"
                        + "&key=" + google_api)
    resp = json.loads(resp.text)
    results = resp["results"]
    restaurant_list = []
    iter_object = iter(results)
    while True:
        try:
            place = next(iter_object)

            try:
                name = place["name"]
            except KeyError as e:
                pass

            try:
                rating = place["rating"]
            except KeyError as e:
                pass

            try:
                place_id = place["place_id"]
            except KeyError as e:
                pass

            data = (
                None,
                location,
                name,
                rating,
                place_id
            )
            restaurant_list.append(data)
        except StopIteration:
            break

    connection = sqlite3.connect('tourism.db')
    cursor = connection.cursor()
    cursor.executemany(
        'INSERT INTO restaurants (id, location, name, rating, place_id) VALUES (?,?,?,?,?)',restaurant_list)
    connection.commit()
    connection.close()

# load_restaurants()