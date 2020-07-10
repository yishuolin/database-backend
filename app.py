from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_login import LoginManager,UserMixin,login_user,current_user,login_required,logout_user
from flask_migrate import Migrate
from flask import g
from utils import *
import sqlite3
import csv
import pandas as pd
import json


# Create Flask app
app = Flask(__name__)

# Make the api can be access from anywhere
CORS(app, supports_credentials=True)

# Set secret key for sessionss
app.config['SECRET_KEY'] = 'secret'

# Make json output prettier
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# Set the database uri
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///test.db"

# Disable Track to elimate warning
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Create database instance, which will reference the above database uri
db = SQLAlchemy(app)

# Create migration tools to easy manage db by using
# flask db init
# flask db migrate -m "Initial migration."
# flask db upgrade
migrate = Migrate(app, db)

# Create loginmanager instance to easy manage login
login_manager = LoginManager()
login_manager.init_app(app)

# User Table
class User(db.Model,UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120))
    def __init__(self, username, password):
        self.username = username
        self.password = password
    def save_to_db(self):
        db.session.add(self)
        db.session.commit()
    def delete(self):
        db.session.delete(self)
        db.session.commit()
    def __repr__(self):
        return '<User %r>' % (self.username)

# SQLite
DATABASE = "test.db"

def get_db():
    db_sqlite = getattr(g, '_database', None)
    if db_sqlite is None:
        db_sqlite = g._database = sqlite3.connect(DATABASE)
    return db_sqlite
def init_db():
    with app.app_context():
        db_sqlite = get_db()
        with app.open_resource('create_table.sql', mode='r') as f:
            db_sqlite.cursor().executescript(f.read())
        cur = db_sqlite.cursor()

        read = pd.read_csv(r'./data/data.csv')
        read.to_sql('temp_songs', db_sqlite, if_exists='append', index=False)
        read = pd.read_csv(r'./data/data_by_genres.csv')
        read.to_sql('temp_genres', db_sqlite, if_exists='append', index=False)
        
        cur.execute('INSERT INTO song_att(id, energy, danceability, tempo, valence, liveness, acousticness) \
                    SELECT id, energy, danceability, tempo, valence, liveness, acousticness \
                    FROM temp_songs;')
        
        cur.execute('INSERT INTO song_info(id, songname, artistname, duration) \
                    SELECT id, name, artists, duration_ms FROM temp_songs;')

        cur.execute('INSERT INTO genre_info(genre, energy, danceability, tempo, valence, liveness, acousticness)\
                    SELECT genres as genre, energy, danceability, tempo, valence, liveness, acousticness \
                    FROM temp_genres;')

        cur.execute('DROP TABLE IF EXISTS temp_songs;')
        cur.execute('DROP TABLE IF EXISTS temp_genre;')
        db_sqlite.commit()

# Response wrapper
def error(msg):
    return jsonify({
        'error': True,
        'msg': msg
    })
def success(data):
    return jsonify({
        'error': False,
        'data': data
    })

# For Login Manager
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)
@login_manager.unauthorized_handler
def unauthorized_handler():
    return error("Not log in!")

# Preprocessing request values
def get_request_value(req):
    if req.method == 'POST':
        return req.get_json(force=True)
    else:
        return req.values

# Flask routes
# To let cors post work, one should set request content type to text/plain to no send option request
# every api here will ignore the content-type field to convert it to json
@app.route('/')
def index():
    #cur = get_db().cursor()
    return 'This is Backend.'

@app.route('/login',methods=['GET','POST'])
def login():
    values = get_request_value(request)
    if values.get('username') == None or values.get('password') == None:
        return error('Empty Filed!')
    else:
        username = values.get('username')
        password = values.get('password')
    user = User.query.filter(User.username == username, User.password == password).first()
    if user != None:
        login_user(user)
        return success({'username':user.username})
    else:
        return error('Invalid Credential!')

@app.route('/userinfo',methods=['GET','POST'])
@login_required
def userinfo():
    return success({'username':current_user.username})

@app.route('/logout',methods=['GET','POST'])
@login_required
def logout():
    logout_user()
    return success({'msg':'Logout Finished'})


# for test
@app.route('/test',methods=['GET','POST'])
def GET_SONGS():
    songs = []
    conn = sqlite3.connect('test.db')
    cursor = conn.cursor()
    query = 'SELECT * FROM song_att limit 10'
    for item in cursor.execute(query):
        # add key value pair
        song = {}
        song.update({'id': item[0], 'energy': item[1], 'danceability': item[2], 'tempo': item[3]})
        song.update({'valence': item[4], 'liveness': item[5], 'acousticness': item[6]})
        songs.append(song)
    conn.close()
    return jsonify(songs)

@app.route('/register',methods=['GET','POST'])
def register():
    values = get_request_value(request)
    if values.get('username') == None or values.get('password') == None:
        return error('Empty Field!')
    else:
        username = values.get('username')
        password = values.get('password')
    
    user = User.query.filter_by(username=username).first()
    if user == None:
        user = User(username,password)
        user.save_to_db()
        return success({'username':user.username})
    else:
        return error('Name Exists!')

@app.route('/query1', methods=['GET', 'POST'])
def query():
    list = []
    c = get_db().cursor()
    for row in c.execute("SELECT songname, duration FROM song_info WHERE artistname LIKE '%Justin Bieber%';"):
        list.append(row)
    T = tuple(list)
    return T[0]

# have error
@app.route('/get_songs', methods=['GET', 'POST'])
def get_songs():
    values = get_request_value(request)
    if values.get('atmosphere') == None or values.get('bpm') == None:
        return error('Empty Field!')
    else:
        genre = genre_selection(values.get('atmosphere'))
        para = (genre, values.get('bpm'),)
        cur = get_db().cursor()
        return cur.execute('SELECT id FROM song_att \
            WHERE att.energy = (SELECT energy FROM genre_info \
            WHERE genre_info.genre = ? \
            ) AND tempo = ?', para)

@app.teardown_appcontext
def close_connection(expection):
    db_sqlite = getattr(g, '_database', None)
    if db_sqlite is not None:
        db_sqlite.close()

if __name__ == '__main__':
    init_db()
    app.run(debug=True,host='0.0.0.0',port=5000,threaded=True)