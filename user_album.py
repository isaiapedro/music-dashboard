import pandas as pd
import logging
import requests
import datetime

file = open("log.txt", "a")
file.write(f"User Task executed at {datetime.datetime.now()}\n")
file.close()

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def extract_music(PROJECT_ID):
    """
    Extracts data from the API and returns it as a DataFrame.
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

    logging.info("Data extracted and saved to JSON files successfully.")

    return current, albums_df


def transform_music(current, albums_df):
    """
    Applies transformations to the data pulled from XComs.
    """
    logging.info("Transforming data...")
    df1 = current
    df2 = albums_df
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


def load_music(project_name):
    """
    Loads transformed data into a PostgreSQL database.
    """

    PROJECT_ID = project_name.lower().replace(" ", "-")

    try:
        logging.info(f"Starting ETL process for project: {project_name}")
        current, albums_df = extract_music(PROJECT_ID)
        logging.info("Extracted data successfully.")
    except Exception as e:
        logging.error(f"Failed to extract data for project: {project_name}. Error: {e}")
        return

    try:
        logging.info("Transforming data...")
        df1, df2 = transform_music(current, albums_df)
    except Exception as e:
        logging.error(f"Failed to transform data. Error: {e}")
        return

    try:
        logging.info(f"Loading {len(df1 + df2)} rows into application project")
        return df1, df2
    except Exception as e:
        logging.error(f"Failed to load data into application project. Error: {e}")
