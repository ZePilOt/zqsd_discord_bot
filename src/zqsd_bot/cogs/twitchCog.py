
import discord
from discord.ext import commands

from tweepy import OAuthHandler
from tweepy import API
from tweepy import Cursor
from datetime import datetime, date, time, timedelta
from collections import Counter
import asyncio
from twitch import TwitchClient

from zqsd_bot import cfg
import logging

CONF = cfg.CONF
LOG = logging.getLogger('bot')

class Channel():
	def __init__(self, channelid):
		self.uid = channelid
		self.online = False

class Twitch():
	def __init__(self, bot):
		self.bot = bot
		self.init = True
		self.client = TwitchClient(client_id = CONF.TWITCH_API_KEY)

		self.channels = []
		for twitch_chan_id in CONF.TWITCH_CHANNELS:
			self.channels.append(Channel(twitch_chan_id))

		self.bot.loop.create_task(self.check_twitch())



	async def check_twitch(self):
		await self.bot.wait_until_ready()
		while not self.bot.is_closed:
			discord_channel = discord.Object(id=CONF.ANNONCE_CHANNEL_ID)
			for channel in self.channels:
				
				channel_id = channel.uid
				stream = self.client.streams.get_stream_by_user(channel_id)
				if stream == None:
					channel.online = False
				else:
					if channel.online == False:
						
						stream_game = stream["game"]
						stream_url = stream["channel"]["url"]
						stream_name = stream["channel"]["display_name"]
						stream_title = stream["channel"]["status"]
						discord_message = ""
						if "factor" in stream_name.lower():
							discord_message = "Mes créateurs, les gens de Factornews, sont maintenant live sur {} ! @here".format(stream_game)
						else:
							discord_message = "{} est maintenant live sur {} ! @here".format(stream_name, stream_game)
						stream_description = stream["channel"]["description"]

						stream_preview = stream["preview"]["large"]
						stream_preview = stream_preview.replace('./', '')
						stream_logo = stream["channel"]["logo"]
						stream_logo = stream_logo.replace('./', '')

						if self.init == False:
							embed = discord.Embed(title=stream_title, description=stream_description, url=stream_url, color=0x6441a4)

							embed.add_field(name = "Followers", value = stream["channel"]["followers"])
							embed.add_field(name = "Views", value = stream["channel"]["views"])
							embed.set_thumbnail(url=stream_logo)
							embed.set_image(url=stream_preview)

							await self.bot.send_message(discord_channel, discord_message, embed=embed)
						
						channel.online = True

				await asyncio.sleep(5)

			self.init = False
			await asyncio.sleep(40)




def setup(bot):
 	bot.add_cog(Twitch(bot)) 	 	