from flask import Flask
from flask_bcrypt import Bcrypt
import os
from flask_socketio import SocketIO
from flask_cors import CORS

socket = SocketIO()
cors = CORS()

app = Flask(__name__,static_folder='assests')
print(__name__)
app.config['SECRET_KEY'] = os.urandom(32)
app.config['UPLOAD_FOLDER'] = 'app/assests/static/users_uploads/'

bcrypt = Bcrypt(app)
socket.init_app(app, cors_allowed_origins="*")
cors.init_app(app)

#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
#app.config['UPLOAD_FOLDER'] = 'application/static'
#db = SQLAlchemy(app)
#login_manager = LoginManager(app)
#login_manager.login_view="login"
#login_manager.login_message_category="info"

from app import routes