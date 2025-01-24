import pandas as pd 
from dotenv import load_dotenv
import os 
import base64
from requests import post, get
import json
import psycopg2
from sqlalchemy import create_engine

#load the environment variables
load_dotenv()

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

#Test they have been loaded correctly
# print(client_id, client_secret)

#-------------------------------------------------------------------
# Uses client credentials to request access token
def get_token():
    auth_info = client_id + ":" + client_secret
    auth_bytes = auth_info.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")
    
    base_url = "https://accounts.spotify.com/api/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": "Basic " + auth_base64
    }
    data = {"grant_type": "client_credentials"}
    result = post(base_url, headers=headers, data=data)
    json_result = json.loads(result.content)
    token = json_result["access_token"]
    return token

# token = get_token()

# Show access token received from spotify
# print(token)
#-------------------------------------------------------------------

#Forms header for whenever we send requests
def get_header(token):
    return {"Authorization": "Bearer " + token}

#-------------------------------------------------------------------
def search_for_artist(token, artist_name):
    url = "https://api.spotify.com/v1/search"
    headers = get_header(token)
    query = f"?q={artist_name}&type=artist&limit=1"
    
    query_url = url + query
    
    result = get(query_url, headers=headers)
    # print(f"Raw response for {artist_name}: {result.content}")  # Debugging line
    try:
        json_result = json.loads(result.content)
    except Exception as e:
        print(f"Error parsing JSON for {artist_name}: {e}")
        return None

    # Check for errors in the JSON response
    if "error" in json_result:
        print(f"API returned an error for {artist_name}: {json_result['error']}")
        return None
    
    # Extract the "artists" key
    json_result = json_result.get("artists", {}).get("items", [])
    
    if len(json_result) == 0:
        print(f"No artist with this name exists: {artist_name}")
        return None
    
    return json_result[0]
#----------------------------------------------------------------

def get_songs_by_artist(token, artist_id):
    url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks?country=US"
    headers = get_header(token)
    result = get(url, headers=headers)
    json_result = json.loads(result.content)["tracks"]
    return json_result

#----------------------------------------------------------------

#Convert song duration from milliseconds to minutes:seconds
def convert_mil_to_sec(df):
    # Transform duration_ms into minutes and seconds (duration_min_sec)
    df["duration_min_sec"] = df["duration_ms"].apply(lambda x: f"{x // 60000}:{(x % 60000) // 1000:02d}")

    # Drop the original duration_ms column 
    df.drop(columns=["duration_ms"], inplace=True)
    
    return df

#----------------------------------------------------------------

#Construct Dataframe for an individual artist
def get_artist_info(artist_name):
    token = get_token()
    artist_info = search_for_artist(token, artist_name)
    artist_id = artist_info["id"]
    artist_name = artist_info["name"]
    artist_popularity = artist_info["popularity"]
    song_info = get_songs_by_artist(token, artist_id)
    
    all_info = []
    
    # Iterate through all songs
    for song in song_info:
        all_info.append({
            "artist_id": artist_id,
            "artist_name": artist_name,  
            "artist_popularity": artist_popularity,
            "song_id": song["id"],
            "song_name": song["name"],
            "song_popularity": song["popularity"],
            "duration_ms": song["duration_ms"]
        })
    
    artist_df = pd.DataFrame(all_info)
    all_info_df = convert_mil_to_sec(artist_df)
    return all_info_df

#------------------------------------------------------------------#

# List of artists
artists = ["Asake","Burna-Boy","Jungle","Kendrick-Lamar", "SZA","Dua-Lipa", "JID","Teddy-Swims", "Bruno-Mars", "Lady-Gaga", "Coldplay", "Taylor-Swift", "Bad-Bunny", "The-Weeknd", "Billie-Eilish", "Ariana-Grande", "Drake", "Rihanna", "Ed-Sheeran", "Sabrina-Carpenter", "Justin-Bieber", "Ariana-Grande", "Eminem", "Kanye-West", "Post-Malone", "BTS", "Travis-Scott", "Doechii", "Imagine-Dragons", "J-Balvin", "Green-Day", "GloRilla", "Childish-Gambino", "Whitney-Houston", "Linkin-Park", "Donna-Summer"]

# Initialize an empty list to store data for all artists
all_artists_data = []

# List of artists used to search api. Info returned used to create dataframe
# Iterate over each artist in the list
for artist_name in artists:
    try:
        # Use the get_artist_info function to retrieve and process artist data
        artist_data = get_artist_info(artist_name)
        all_artists_data.append(artist_data)  
    except Exception as e:
        print(f"An error occurred for artist {artist_name}: {e}")

# Combine all artist DataFrames into one
if all_artists_data:  
    final_df = pd.concat(all_artists_data, ignore_index=True)
else:
    final_df = pd.DataFrame()  # Create an empty DataFrame if no data was retrieved

# Display the final DataFrame
# print(final_df)

#----------------- Load Data into Database ------------------#

# Load environment variables from the .env file
load_dotenv()

# Database connection parameters
host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")
database = os.getenv("DB_NAME")
user = os.getenv("DB_USER")
password = os.getenv("DB_PASS")

# Create the connection string
connection_string = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"

# Create an SQLAlchemy engine
engine = create_engine(connection_string)

# Write the DataFrame to the pagila database in the 'student' schema
table_name = "ak_spotify"  
final_df.to_sql(
    table_name,
    engine,
    schema="student",
    if_exists="replace",  
    index=False  
)

#--------------------------------------------------------------------------#
    
    
    