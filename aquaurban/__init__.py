from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_socketio import SocketIO
import aquaurban

app = Flask(__name__)
app.config.from_object('config.default')
app.add_template_global(aquaurban, 'aquaurban')
'''
THE CONFIG DIRECTORY IS IN THE ROOT DIRECTORY AND IGNORED BY GIT FOR SECURITY.
TO MAKE THE APP RUN, CREATE YOUR OWN CONFIG PACKAGE OR DO AS YOU LIKE...
see: http://exploreflask.com/en/latest/configuration.html
'''
db = SQLAlchemy(app)
'''
TO USE THE DATABASE WITH SQLALCHEMY, YOU NEED TO ADD A CONFIG VARIABLE
CALLED "SQLALCHEMY_DATABASE_URI" WITH THE FILEPATH RELATIVE TO THE
"aquaurban" PACKAGE FOLDER.
'''
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'danger'
socketio = SocketIO(app, async_mode='threading')

from aquaurban import http_route, ws_route
from aquaurban.mqtt_route import MqttHub
mqtt_hub = MqttHub()