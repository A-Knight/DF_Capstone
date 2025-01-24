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