import math
import pandas as pd
from requests import get


def search_for_artist(artist_name):
    url = "https://api.deezer.com/search/artist"
    result = get(url, params={"q": artist_name, "limit": 1})

    if result.status_code != 200:
        print(f"Search failed for {artist_name} ({result.status_code})")
        return None

    items = result.json().get("data", [])
    if not items:
        print(f"No artist with this name exists: {artist_name}")
        return None

    return items[0]


def get_songs_by_artist(artist_id):
    url = f"https://api.deezer.com/artist/{artist_id}/top"
    result = get(url, params={"limit": 10})

    if result.status_code != 200:
        print(f"Top-tracks failed ({result.status_code})")
        return []

    return result.json().get("data", [])


def convert_sec_to_min_sec(df):
    df["duration_min_sec"] = df["duration_sec"].apply(
        lambda x: f"{int(x) // 60}:{int(x) % 60:02d}"
    )
    df.drop(columns=["duration_sec"], inplace=True)
    return df


def scale_to_100(value, max_reference):
    """Normalizes raw fan/rank counts onto a 0-100 popularity scale."""
    if not value or value <= 0:
        return 0
    score = (math.log10(value) / math.log10(max_reference)) * 100
    return min(100, max(1, round(score)))


def get_artist_info(artist_name):
    artist_info = search_for_artist(artist_name)
    if artist_info is None:
        return None

    artist_id = artist_info["id"]
    resolved_name = artist_info["name"]
    # Scale Deezer fan count (~10M+ fans -> ~100) to match Spotify's 0-100 popularity scale
    artist_popularity = scale_to_100(artist_info.get("nb_fan", 0), max_reference=15_000_000)

    song_info = get_songs_by_artist(artist_id)
    if not song_info:
        return None

    all_info = []
    for song in song_info:
        all_info.append({
            "artist_id": artist_id,
            "artist_name": resolved_name,
            "artist_popularity": artist_popularity,
            "song_id": song["id"],
            "song_name": song["title"],
            # Scale Deezer track rank (~1M+ -> ~100) to a 0-100 popularity score
            "song_popularity": scale_to_100(song.get("rank", 0), max_reference=1_000_000),
            "duration_sec": song["duration"]
        })

    artist_df = pd.DataFrame(all_info)
    return convert_sec_to_min_sec(artist_df)


if __name__ == "__main__":
    with open("utils/artist_list.txt", "r") as file:
        artists = list(dict.fromkeys(
            line.strip().replace("-", " ") for line in file if line.strip()
        ))

    all_artists_data = []
    for artist_name in artists:
        try:
            artist_data = get_artist_info(artist_name)
            if artist_data is not None and not artist_data.empty:
                all_artists_data.append(artist_data)
                print(f"Fetched: {artist_data['artist_name'].iloc[0]}")
        except Exception as e:
            print(f"An error occurred for artist {artist_name}: {e}")

    if all_artists_data:
        final_df = pd.concat(all_artists_data, ignore_index=True)
        final_df.to_csv("spotify_data.csv", index=False)
        print(f"\nSaved {len(final_df)} rows to spotify_data.csv successfully!")
    else:
        print("No data was retrieved.")

