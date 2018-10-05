
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

import sqlite3


CONF = cfg.CONF
LOG = logging.getLogger('bot')

 
class Twitter():
    def __init__(self, bot):
        self.bot = bot
        auth = OAuthHandler(CONF.TWITTER_CONSUMER_KEY, CONF.TWITTER_CONSUMER_SECRET)
        auth.set_access_token(CONF.TWITTER_ACCESS_TOKEN, CONF.TWITTER_ACCESS_TOKEN_SECRET)
        self.auth_api = API(auth)

        self.mostRecents = {}

        conn = sqlite3.connect('keys.db')
        c = conn.cursor()
        
        c.execute("SELECT * FROM twitter")
        results = c.fetchall()

        if len(results) == 0:
            conn.close()
            return

        for result in results:
            LOG.info("Adding twitter user " + result[0])
            self.mostRecents[result[0]] = result[1]

        conn.close()

        self.bot.loop.create_task(self.check_twitter())

    async def check_twitter(self):

        await self.bot.wait_until_ready()


        channel = discord.Object(id=CONF.ANNONCE_CHANNEL_ID)

        for target in self.mostRecents:   
            LOG.debug("checking account " + target)
            tweets = Cursor(self.auth_api.user_timeline, id=target, since_id = self.mostRecents[target], tweet_mode="extended")
            
            for status in tweets.items():
                if status.in_reply_to_status_id == None and hasattr(status, "retweeted_status") == False :
                    link = "https://twitter.com/{}/status/{}".format(target, status.id_str)
                    embed = discord.Embed(title=target, description=status.full_text, url=link, color=0x1DA1F2)
                    if "media" in status.entities:
                        for media in status.entities["media"]:
                            embed.set_image(url=media["media_url"])
                            break
                    
                    embed.set_thumbnail(url=status.user.profile_image_url)
                    embed.set_footer(text=status.created_at)
                    await self.bot.send_message(channel, embed=embed)


                if status.id > self.mostRecents[target]:
                    self.mostRecents[target] = status.id
                    conn = sqlite3.connect('keys.db')
                    c = conn.cursor()
                    args = (status.id, target)
                    c.execute("UPDATE twitter SET lastTweet = ? WHERE account = ?", args )
                    conn.commit()
                    conn.close()


        await asyncio.sleep(5*60)


def setup(bot):
    bot.add_cog(Twitter(bot))        