from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config

from flask_socketio import SocketIO

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = "login"

socketio = SocketIO(app)
# socketio.init_app(app)

# if __name__ == '__main__':
# 	socketio.run(app)

from app import routes, models


# comment lines below when creating the database. uncomment lines below when running the app
from app.params import ONLINE_CONDITIONS, IN_PERSON_CONDITIONS

rows = (db.session.query(models.OnlineCondition).count() + db.session.query(models.InPersonCondition).count())
if rows == 0:
	for condition in ONLINE_CONDITIONS:
		no_feedback_trial = condition.index("no_feedback")
		feedback_trial = 1 - no_feedback_trial
		feedback_type = condition[feedback_trial]
		trials = condition
		db.session.add(models.OnlineCondition(trials=trials, no_feedback_trial=no_feedback_trial, feedback_trial=feedback_trial, feedback_type=feedback_type, count=0))
	for condition in IN_PERSON_CONDITIONS:
		trials = condition
		db.session.add(models.InPersonCondition(trials=trials, trial_1=condition[0], trial_2=condition[1], trial_3=condition[2], trial_4=condition[3], trial_5=condition[4], count=0))

db.session.commit()
