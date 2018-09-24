
import discord
from discord.ext import commands

from tweepy import OAuthHandler
from tweepy import API
from tweepy import Cursor
from datetime import datetime, date, time, timedelta
from collections import Counter
import asyncio
import requests
from zqsd_bot import cfg
import logging

CONF = cfg.CONF
LOG = logging.getLogger('bot')

class Channel():
	def __init__(self, channelid):
		self.uid = channelid
		self.online = False

class Mixer():
	def __init__(self, bot):
		self.bot = bot
		self.init = True
		self.channels = []
		for mixer_chan_id in CONF.MIXER_CHANNELS:
			self.channels.append(Channel(mixer_chan_id))
		
		self.bot.loop.create_task(self.check_mixer())

	async def check_mixer(self):
		await self.bot.wait_until_ready()
		while not self.bot.is_closed:
			discord_channel = discord.Object(id=CONF.ANNONCE_CHANNEL_ID)
			for channel in self.channels:
				s = requests.Session()
				s.headers.update({'Client-ID': CONF.MIXER_API_KEY})
				
				channel_id = channel.uid
				channel_response = s.get('https://mixer.com/api/v1/channels/{}'.format(channel_id))
				
				stream = channel_response.json()
				if stream["online"] == False:
					channel.online = False
				else:
					if channel.online == False:
						
						stream_game = stream["type"]["name"]
						stream_url = "https://mixer.com/{}".format(channel_id)
						stream_name = stream["token"]
						stream_title = stream["name"]
						discord_message = ""
						if "factor" in stream_name.lower():
							discord_message = "Mes créateurs, les gens de Factornews, sont maintenant live sur {} ! @here".format(stream_game)
						else:
							discord_message = "{} est maintenant live sur {} ! @here".format(stream_name, stream_game)
						stream_description = stream["description"]
						stream_preview = None
						if stream["type"]["coverUrl"]:
							stream_preview = stream["type"]["coverUrl"]
							stream_preview = stream_preview.replace('./', '')
						if stream["thumbnail"]:
							stream_logo = stream["thumbnail"]["url"]
							stream_logo = stream_logo.replace('./', '')

						if self.init == False:
							embed = discord.Embed(title=stream_title, description=stream_description, url=stream_url, color=0x6441a4)

							embed.add_field(name = "Followers", value = stream["numFollowers"])
							embed.add_field(name = "Views", value = stream["viewersTotal"])
							if stream["thumbnail"]:
								embed.set_thumbnail(url=stream_logo)
							if stream_preview:	
								embed.set_image(url=stream_preview)
							await self.bot.send_message(discord_channel, discord_message, embed=embed)
						
						channel.online = True

				await asyncio.sleep(5)

			self.init = False
			await asyncio.sleep(40)




def setup(bot):
	bot.add_cog(Mixer(bot)) 	 	