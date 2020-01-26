# Name_The_Tune_bot
Another telegram game bot, this time the goal is to guess the artist by using part of the song lyrics

You can play it here @namethetune_game_bot
At the moment only Russian version available.

I got the lyrics via scraping with BeautifulSoup mostly genuis.com (notebook in Scraping repo). 
List of tracks was obtained from billboard charts. 
Main feature is a leaderboard with an option to change username and refuse/accept to participate at any moment.

Game data stored in Postgres database, provided by Heroku. The bot itself is deployed also using Heroku services.
