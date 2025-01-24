import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
import matplotlib.pyplot as plt
from data_extraction import get_artist_info
import plotly.express as px
import seaborn as sns
from wordcloud import WordCloud

# Load environment variables
load_dotenv()

# Database connection parameters
host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")
database = os.getenv("DB_NAME")
user = os.getenv("DB_USER")
password = os.getenv("DB_PASS")

# Create database connection
connection_string = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
engine = create_engine(connection_string)

st.markdown(
    "<h1 style='color: #1DB954; font-size: 45px'>Spotify Artists and Their Popularity</h1>", 
    unsafe_allow_html=True
)

with st.expander("What is popularity?"):
    st.write("The popularity of a track is a value between 0 and 100, with 100 being the most popular. The popularity is calculated by algorithm and is based, in the most part, on the total number of plays the track has had and how recent those plays are.")
    st.write("The artist's popularity is calculated from the popularity of all the artist's tracks")

# Fetch data from database
query = "SELECT * FROM student.ak_spotify"
data = pd.read_sql(query, engine)

#duration_min_sec is in db as varchar. Have to convert to int in order to aggregate
duration_query = """
SELECT 
    artist_name, 
    artist_popularity, 
    AVG((SUBSTRING(duration_min_sec FROM '^([0-9]+):')::int * 60 + 
         SUBSTRING(duration_min_sec FROM ':([0-9]+)$')::int)) AS avg_song_length_seconds
FROM 
    student.ak_spotify
GROUP BY 
    artist_name, artist_popularity
ORDER BY 
    artist_popularity DESC;
"""
duration_data = pd.read_sql(duration_query, engine)


#----------------- SELECT VISUAL ------------------#

# Create a select box for choosing the visualization
visualization_option = st.selectbox(
    "Select a visualization:",
    [
        "Artist Popularity vs. Song Length",
        "Artist Popularity",
        "Song Popularity by Artist"
    ]
)

# Option 1: Scatter Plot
if visualization_option == "Artist Popularity vs. Song Length":
    st.subheader("Artist Popularity vs. Song Length")

    fig, ax = plt.subplots(figsize=(12, 8))

    scatter = ax.scatter(
        duration_data["avg_song_length_seconds"], 
        duration_data["artist_popularity"], 
        c=duration_data["artist_popularity"], 
        cmap="viridis", 
        s=100, 
        alpha=0.8
    )

    ax.set_title("Artist Popularity vs. Average Song Length", fontsize=16)
    ax.set_xlabel("Average Song Length (seconds)", fontsize=14)
    ax.set_ylabel("Artist Popularity", fontsize=14)

    for i, artist in duration_data.iterrows():
        ax.text(
            artist["avg_song_length_seconds"], 
            artist["artist_popularity"] + 0.5,  
            artist["artist_name"], 
            fontsize=10, 
            alpha=0.7
        )

    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label("Artist Popularity", fontsize=12)

    st.pyplot(fig)


# Option 2: Word Cloud
elif visualization_option == "Artist Popularity":
    st.subheader("Artist Popularity")

    artist_popularity = data.groupby("artist_name")["artist_popularity"].mean()
    wordcloud_data = artist_popularity.to_dict()

    wordcloud = WordCloud(
        width=1600, 
        height=800, 
        background_color="black", 
        colormap="viridis", 
        contour_color="white", 
        contour_width=1, 
        relative_scaling=0.5
    ).generate_from_frequencies(wordcloud_data)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.imshow(wordcloud, interpolation="bilinear")
    ax.axis("off")
    st.pyplot(fig)

# Option 3: Bubble Chart
elif visualization_option == "Song Popularity by Artist":
    st.subheader("Song Popularity by Artist")

    artist_popularity = data.groupby("artist_name")["song_popularity"].mean().reset_index()
    bubble_sizes = artist_popularity["song_popularity"] * 10

    fig, ax = plt.subplots(figsize=(15, 8))

    scatter = ax.scatter(
        artist_popularity["artist_name"], 
        artist_popularity["song_popularity"], 
        s=bubble_sizes, 
        alpha=0.6, 
        color="dodgerblue", 
        edgecolors="black", 
        linewidth=0.5
    )

    ax.set_title("Average Song Popularity by Artist", fontsize=18, color="black", pad=20)
    ax.set_xlabel("Artist", fontsize=14)
    ax.set_ylabel("Average Song Popularity", fontsize=14)
    ax.set_xticks(range(len(artist_popularity["artist_name"])))
    ax.set_xticklabels(artist_popularity["artist_name"], rotation=90, fontsize=10)
    ax.grid(True, linestyle="--", alpha=0.5)

    plt.tight_layout()
    st.pyplot(fig)

#--------------- Search For an Artist -----------------#

st.subheader("Enter the name of an artist to see their top tracks")
artist_name = st.text_input(" ")

#check input
if artist_name.strip():  
    try:
        # Fetch artist information and their songs
        artist_df = get_artist_info(artist_name)
        
        # Get the correct artist name from the dataframe
        if not artist_df.empty:
            correct_artist_name = artist_df["artist_name"].iloc[0]
            
            # Sort by song popularity
            artist_df = artist_df.sort_values(by="song_popularity", ascending=False)
            
            # Use Plotly for a horizontal bar chart
            fig = px.bar(
                artist_df,
                x="song_popularity",
                y="song_name",
                orientation="h",
                color="song_popularity",
                color_continuous_scale=px.colors.sequential.Viridis,
                title=f"Top Songs by {correct_artist_name}",
                labels={"song_name": "Song", "song_popularity": "Popularity"},
            )
            
            # Update layout for better visuals
            fig.update_layout(
                xaxis_title="Popularity",
                yaxis_title="Songs",
                title_font=dict(size=24, family="Arial", color="#1DB954"),  # Spotify's green color
                template="plotly_dark",  # Dark theme
            )
            
            st.plotly_chart(fig)
        else:
            st.write("No data found for the given artist.")
    except Exception as e:
        st.error(f"An error occurred: {e}")
else:
    st.write("Please enter an artist's name to see their most popular songs.")





