import sqlalchemy.orm
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
table_name = 'weather'

engine = db.create_engine('sqlite:///' + db_name)
Model.metadata.create_all(bind=engine)
Session = sessionmaker(bind=engine)
session = Session()

# Standard code block to run Flask.
app = Flask(__name__)


class Weather(Model):
    __tablename__ = 'weather'
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String)
    date = db.Column(db.String)
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

go_travel_bot = ChatBot(
    name="GoTravelBot",
    read_only=True,
    logic_adapters=["chatterbot.logic.BestMatch"]
)
# Clear database for chatbot so that we can update the data in the weather responses
go_travel_bot.storage.drop()

list_trainer = ListTrainer(go_travel_bot)


def load_location_data():
    try:
        connection = sqlite3.connect('tourism.db')
        cur = connection.cursor()
        sql_locations_query = """SELECT * FROM places"""
        cur.execute(sql_locations_query)
        locations = cur.fetchall()
        cur.close()
        for location in locations:
            prepare_todays_weather_response(location[1])
            prepare_best_restaurant_response(location[1])
    except sqlite3.Error as error:
        print("Failed to read data from sqlite table", error)


def prepare_todays_weather_response(loc):
    forecast_record = session.query(Weather).filter_by(location=loc).order_by(Weather.date.asc()).first()
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
    ]
    list_trainer.train(current_weather)


def prepare_best_restaurant_response(loc):
    restaurant_record = session.query(Restaurant).filter_by(location=loc).order_by(Restaurant.rating.desc()).first()
    restaurant_response = ("The best restaurant in " + loc + ", according to Google, is "
                           + restaurant_record.name + ". It has a rating of "
                           + str(restaurant_record.rating) + " stars. Here is the link if you are interested: "
                           + "https://www.google.com/maps/search/?api=1&query=Google&query_place_id="
                           + restaurant_record.place_id)
    best_rest = [
        "What is the best restaurant in " + loc,
        restaurant_response
    ]
    list_trainer.train(best_rest)

# Update all weather data then load all responses into the chatbot
# update_all_weather_forecasts()
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

