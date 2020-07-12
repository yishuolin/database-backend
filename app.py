from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_login import LoginManager,UserMixin,login_user,current_user,login_required,logout_user
from flask_migrate import Migrate
from flask import g
from utils import *
import json
import sqlite3
import csv
import pandas as pd

# Create Flask app
app = Flask(__name__)

# Make the api can be access from anywhere
CORS(app, supports_credentials=True)

# Set secret key for sessions
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
    music_list = db.Column(db.TEXT)
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.music_list = ""
    def save_to_db(self):
        db.session.add(self)
        db.session.commit()
    def delete(self):
        db.session.delete(self)
        db.session.commit()
    def __repr__(self):
        return '<User %r>' % (self.username)

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

# building song_att, song_info, genre_info tables
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

        cur.execute('INSERT INTO genre_info(genres, energy, danceability, tempo, valence, liveness, acousticness)\
                    SELECT genres, energy, danceability, tempo, valence, liveness, acousticness \
                    FROM temp_genres;')

        cur.execute('DROP TABLE IF EXISTS temp_songs;')
        cur.execute('DROP TABLE IF EXISTS temp_genres;')
        db_sqlite.commit()

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
@app.route('/api')
def index():
    return 'This is Backend.'

@app.route('/api/login',methods=['GET','POST'])
def login():
    values = get_request_value(request)
    if not values.get('username') or not values.get('password'):
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

@app.route('/api/userinfo',methods=['GET','POST'])
@login_required
def userinfo():
    return success({'username':current_user.username})

@app.route('/api/logout',methods=['GET','POST'])
@login_required
def logout():
    logout_user()
    return success({'msg':'Logout Finished'})

@app.route('/api/register',methods=['GET','POST'])
def register():
    values = get_request_value(request)
    if not values.get('username') or not values.get('password'):
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

# chooes songs by the chosen atmosphere
@app.route('/api/get_songs', methods=['GET', 'POST'])
def get_songs():
    values = get_request_value(request)
    if values.get('atmosphere') == None or values.get('duration') == None:
        return error('Empty Field!')
    else:
        genre = genre_selection(values.get('atmosphere'))
        duration = int(values.get('duration')) * 60000
        cur = get_db().cursor()
        para = (genre,)
        genre_standard = cur.execute('SELECT * FROM genre_info WHERE genres = ?;', para).fetchone()
        
        total_dur = 0

        query = 'SELECT songname, artistname, duration FROM (SELECT t1.id as id, t2.songname as songname, t2.artistname as artistname\
                , t2.duration as duration, ( ABS(t1.energy - ?) + ABS(t1.danceability - ?) + ABS(t1.valence - ?) \
                + ABS(t1.tempo - ?) + ABS(t1.liveness - ?) + ABS(t1.acousticness - ?)) as dist FROM song_att as t1,\
                song_info as t2 WHERE t1.id = t2.id ORDER BY dist ASC LIMIT 50) ORDER BY RANDOM();'
        
        para = (genre_standard[1], genre_standard[2], genre_standard[3], genre_standard[4], genre_standard[5], genre_standard[6],)

        song_list = []
        for song_result in cur.execute(query, para).fetchall():
            #song_result = cur.execute('SELECT songname, artistname, duration FROM song_info WHERE id = ? ', (item[0], )).fetchone()
            song = {}
            song.update({'songname': song_result[0], 'artistname': song_result[1]})
            song_list.append(song)
            total_dur = total_dur + song_result[2]
            if total_dur > duration:
                break

        return jsonify(song_list)

# choose song by specific values of tempo, energy, and liveness
@app.route('/api/customize_attributes', methods=['GET', 'POST'])
def customize_attributes():
    values = get_request_value(request)
    if values.get('tempo') == None or values.get('energy') == None or values.get('liveness') == None:
        return error({'Empty field!'})
    else :
        tempo = float(values.get('tempo'))
        energy = float(values.get('energy'))
        liveness = float(values.get('liveness'))
        duration = int(values.get('duration')) * 60000

        para = (energy, tempo, liveness,)
        cur = get_db().cursor()
        query = 'SELECT songname, artistname, duration FROM (SELECT t1.id as id, t2.songname as songname, t2.artistname as artistname\
                    , t2.duration as duration, ( ABS(t1.energy - ?) + ABS(t1.tempo - ?) + ABS(t1.liveness - ?)) as dist \
                    FROM song_att as t1, song_info as t2 WHERE t1.id = t2.id ORDER BY dist ASC LIMIT 50) ORDER BY RANDOM();'

        total_duration = 0
        song_list = []
        for item in cur.execute(query, para):
            song = {}
            song.update({'songname': item[0], 'artistname': item[1]})
            song_list.append(song)
            total_duration = total_duration + int(item[2])
            if total_duration > duration:
                break

        return jsonify(song_list)


@app.route('/api/add_song_to_database', methods=['GET', 'POST'])
def add_song_to_database():
    values = get_request_value(request)
    if values.get('songname') == None or values.get('artistname') == None or values.get('atmosphere') == None:
        return error('Please fill in all the information correctly')
    else : 
        songname = values.get('songname')
        artistname = values.get('artistname')
        atmos = values.get('atmosphere')
        duration = 10000 # example

        genre = genre_selection(atmos)

        db_sqlite = get_db()
        cur = db_sqlite.cursor()
        genre_standard = cur.execute('SELECT * FROM genre_info WHERE genres = ?', (genre,)).fetchone()
        new_id = id_generator()
        while cur.execute('SELECT * FROM song_info WHERE id = ?', (new_id,)).fetchone() != None :
            new_id = id_generator()
        
        para = (new_id, genre_standard[1], genre_standard[2], genre_standard[3], genre_standard[4], \
                genre_standard[5], genre_standard[6],)
        cur.execute('INSERT INTO song_att VALUES(?, ?, ?, ?, ?, ?, ?)', para)

        para = (new_id, songname, artistname, duration,)
        cur.execute('INSERT INTO song_info VALUES(?, ?, ?, ?)', para)
        db_sqlite.commit()

        return success({'msg':'Add new song to database successfully', 'song':songname, 'artist': artistname})

@app.teardown_appcontext
def close_connection(expection):
    db_sqlite = getattr(g, '_database', None)
    if db_sqlite is not None:
        db_sqlite.close()   

if __name__ == '__main__':
    init_db()
    app.run(debug=True,host='0.0.0.0',port=5000,threaded=True)