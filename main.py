from flask import *
import sqlalchemy as db
from sqlalchemy.orm import sessionmaker
import sqlite3
from chatterbot import ChatBot
from chatterbot.trainers import ListTrainer
from sqlalchemy.ext.declarative import declarative_base
from weather import update_all_weather_forecasts


db_name = r'tourism.db'
Model = declarative_base()
engine = db.create_engine('sqlite:///' + db_name + '?check_same_thread=False')
Model.metadata.create_all(bind=engine)
Session = sessionmaker(bind=engine)

# Standard code block to run Flask.
app = Flask(__name__)


class Weather(Model):
    __tablename__ = 'weather'
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String)
    date = db.Column(db.String)
    day = db.Column(db.String)
    weather_main = db.Column(db.String)
    description = db.Column(db.String)
    min_temp = db.Column(db.Float)
    max_temp = db.Column(db.Float)
    icon = db.Column(db.String)


class Restaurant(Model):
    __tablename__ = 'restaurants'
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String)
    name = db.Column(db.String)
    rating = db.Column(db.Float)
    place_id = db.Column(db.String)


# Chatbot instance with default response
# Requires threshold of 0.90 otherwise it mixes up the responses
# e.g 'What is the weather today in Oxford?' is similar to 'What is the weather today in Cambridge?'
go_travel_bot = ChatBot(
    name="GoTravelBot",
    read_only=True,
    logic_adapters=[
        {
            'import_path': 'chatterbot.logic.BestMatch',
            'default_response': 'I am sorry. I do not understand. You can ask me questions like:'
            + '<br>What is the weather today in Oxford?'
            + '<br>What is the best restaurant in Cambridge?'
            + '<br>Which city has the best weather this week?'
            + '<br>What is the 7 day forecast for Bristol?',
            'maximum_similarity_threshold': 0.90
        }
    ]
)
# Clear database for chatbot so that we can update the data in the weather responses
go_travel_bot.storage.drop()
list_trainer = ListTrainer(go_travel_bot)


# Fetches locations from the database and calls a number of functions to use the data
# from the database to train the chatbot
def load_location_data():
    prepare_best_weather()
    try:
        connection = sqlite3.connect('tourism.db', check_same_thread=False)
        cur = connection.cursor()
        sql_locations_query = """SELECT * FROM places"""
        cur.execute(sql_locations_query)
        locations = cur.fetchall()
        cur.close()
        connection.close()
        for location in locations:
            prepare_todays_weather_response(location[1])
            prepare_best_restaurant_response(location[1])
            weekly_forecast_response(location[1])
    except sqlite3.Error as error:
        print("Failed to read data from sqlite table", error)


# Fetches today's weather data for a location from the database and uses list trainer to
# train chatbot with questions and answers
def prepare_todays_weather_response(loc):
    session_weather = Session()
    forecast_record = session_weather.query(Weather).filter_by(location=loc).order_by(Weather.date.asc()).first()
    clothes_recommendation = ''
    if forecast_record.min_temp < 5:
        clothes_recommendation += "I would recommend wearing warm layers and bringing a jumper with you."
    elif forecast_record.min_temp < 10:
        clothes_recommendation += "I would recommend bringing a jumper with you."
    else:
        pass

    if 'rain' in forecast_record.description:
        clothes_recommendation += " It might be a good idea to take an umbrella with you as rain is forecast."
    else:
        pass

    forecast_response = ("The temperature in " + loc + " today will be a maximum of "
                         + str(forecast_record.max_temp) + "&degC with a low of "
                         + str(forecast_record.min_temp) + "&degC. Expect " + forecast_record.description
                         + ". " + clothes_recommendation)

    current_weather = [
        "What is the weather today in " + loc,
        forecast_response,
        "Can you tell me the weather today for " + loc,
        forecast_response,
        "Weather for " + loc,
        forecast_response,
        loc + " weather please"
    ]
    list_trainer.train(current_weather)
    session_weather.close()


# Fetches weather data from the database and ascertains which location has the best weather then uses list trainer to
# train chatbot with questions and answers
def prepare_best_weather():
    session_best = Session()
    best_weather_record = session_best.query(Weather).order_by(Weather.max_temp.desc()).first()
    best_weather_response = ("The city with the best weather this week is "
                             + best_weather_record.location + ". The maximum temperature will be "
                             + str(best_weather_record.max_temp) + "&degC on " + best_weather_record.day
                             + " the " + best_weather_record.date + ".")
    questions = ("Which city has the best weather this week?", "Where is the best weather this week?",
                 "When is the best weather this week?", "When and where are the best weather this week?")
    for question in questions:
        list_trainer.train([question,
                            best_weather_response
                            ])


# Fetches data on the best restaurant in an area from the database and uses list trainer to
# train chatbot with questions and answers
def prepare_best_restaurant_response(loc):
    session_restaurant = Session()
    restaurant_record = (session_restaurant.query(Restaurant).filter_by(location=loc)
                         .order_by(Restaurant.rating.desc()).first())
    restaurant_response = ("The best restaurant in " + loc + ", according to Google, is "
                           + restaurant_record.name + ". It has a rating of "
                           + str(restaurant_record.rating) + " stars. Here is the link if you are interested: "
                           + '<a href="https://www.google.com/maps/search/?api=1&query=Google&query_place_id='
                           + restaurant_record.place_id + '">link</a>')
    best_rest = [
        "What is the best restaurant in " + loc,
        restaurant_response,
        "Where can I eat in " + loc,
        restaurant_response,
        "Best place to eat in " + loc,
        restaurant_response
    ]
    list_trainer.train(best_rest)
    session_restaurant.close()


# Fetches 7-day forecast weather data for a location from the database and uses list trainer to
# train chatbot with questions and answers
def weekly_forecast_response(loc):
    session_forecast = Session()
    forecast = session_forecast.query(Weather).filter_by(location=loc).order_by(Weather.date.asc()).all()
    forecast_iter = iter(forecast)
    table_data = ''
    while True:
        try:
            day = next(forecast_iter)
            table_data += ('<tr><td>'
                           + day.day + '</td><td>' + day.date + '</td><td>' + day.description + '</td><td>'
                           + str(day.min_temp) + '&degC' + '</td><td>' + str(day.max_temp) + '&degC'
                           + '</td></tr>')
        except StopIteration:
            break
    table_string = ('<div>Here is the forecast for ' + loc + ':<br><h2>' + loc + ' Forecast</h2>'
                    + '<table><tr><th>Day</th><th>Date</th><th>Conditions</th><th>Min Temp</th><th>Max Temp</th></tr>'
                    + table_data + '</table></div>')
    forecast_list = [
        "What is the forecast for " + loc,
        table_string,
        "What is the forecast for this week for " + loc,
        table_string,
        "What is the 7 day forecast for " + loc,
        table_string
    ]
    list_trainer.train(forecast_list)
    session_forecast.close()


# Update all weather data then load all responses into the chatbot
update_all_weather_forecasts()
load_location_data()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/get")
def get_bot_response():
    user_text = request.args.get('msg')
    bot_response = go_travel_bot.get_response(user_text).text
    return str(bot_response)


if __name__ == "__main__":
    app.run()
