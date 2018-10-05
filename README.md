# zqsd_discord_bot
Discord bot for ZQSD server.

Requirements :
python 3.6 with :
	Discord api
	twitch api
	twitter api
	googlz api

DATABASE : SQLite3 named "keys.db"

CREATE TABLE "givekey" ( `key` INTEGER NOT NULL, `username` TEXT NOT NULL, given INTEGER DEFAULT 0, FOREIGN KEY(key) REFERENCES steamkeys(rowId) )
CREATE TABLE "steamkeys" ( `user` text, `platform` text, `game` text, `date` text, `counter` INTEGER, `rowId` INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE )
CREATE UNIQUE INDEX uq_givekey ON givekey("key", "username")
CREATE TABLE "twitter" ( `account` TEXT, `lastTweet` INTEGER )

CONFIG FILE : config.py with these parameters :


COMMAND_PREFIX = "!"
LOADED_EXTENSIONS = ["twitterCog", "keydonationCog", "twitchCog", "mixerCog"]

DISCORD_BOT_TOKEN = '<key>'

ANNONCE_CHANNEL_ID = '492772683327602688'
DONATION_CHANNEL_ID = '491651369103523840'

MIXER_API_KEY = '<key>'
TWITCH_API_KEY = '<key>'

MIXER_CHANNELS =  ["elodry"]
TWITCH_CHANNELS = [83473762, 177051, 59177051, 73708725, 24973468, 48170158]

GOOGLE_CLIENT_ID = '<key>'
GOOGLE_CLIENT_SECRET = '<key>'
GOOGLE_SPREADSHEET_ID = "1Scz3FbCW8abM3btJwe3qNH_1OekGk-DdMR11_7C51ZE"

TWITTER_CONSUMER_KEY = '<key>'
TWITTER_CONSUMER_SECRET = '<key>'
TWITTER_ACCESS_TOKEN = '<key>'
TWITTER_ACCESS_TOKEN_SECRET = '<key>'