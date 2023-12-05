import sqlalchemy.orm
from flask import *
import sqlalchemy as db
from sqlalchemy.orm import sessionmaker
import sqlite3
from chatterbot import ChatBot
from chatterbot.trainers import ListTrainer
from sqlalchemy.ext.declarative import declarative_base


db_name = r'tourism.db'
Model = declarative_base()
table_name = 'weather'

engine = db.create_engine('sqlite:///' + db_name)
Model.metadata.create_all(bind=engine)
Session = sessionmaker(bind=engine)
session = Session()


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

# my_bot = ChatBot(
#     name="PyBot",
#     read_only=True,
#     logic_adapters=["chatterbot.logic.BestMatch"]
# )
# my_bot.storage.drop()


def load_location_data():
    try:
        connection = sqlite3.connect('tourism.db')
        cur = connection.cursor()
        sql_locations_query = """SELECT * FROM places"""
        cur.execute(sql_locations_query)
        locations = cur.fetchall()
        cur.close()
        for location in locations:
            pass
    except sqlite3.Error as error:
        print("Failed to read data from sqlite table", error)


def weather_recommendation(min_temp, wea_desc):
    clothes_recommendation = ''
    if min_temp < 5:
        clothes_recommendation += "I would recommend wearing warm layers and bringing a jumper with you."
    elif min_temp < 10:
        clothes_recommendation += "I would recommend bringing a jumper with you."
    else:
        pass

    if 'rain' in wea_desc:
        clothes_recommendation += " It might be a good idea to take an umbrella with you as rain is forecast."
    else:
        pass

    return clothes_recommendation

# print(weather_recommendation(11,'sd'))

small_talk = [
    "Hello there John",
    f"Hi there! The number is 5",
    "How are you doing?",
    "I'm doing great.",
    "That is good to hear",
    "Thank you.",
    "You're welcome."
]
#
# list_trainer = ListTrainer(my_bot)
# list_trainer.train(small_talk)
#
# while True:
#     try:
#         bot_input = input("You: ")
#         bot_response = my_bot.get_response(bot_input)
#         print(f"{my_bot.name}: {bot_response}")
#     except(KeyboardInterrupt, EOFError, SystemExit):
#         break