import discord
from discord.ext import commands		
import sqlite3
import re
import asyncio
import random
from zqsd_bot import cfg
import logging

CONF = cfg.CONF
LOG = logging.getLogger('bot')

# If modifying these scopes, delete the file token.json.
SCOPES = 'https://www.googleapis.com/auth/spreadsheets'

from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools

class DonationDeCle():
	'''
	Gere les donations de clé
	'''
	def __init__(self, bot):
		self.bot = bot
		self.init = True
		self.users = {}

		#self.bot.loop.create_task(self.update_google_doc())
		self.bot.loop.create_task(self.announce_game())
		self.bot.loop.create_task(self.announce_liste())
		self.bot.loop.create_task(self.bother_to_give())


	@commands.command(pass_context=True)
	async def listecle(self, ctx):
		'''
		Comme son nom l'indique...
		'''
		await self.bot.whisper("La liste, elle est dans ton coeur, et ici : https://docs.google.com/spreadsheets/d/1Scz3FbCW8abM3btJwe3qNH_1OekGk-DdMR11_7C51ZE/view#gid=0")

	@commands.command(pass_context=True)
	async def donnemoilacle(self, ctx, platform: str, de:str, username:str, pour:str, game:str, steple:str):
		'''
		Prenez donc une clé, c'est gratuit !donnemoilacle [steam] de [machin] pour [jeu] steuplé
		'''			

		member = ctx.message.author
		platform = platform.lower()
		conn = sqlite3.connect('keys.db')
		c = conn.cursor()
		c.execute("PRAGMA foreign_keys = ON;")

		args = (platform.lower(), "%"+game.lower()+"%")
		c.execute("SELECT rowId, user, counter FROM steamkeys WHERE lower(platform) = ? and lower(game) LIKE ? and counter >= 1", args)
		selected = c.fetchall()
		if len(selected) == 0:
			await self.bot.whisper('Désolé, je n\'ai trouvé aucune clé {} pour le jeu {}'.format(platform, game))
			conn.close()
			return

		giver = None
		idGame = None
		counterKey = 0
		for row in selected:
			giver = await self.bot.get_user_info(row[1])
			if str(giver) == username:
				idGame = row[0]
				counterKey = row[2]
				break

		if idGame == None:
			await self.bot.whisper('Désolé, je n\'ai trouvé aucune clé {} donnée par {} pour le jeu {}'.format(platform, username, game))
			conn.close()
			return		

		#check that there is no donation in progress for this key.
		args = (idGame,)
		c.execute("SELECT COUNT(*) FROM givekey WHERE givekey.key = ? AND givekey.given = 0", args)
		result = c.fetchone()
		if result[0] >= counterKey:
			await self.bot.whisper('Désolé, toutes les clés disponibles de {} pour le jeu {} sont déjà demandées.'.format(platform, username, game))
			conn.close()
			return


		args = (idGame, str(member.id))
		try:
			c.execute("INSERT INTO givekey VALUES (?,?,0)", args)   
			conn.commit()
		
		except sqlite3.IntegrityError as e:
			if str(e).startswith("FOREIGN KEY"):
				await self.bot.whisper('Une erreur fatale ! C\'est pas de votre faute, mais je n\'ai pas retrouvé le jeu dans ma liste.')
				conn.close()
				return
			elif str(e).startswith("UNIQUE"):
				await self.bot.whisper('La demande a déjà été faite. Il faut être patient monsieur !')
				conn.close()
			return

		args = (idGame,)
		#c.execute("UPDATE steamkeys SET counter = counter-1 WHERE rowId = ?", args )
		#conn.commit()
		await self.bot.whisper('La demande a bien été prise en compte. J\'avertis {} que vous désirez la clé !'.format(username))


		await self.bot.send_message(giver, "<@{}> désire votre clé {} pour {}.\nUne fois donnée, merci de taper la commande suivante : \n!don de {} sur {} a {}\nSinon je vais continuer à vous embêter avec ce message. En cas de refus de don, même commande, et vous vous demerdez avec {}, je suis pas votre père.".format(str(member.id), platform, game, game, platform, str(member), member.name))



		conn.close()

	@donnemoilacle.error
	async def donnemoilacle_error(self, error, ctx):
		LOG.error(error) 
		
		await self.bot.whisper('Veuillez taper la commande\n !donnemoilacle [plateforme] de [machin] pour [jeu] steuplé')
    


	async def update_google_doc(self):
		await self.bot.wait_until_ready()
		LOG.info("updating google doc")
		service = None
		store = file.Storage('token.json')
		creds = store.get()
		if not creds or creds.invalid:
			flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
			creds = tools.run_flow(flow, store)
		
		service = build('sheets', 'v4', http=creds.authorize(Http()))

		# The A1 notation of the values to clear.
		range_ = 'Keys!A3:Z' 
		clear_values_request_body = {
		}

		request = service.spreadsheets().values().clear(spreadsheetId=CONF.GOOGLE_SPREADSHEET_ID, range=range_, body=clear_values_request_body)
		response = request.execute()


		conn = sqlite3.connect('keys.db')
		c = conn.cursor()
		c.execute("SELECT steamkeys.user, steamkeys.platform, steamkeys.game, steamkeys.date, steamkeys.counter, steamkeys.rowId FROM steamkeys WHERE (SELECT COUNT(*) FROM givekey WHERE givekey.key = steamkeys.rowId AND givekey.given = 0) < steamkeys.counter ORDER BY steamkeys.game")
		results = c.fetchall()
		if len(results) == 0:
			conn.close()
			return

		else:
			LOG.debug("updating with" + str(len(results)) + "values")

		
		values = []


		for result in results:
			counterKey = result[4] 
			#check that there is no donation in progress for this key.
			args = (result[5], )
		
			if not result[0] in self.users:
				giver = await self.bot.get_user_info(result[0])
				self.users[result[0]] = giver

			gameName = await self.parse_game_name(result[2])
			if gameName == None:
				continue
			LOG.info("adding" + gameName)
			cmd = "!donnemoilacle {} de {} pour {} steuplé".format(result[1], str(self.users[result[0]]), gameName)

			values.append( [ str(self.users[result[0]]), result[1], gameName, result[2], result[4], result[3], cmd ] )

		

		range_name = "Keys!A3:G" + str(len(values)+2)

		body = {
			'values': values
		}

		service.spreadsheets().values().update(spreadsheetId=CONF.GOOGLE_SPREADSHEET_ID, range=range_name, valueInputOption='RAW', body=body).execute()

		conn.close()

	@commands.group(pass_context=True)
	async def donnecle(self, ctx):
		'''
		Donne une clé à la communauté. Fais revenir l'être aimé.
		'''	
		if ctx.invoked_subcommand is None:
			await self.bot.whisper('Plate forme inconnue...\nVeuillez taper la commande\n "!donnecle [plateforme] [lien store]\n Par exemple :\n!donnecle steam https://store.steampowered.com/app/346010/Besiege/\nPlate-forme reconnue : steam, gog')

	@donnecle.command(pass_context=True)
	async def gog(self, ctx, game: str):
		if game.startswith("https://www.gog.com/game") == False:
			await self.bot.whisper('Merci de me donner le lien du store gog pour votre jeu ! Par exemple :\n!donnecle gog https://www.gog.com/game/divinity_original_sin_2_divine_edition')
			member = ctx.message.author
			platform = "gog"
			await self.add_key_to_db(member, platform, game)
			await self.bot.whisper('Votre clé cherche désormais un maître. Merci !')


	@donnecle.command(pass_context=True)
	async def steam(self, ctx, game: str):

		if game.startswith("https://store.steampowered.com/app") == False:
			await self.bot.whisper('Merci de me donner le lien du store steam pour votre jeu ! Par exemple :\n!donnecle steam https://store.steampowered.com/app/346010/Besiege/')
		else:
			member = ctx.message.author
			platform = "steam"
			await self.add_key_to_db(member, platform, game)
			await self.bot.whisper('Votre clé cherche désormais un maître. Merci !')

	async def add_key_to_db(self, member, platform, gameurl):

			conn = sqlite3.connect('keys.db')
			c = conn.cursor()
			
			args = (platform.lower(), gameurl.lower())
			c.execute("SELECT rowId FROM steamkeys WHERE platform = ? and lower(game) = ? LIMIT 1", args)

			selected = c.fetchone()
			if selected != None:
				args = (selected[0],)
				c.execute("UPDATE steamkeys SET counter = counter+1, date = datetime('now') WHERE rowId = ?", args )
			else:
				args = (str(member.id), platform.lower(), gameurl.lower())
				c.execute("INSERT INTO steamkeys VALUES (?, ?, ?, datetime('now'), 1, NULL)", args)
			
			conn.commit()
			conn.close()
			await self.update_google_doc()
			await self.post_announce(gameurl, platform, member)


	@gog.error
	async def donnecle_error(self, error, ctx): 
		LOG.error(error)
		await self.bot.whisper('Veuillez taper la commande\n "!donnecle [gog] [lien store]\n Par exemple :\n!donnecle gog https://www.gog.com/game/divinity_original_sin_2_divine_edition')

	@steam.error
	async def donnecle_error(self, error, ctx): 
		LOG.error(error)
		await self.bot.whisper('Veuillez taper la commande\n "!donnecle [steam] [lien store]\n Par exemple :\n!donnecle steam https://store.steampowered.com/app/346010/Besiege/')


	@commands.command(pass_context=True)
	async def update(self, ctx):	 
		'''
		Met à jour le google doc
		'''	
		member = ctx.message.author
		if str(member.id) == "182381180941893632":
			await self.bot.whisper("Updating google doc")
			await self.update_google_doc()
			await self.bot.whisper("Done")
		else:
			await self.bot.whisper("Tu n\'es pas mon maître !")

	@commands.command(pass_context=True)
	async def don(self, ctx, de: str, game:str, sur:str, platform:str, a:str, destination:str):
		'''
		!don de [Jeu] sur [Plateforme] a [machin] Valide une donation (ou retire la clé de la liste de clé)
		'''		
		member = ctx.message.author
		conn = sqlite3.connect('keys.db')
		c = conn.cursor()
		c.execute("PRAGMA foreign_keys = ON;")
		args = (str(member.id), platform.lower(), "%"+game.lower()+"%")

		c.execute("SELECT givekey.rowid, steamkeys.rowid, givekey.username FROM givekey INNER JOIN steamkeys ON givekey.key=steamkeys.rowId WHERE counter >= 1 AND steamkeys.user = ? AND steamkeys.platform = ? AND lower(steamkeys.game) LIKE ?", args)
		result = c.fetchall()
		
		given = False

		if len(result) != 0:
			for row in result:
				giver = await self.bot.get_user_info(row[2])
				
				if str(giver) == destination:
					args = (row[1],)
					c.execute("UPDATE steamkeys SET counter = counter-1 WHERE rowId = ?", args )
					conn.commit()
					args = (row[0],)
					c.execute("UPDATE givekey SET given = 1 WHERE rowid = ?", args )
					conn.commit()
					given = True
					channel = discord.Object(id=CONF.DONATION_CHANNEL_ID)
					await self.bot.send_message(channel, "Une clé {} pour {} a trouvé un nouveau maître ! Gloire à {} !".format(platform, game, member.name))
					await self.bot.send_message(giver, "Votre demande de clé {} pour {} a été accepté par {}. Bon jeu !".format(platform, game, member.name))
					await self.update_google_doc()

					break

		if given == False:
			await self.bot.whisper('Désolé, je n\'ai trouvé aucune donation en cours de votre part pour le jeu {} à {}'.format(game, destination))
		else:
			await self.bot.whisper('Confirmation du don. Puisse ce geste vous donner fortune.')
		conn.close()


	@commands.command(pass_context=True)
	async def refusedon(self, ctx, de: str, game:str, sur:str, platform:str, a:str, destination:str):
		'''
		!refusedon de [Jeu] sur [Plateforme] a [machin] Invalide une donation
		'''		
		member = ctx.message.author
		conn = sqlite3.connect('keys.db')
		c = conn.cursor()
		c.execute("PRAGMA foreign_keys = ON;")
		args = (str(member.id), platform.lower(), "%"+game.lower()+"%")

		c.execute("SELECT givekey.rowid, steamkeys.rowid, givekey.username FROM givekey INNER JOIN steamkeys ON givekey.key=steamkeys.rowId WHERE counter >= 1 AND steamkeys.user = ? AND steamkeys.platform = ? AND lower(steamkeys.game) LIKE ?", args)
		result = c.fetchall()
		
		given = False

		if len(result) != 0:
			for row in result:
				giver = await self.bot.get_user_info(row[2])
				
				if str(giver) == destination:
					args = (row[0],)
					c.execute("UPDATE givekey SET given = 1 WHERE rowid = ?", args )
					conn.commit()
					given = True

					await self.bot.send_message(giver, "Votre demande de clé {} pour {} a été refusée par {} !".format(platform, game, member.name))

					await self.update_google_doc()

					break

		if given == False:
			await self.bot.whisper('Désolé, je n\'ai trouvé aucune donation en cours de votre part pour le jeu {} à {}'.format(game, destination))
		else:
			await self.bot.whisper('Confirmation du refus don. La clé est de nouveau disponible.')
		conn.close()



	@don.error
	async def don_error(self, error, ctx): 
		LOG.error(error)
		await self.bot.whisper('Veuillez taper la commande\n !don de [Jeu] sur [Plateforme] a [machin]')


	async def parse_game_name(self, url):
		await self.bot.wait_until_ready()
		game = None
		if "store.steampowered.com/app" in url:
			regexp = "(http|https)://store.steampowered.com/app/[0-9]+/([^/]+)/?"
		elif "gog.com/game" in url:
			regexp = "(http|https)://www.gog.com/game/([^/]+)/?"
		p = re.compile(regexp)
		
		m = p.match(url)
		if m:
			game = m.group(2)				

		return game


	async def post_announce(self, gameURL, platform, giver):
		channel = discord.Object(id=CONF.DONATION_CHANNEL_ID)
		game = await self.parse_game_name(gameURL)
		if game == None:
			return
		Choice1 = ["beau", "bon", "charmant", "délicieux", "divin", "doré", "fabuleux", "féerique", "fantasmagorique", "magique", "magnifique", "miraculeux", "mirifique", "mirobolant", "muscadin", "paradisiaque", "phénoménal", "prestigieux", "prodigieux", "rare", "ravissant" ,"remarquable", "romanesque", "saisissant", "sensationnel", "souverain", "splendide", "stupéfiant", "sublime", "superbe", "surprenant", "terrible" ,"thaumaturgique", "généreux", "grand", "riche", "fantastique", "cohérent", "merveilleux", "salutaire", "souriant", "chatoyant", "brillant", "pas si vieux que ça", "pas si bête que ça"]
		Choice2 = ["a généré une", "veut refourguer une", "a suremment volé une","veut votre bien avec une", "vous occroie une", "se débarasse d'une", "a trop de", "cherche un nouveau maître pour sa"]


		msg = "Le {} {} {} clé {} pour {}.\nVeuillez taper la commande suivante en PM : \n".format(random.choice(Choice1), giver.name, random.choice(Choice2), platform, gameURL)
		msg+= "!donnemoilacle {} de {} pour {} steuplé\n".format(platform, str(giver), game)
		msg+=  "afin que j\'en informe le {} {}. !listecle pour avoir la liste des clés disponibles. !donnecle pour donner une clé. !help pour la liste des commandes.".format(random.choice(Choice1), giver.name)

		if self.init == False:
			await self.bot.send_message(channel, msg)
		else: 
			self.init = False

	async def announce_liste(self):
		await self.bot.wait_until_ready()
		while not self.bot.is_closed:
			channel = discord.Object(id=CONF.DONATION_CHANNEL_ID)

			await self.bot.send_message(channel, "La liste de clés, elle est dans ton coeur, et ici : \nhttps://docs.google.com/spreadsheets/d/1Scz3FbCW8abM3btJwe3qNH_1OekGk-DdMR11_7C51ZE/view#gid=0\nVous retrouvez également l'aide pour donner une clé et faire revenir l'être aimé (1) ou en demander une !\nN'hésitez pas, elle sont là pour ça !\n(1)Le résultat n'est pas garanti")

			await asyncio.sleep(24*60*60)		


	async def announce_game(self):
		await self.bot.wait_until_ready()
		
		while not self.bot.is_closed:
			conn = sqlite3.connect('keys.db')
			c = conn.cursor()

			c.execute("SELECT * FROM steamkeys WHERE counter >= 1 ORDER BY RANDOM() LIMIT 1")

			selected = c.fetchone()
			if selected != None:

				giver = await self.bot.get_user_info(selected[0])				

				platform = selected[1]
				gameURL = selected[2]

				await self.post_announce(gameURL, platform, giver)

				conn.close()

			await asyncio.sleep(2*60*60)


	async def bother_to_give(self):
		await self.bot.wait_until_ready()
		while not self.bot.is_closed:
			conn = sqlite3.connect('keys.db')
			c = conn.cursor()
			c.execute("SELECT * FROM givekey WHERE given = 0")
			selected = c.fetchall()
			if len(selected) > 0:
				for row in selected:
					
					args = (row[0],)
					c.execute("SELECT user, platform, game FROM steamkeys WHERE rowId = ? LIMIT 1", args)
					gameinfo = c.fetchone()
					if gameinfo == None:
						continue

					gameName = await self.parse_game_name(gameinfo[2])
					if gameName == None:
						continue
					try:
						giver = await self.bot.get_user_info(gameinfo[0])
					except:
						pass

					destinationId = row[1]
					destination = None
					try:
						destination = await self.bot.get_user_info(destinationId)
					except:
						pass

					if destination:
						await self.bot.send_message(giver, "<@{}> désire votre clé {} pour {}.\nUne fois donnée, merci de taper la commande suivante : \n!don de {} sur {} a {}\nSinon je vais continuer à vous embêter avec ce message. En cas de refus de don, même commande, et vous vous demerdez avec {}, je suis pas votre père.".format(destination.id, gameinfo[1], gameName, gameName, gameinfo[1], str(destination), destination.name))


			conn.close()
			await asyncio.sleep(12*60*60)


def setup(bot):
	bot.add_cog(DonationDeCle(bot))		