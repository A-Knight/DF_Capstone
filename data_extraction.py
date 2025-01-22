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

token = get_token()

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

token = get_token()
result = search_for_artist(token, "Bruno-Mars")

# print(result)
artist_id = result["id"]

# print(artist_id)
# print(result["name"])
songs = get_songs_by_artist(token, artist_id)
# print(songs)

# for idx, song in enumerate(songs):
#     print(f"{idx + 1}. {song['name']}")

#------------------------------------------------------------------

# df = pd.DataFrame(songs)
# df2 = pd.DataFrame(result)
df1 = pd.DataFrame(songs)

# Select only the 'id', 'name', and 'popularity' columns
filtered_df = df1[['id', 'name', 'popularity', 'duration_ms']]

# Display the filtered DataFrame
filtered_df

#--------------------------------------------------------------------

# List of artists
artists = ["Asake","Burna-Boy","Jungle","Kendrick-Lamar", "SZA","Dexta-Daps", "JID","Teddy-Swims", "Bruno-Mars", "Lady-Gaga", "Coldplay", "Taylor-Swift", "Bad-Bunny", "The-Weeknd", "Billie-Eilish", "Ariana-Grande", "Drake", "Rihanna", "Ed-Sheeran", "Sabrina-Carpenter", "Justin-Bieber", "Ariana-Grande", "Eminem", "Kanye-West", "Post-Malone", "BTS", "Travis-Scott"]

# Initialize an empty list to store data for all artists
all_songs_data = []

# Iterate over each artist in the list
for artist_name in artists:
    try:
        # Search for the artist
        result = search_for_artist(token, artist_name)
        if result is None:
            print(f"No data found for artist: {artist_name}")
            continue
        
        # Get the artist ID and name
        artist_id = result["id"]
        artist_name = result["name"]  # This extracts the correct name of the artist
        artist_popularity = result["popularity"]
        
        # Fetch the top tracks for the artist
        songs = get_songs_by_artist(token, artist_id)
        
        # Append relevant data from the songs to the list
        for song in songs:
            all_songs_data.append({
                "id": song["id"],
                "artist_name": artist_name,  # Add the artist's name to each song entry
                "artist_popularity": artist_popularity,
                "song_name": song["name"],
                "song_popularity": song["popularity"],
                "duration_ms": song["duration_ms"]
                
            })
    except Exception as e:
        print(f"An error occurred for artist {artist_name}: {e}")

# Convert the collected data into a DataFrame
final_df = pd.DataFrame(all_songs_data)

# Display the DataFrame
# final_df

#-------------------------------------------------------


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

# Write the DataFrame to the database in the 'student' schema
table_name = "ak_spotify"  # Desired table name
final_df.to_sql(
    table_name,
    engine,
    schema="student",
    if_exists="replace",  # Options: 'fail', 'replace', 'append'
    index=False  # Do not write the DataFrame index as a column
)