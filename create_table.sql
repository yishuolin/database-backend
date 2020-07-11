DROP TABLE IF EXISTS song_att;
DROP TABLE IF EXISTS temp_songs;
DROP TABLE IF EXISTS temp_genres; 
DROP TABLE IF EXISTS song_info;
DROP TABLE IF EXISTS genre_info;

CREATE TEMP TABLE temp_songs (
    acousticness REAL,
    artists TEXT,
    danceability REAL,
    duration_ms INTEGER,
    energy REAL,
    explicit INTEGER,
    id TEXT PRIMARY KEY,
    instrumentalness REAL,
    key INTEGER,
    liveness INTEGER,
    loudness REAL,
    mode INTEGER,
    name TEXT,
    popularity INTEGER,
    release_date INTEGER,
    speechiness REAL,
    tempo REAL,
    valence REAL,
    year INTEGER
);

CREATE TEMP TABLE temp_genres(
    genres PRIMARY KEY,
    acousticness REAL,
    danceability REAL,
    duration_ms REAL,
    energy REAL,
    instrumentalness REAL,
    liveness REAL,
    loudness REAL,
    speechiness REAL,
    tempo REAL,
    valence REAL,
    popularity REAL,
    key INTEGER,
    mode INTEGER
);

CREATE TABLE song_att(
    id PRIMARY KEY,
    energy REAL,
    danceability REAL,
    tempo  INTEGER,
    valence REAL,
    liveness REAL,
    acousticness REAL
);

CREATE TABLE genre_info(
    genres PRIMARY KEY,
    energy REAL,
    danceability REAL,
    tempo  INTEGER,
    valence REAL,
    liveness REAL,
    acousticness REAL
);

CREATE TABLE song_info(
    id TEXT PRIMARY KEY, 
    songname TEXT NOT NULL, 
    artistname TEXT, 
    duration INTEGER
);