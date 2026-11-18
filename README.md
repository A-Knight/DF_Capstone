## Project Overview

- Extract data about artists and their most popular songs from Spotify API
- Explore how different factors like genre, song length and region relate to song popularity
- Perform any necessary cleaning and transformation of data
- Load data into a database
- Visualize data

### Extraction Script Instructions

- Step 1. Install the required libraries

  > pip install -r requirements.txt

- Step 2. Run the extraction script

  > python data_extraction.py (For windows/linux)

- Step 3. Run the application
  > streamlit run app.py

---

### Author Note 17.11.26

- The access requirements to the spotify api have changed.
- Access to the db the data was being loaded into has been restricted.
- Consequently the Deezer API is now being used to fill its place however some functionality/visualisations may not be as originally implemented.
- Running the extraction script now outputs to a local csv
---
