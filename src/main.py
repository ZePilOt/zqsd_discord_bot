#!/usr/bin/python

import argparse
import sys

import logging 

from zqsd_bot import cfg
from zqsd_bot import log
from zqsd_bot import utils
from discord.ext import commands
from discord.ext.commands import Bot

CONF = cfg.CONF

parser = argparse.ArgumentParser("Start the Discord bot")
parser.add_argument('--config-file', '-c', dest='config_file', default=f"config.py", help="Bot configuration file")
parser.add_argument('--log-dir', '-l', dest='log_dir',
					default=f"./logs/{utils.get_project_name()}/", help="Bot log folder")


async def list_servers(bot):
	LOG = logging.getLogger('bot')
	await bot.wait_until_ready()
	LOG.debug("Current servers:")
	for server in bot.servers:
		LOG.debug("connected to {} ".format(server))


def main():

	args = parser.parse_args()
	log.setup(args.log_dir, args.config_file)
	LOG = logging.getLogger('bot')
	CONF.load(args.config_file)

	sys.path.append(utils.get_project_name())

	bot = Bot(command_prefix=CONF.COMMAND_PREFIX, pm_help=True)

	LOG.info("bot config : " + args.config_file)

	for extension in CONF.LOADED_EXTENSIONS: 
		try:
			extension_module_name = f"{utils.get_project_name()}.cogs" 
			bot.load_extension(extension_module_name + "." + extension)
			LOG.info(f"The extension '{extension.split('.')[0]}' has been successfully loaded")
		except:
			LOG.exception(f"Failed to load extension '{extension.split('.')[0]}'")	 	

	bot.loop.create_task(list_servers(bot))
	bot.loop.run_until_complete(bot.start(CONF.DISCORD_BOT_TOKEN))



if __name__ == "__main__":
	main()
