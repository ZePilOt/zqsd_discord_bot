
import discord
from discord.ext import commands

from tweepy import OAuthHandler
from tweepy import API
from tweepy import Cursor
from datetime import datetime, date, time, timedelta
from collections import Counter
import asyncio

from zqsd_bot import cfg
import logging

CONF = cfg.CONF
LOG = logging.getLogger('bot')

 
class Twitter():
    def __init__(self, bot):
        self.bot = bot
        auth = OAuthHandler(CONF.TWITTER_CONSUMER_KEY, CONF.TWITTER_CONSUMER_SECRET)
        auth.set_access_token(CONF.TWITTER_ACCESS_TOKEN, CONF.TWITTER_ACCESS_TOKEN_SECRET)
        self.auth_api = API(auth)
        self.bot.loop.create_task(self.check_twitter())
        self.end_date = datetime.utcnow()

    async def check_twitter(self):
        await self.bot.wait_until_ready()
        channel = discord.Object(id=CONF.ANNONCE_CHANNEL_ID)

        for target in CONF.TWITTER_ACCOUNTS:   
 
            for status in Cursor(self.auth_api.user_timeline, id=target).items(10):

                if status.in_reply_to_status_id == None and hasattr(status, "retweeted_status") == False and status.created_at >= self.end_date:
                    link = "https://twitter.com/{}/status/{}".format(target, status.id_str)
                    await self.bot.send_message(channel, link)
                        #break

        self.end_date = datetime.utcnow()
        await asyncio.sleep(5*60)


def setup(bot):
    bot.add_cog(Twitter(bot))        