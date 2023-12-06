import requests
import constants
from datetime import datetime
import sqlite3
import multiprocessing


# Function to delete all records in a table
def clear_database_table(db_name, table_name):
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    del_query = 'DELETE FROM ' + table_name
    cursor.execute(del_query)
    connection.commit()
    cursor.close()
    connection.close()


# Function to get the weather data and return it into an instance of a WeatherData class.
def get_weather_forecast(location_array):
    location = location_array[1]
    lat = location_array[2]
    lng = location_array[3]
    API_key = constants.api_key_openweather
    # requests API data using inputs
    resp = requests.get(f'https://api.openweathermap.org/data/2.5/onecall?'
                        f'lat={lat}'
                        f'&lon={lng}'
                        f'&appid={API_key}'
                        f'&units=metric').json()

    # create empty array to store forecast
    weatherforecast = []

    # create iterable object to go through the 'daily' array in the returned API
    iter_object = iter(resp.get('daily'))
    while True:
        try:
            day = next(iter_object)
            data = (
                None,
                location,
                datetime.fromtimestamp((day.get('dt'))).strftime('%d-%m-%Y'),
                datetime.fromtimestamp((day.get('dt'))).strftime('%A'),
                day.get('weather')[0].get('main'),
                day.get('weather')[0].get('description'),
                round(day.get('temp').get('min'), 1),
                round(day.get('temp').get('max'), 1),
                day.get('weather')[0].get('icon')
            )
            weatherforecast.append(data)
        except StopIteration:
            break
    connection = sqlite3.connect('tourism.db')
    cursor = connection.cursor()
    cursor.executemany('INSERT INTO weather (id, location, date, day, weather_main, description, min_temp, max_temp, icon) VALUES (?,?,?,?,?,?,?,?,?)', weatherforecast)
    connection.commit()
    connection.close()


def update_all_weather_forecasts():
    clear_database_table('tourism.db', 'weather')
    try:
        connection = sqlite3.connect('tourism.db')
        cur = connection.cursor()
        sql_locations_query = """SELECT * FROM places"""
        cur.execute(sql_locations_query)
        locations = cur.fetchall()
        cur.close()
        connection.close()
        processes = []
        for location in locations:
            p = multiprocessing.Process(target=get_weather_forecast, args=(location,))
            processes.append(p)
            p.start()
            # get_weather_forecast(location)
        for process in processes:
            process.join()
    except sqlite3.Error as error:
        print("Failed to read data from sqlite table", error)

if __name__ == '__main__':
    update_all_weather_forecasts()



