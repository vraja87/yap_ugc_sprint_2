# Test Results Comparison: MongoDB vs Postgresql

## Overview
Even on small amounts of data, MongoDB demonstrates higher read speeds,
while increasing data volumes, MongoDB also continues to show good reading and aggregation results,
while maintaining compliance with the 200 ms requirement.

### MongoDb results:
Total Insertion Time: 0:06:44.340743<br>
 - **get_bookmarked_films_by_user**<br>
min `3.74` ms max `11.72` ms avg `4.88` ms<br>
- **get_liked_films_by_user**<br>
min `3.83` ms max `6.12` ms avg `4.64` ms<br>
- **get_average_film_rating**<br>
min `23.97` ms max `33.75` ms avg `26.45` ms<br>
 - **get_likes_dislikes_count**<br>
min `25.01` ms max `40.41` ms avg `27.53` ms<br><br>
Tests under load. Insert like, and check it's appearence:
- **get_likes_dislikes_count**<br>
min `36.83` ms max `86.03` ms avg `55.06` ms<br>
- **get_liked_films_by_user**<br>
min `5.08` ms max `18.29` ms avg `9.00` ms<br>


### Postgresql results:
Total Insertion Time: 0:00:09.930405<br>
 - **get_bookmarked_films_by_user**<br>
min `40.33` ms max `63.53` ms avg `44.97` ms<br>
 - **get_liked_films_by_user**<br>
min `39.94` ms max `51.59` ms avg `43.68` ms<br>
 - **get_average_film_rating**<br>
min `40.79` ms max `62.33` ms avg `45.38` ms<br>
 - **get_likes_dislikes_count**<br>
min `45.08` ms max `58.63` ms avg `49.42` ms<br><br>
Tests under load. Insert like, and check it's appearence:
 - **get_likes_dislikes_count**<br>
min `48.92` ms max `99.62` ms avg `63.46` ms<br>
 - **get_liked_films_by_user**<br>
min `44.68` ms max `93.88` ms avg `55.56` ms<br>


### Test procedure: 
 The tests are conducted locally. Dependencies need to be installed. mongo .env addresses must be `localhost` for tests.
 - `docker-compose up -d --build`
 - `bash init_mongo_db.sh`
 - `python main_test.py`
 - `docker-compose down -v`
