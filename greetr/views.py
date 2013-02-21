import random
import flask
from flask import g
from greetr import app

def random_greeting():
	greetings = ["Greetings, human!", 
				 "Howdy!",
				 "How are you?",
				 "Have a good day, sir and/or madam!" ,
				 "Good morning! And in case I don't see ya, good afternoon, good evening and goodnight!",
				 "May the force be with you.",
				 "Live long and prosper!"]
	random.shuffle(greetings)
	return greetings[0]


@app.route('/')
def index():
    return flask.render_template('greeting.html', greeting=random_greeting())
