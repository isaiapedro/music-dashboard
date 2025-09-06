import numpy as np
import pandas as pd
import logging
import requests
import datetime
import psycopg2
from psycopg2.extensions import register_adapter, AsIs
register_adapter(np.int64, AsIs)

hostname = 'localhost'
database = 'music-app'
username = 'postgres'
pwd = '4B3questnloot'
port_id = 5432

conn = None
cur = None

file = open("log.txt", "a")
file.write(f"Admin Task executed at {datetime.datetime.now()}\n")
file.close()

PROJECT_ID = "um-ano-e-meio-de-musica"

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def extract_music():
    """
    Extracts data from the API and saves it to a JSON file.
    """

    logging.info("Requesting API data...")

    try:
        response = requests.get("https://1001albumsgenerator.com/api/v1/projects/{}".format(PROJECT_ID))
        response.raise_for_status()  # Raise an error for bad responses
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch data from URL: {e}")
        return

    data = response.json()

    # current album
    current_album = data['currentAlbum']

    artist = current_album['artist']
    artistOrigin = current_album['artistOrigin']
    imagesUrl = current_album['images'][0]['url']
    genres = current_album['genres']
    subGenres = current_album['subGenres']
    name = current_album['name']
    releaseDate = current_album['releaseDate']
    youtubeMusicId = current_album['youtubeMusicId']
    spotifyId = current_album['spotifyId']

    current = pd.DataFrame({
        'artist': artist,
        'artistOrigin': artistOrigin,
        'images': imagesUrl,
        'genres': [genres],
        'subGenres': [subGenres],
        'name': name,
        'releaseDate': releaseDate,
        'youtubeMusicId': youtubeMusicId,
        'spotifyId': spotifyId
    }, index=[0])

    logging.info(f"Extracted data for current album: {name} by {artist}")

    # listening history
    history = pd.DataFrame(data['history'])

    # past albums

    all_albums = history['album'].tolist()
    past_albums = pd.DataFrame(all_albums)

    albums_df = pd.DataFrame()

    albums_df['artist'] = past_albums['artist']
    albums_df['name'] = past_albums['name']
    albums_df['artistOrigin'] = past_albums['artistOrigin']
    albums_df['releaseDate'] = past_albums['releaseDate']
    albums_df['images'] = past_albums['images'].apply(lambda x: x[0]['url'] if isinstance(x, list) and len(x) > 0 else None)
    albums_df['genres'] = past_albums['genres'].apply(lambda x: x if isinstance(x, list) else [])
    albums_df['subGenres'] = past_albums['subGenres'].apply(lambda x: x if isinstance(x, list) else [])
    albums_df['rating'] = history['rating']
    albums_df['globalRating'] = history['globalRating']
    albums_df['review'] = history['review']
    albums_df['youtubeMusicId'] = past_albums['youtubeMusicId']

    logging.info("Data extracted and saved sucessfully.")

    return current, albums_df


def transform_music(df1, df2):
    """
    Applies transformations to the data pulled from XComs.
    """
    logging.info("Transforming data...")
    logging.info(f"Applying transformations to {len(df2) + len(df1)} rows...")

    # Convert list columns to comma-separated strings
    for col in ['genres', 'subGenres']:
        df1[col] = df1[col].apply(lambda x: ', '.join(x) if isinstance(x, list) else x)

    for col in ['genres', 'subGenres']:
        df2[col] = df2[col].apply(lambda x: ', '.join(x) if isinstance(x, list) else x)

    # Merge genres and subGenres into a single column
    df2['allGenres'] = df2.apply(lambda row: ', '.join(filter(None, [row['genres'], row['subGenres']])), axis=1)

    # Remove genre duplicates
    df2['allGenres'] = df2['allGenres'].apply(lambda x: ', '.join(sorted(set(map(str.strip, x.split(','))))))

    # Drop the original genres and subGenres columns
    df2 = df2.drop(columns=['genres', 'subGenres'])

    # Create 5 albums global rating streak
    df2['streak'] = df2['globalRating'].rolling(window=5).mean()

    # Remove Nan Values on Rating
    df2 = df2.dropna(subset=['rating'])
    df2['rating'] = df2['rating'].astype(int)

    logging.info("Data transformed successfully.")

    return df1, df2


def load_music(df1, df2):
    """
    Loads transformed data into a PostgreSQL database.
    """
    try:
        conn = psycopg2.connect(
            host=hostname,
            dbname=database,
            user=username,
            password=pwd,
            port=port_id
        )

        cur = conn.cursor()

        logging.info("Connected to database successfully.")

        # Drop tables if they exist
        drop_script = '''
        DROP TABLE IF EXISTS current_album;
        DROP TABLE IF EXISTS albums;
        '''
        cur.execute(drop_script)
        conn.commit()

        logging.info("Dropped 'current_album' and 'albums' tables if they existed.")

        # Create tables if they don't exist
        create_script = '''
        CREATE TABLE IF NOT EXISTS current_album (
            artist VARCHAR(255),
            artistOrigin VARCHAR(255),
            images VARCHAR(255),
            genres VARCHAR(255),
            subGenres VARCHAR(255),
            name VARCHAR(255),
            releaseDate int,
            youtubeMusicId VARCHAR(255),
            spotifyId VARCHAR(255)
        )
        '''
        cur.execute(create_script)

        conn.commit()

        logging.info("Created 'current_album' table if it didn't exist.")

        insert_script = 'INSERT INTO current_album (artist, artistOrigin, images, genres, subGenres, name, releasedate, youtubemusicid, spotifyid) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)'

        insert_value = (
            df1['artist'].iloc[0],
            df1['artistOrigin'].iloc[0],
            df1['images'].iloc[0],
            df1['genres'].iloc[0],
            df1['subGenres'].iloc[0],
            df1['name'].iloc[0],
            df1['releaseDate'].iloc[0],
            df1['youtubeMusicId'].iloc[0],
            df1['spotifyId'].iloc[0]
        )

        cur.execute(insert_script, insert_value)
        conn.commit()

        logging.info("Inserted data into 'current_album' table.")

        create_script = '''
        CREATE TABLE IF NOT EXISTS albums (
            artist VARCHAR(255),
            name VARCHAR(255),
            artistOrigin VARCHAR(255),
            releaseDate VARCHAR(255),
            images VARCHAR(255),
            allGenres VARCHAR(255),
            streak float,
            rating INT,
            globalRating float,
            review TEXT,
            youtubeMusicId VARCHAR(255)
        )
        '''
        cur.execute(create_script)
        conn.commit()

        logging.info("Created 'albums' table if it didn't exist.")

        insert_script = 'INSERT INTO albums (artist, name, artistOrigin, releaseDate, images, allGenres, streak, rating, globalRating, review, youtubeMusicId) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'

        for _, row in df2.iterrows():
            insert_value = (
                row['artist'],
                row['name'],
                row['artistOrigin'],
                row['releaseDate'],
                row['images'],
                row['allGenres'],
                row['streak'],
                row['rating'],
                row['globalRating'],
                row['review'],
                row['youtubeMusicId']
            )
            cur.execute(insert_script, insert_value)
            conn.commit()

        logging.info("Inserted data into 'albums' table.")

    except Exception as e:
        logging.error(f"Failed to load data to database: {e}")
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()


if __name__ == "__main__":

    df1, df2 = extract_music()
    transformed_df1, transformed_df2 = transform_music(df1, df2)
    load_music(transformed_df1, transformed_df2)
