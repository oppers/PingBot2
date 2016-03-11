from discord.ext import commands
from core.colors import colors
from core.sysnotify import WindowNotify
from PIL import Image, ImageFont, ImageDraw
import asyncio
import random
import os
import logging
import discord
import configparser

bot = discord.Client()

info_dir = "./core/config"
config = configparser.ConfigParser()
config.read('./core/config/bot.info')
email = config.get('config', 'email', fallback="Email")
password = config.get('config', 'password', fallback="Password")
cmd_prefix = config.get("config","prefix",fallback="!")
description = config.get("config", "description", fallback="A discord bot built using Python (discord.py)")
pm_help = config.get("config", "pm_help", fallback=True)
no_perm_msg = config.get('messages', 'no_permission', fallback="You do not have the permission to use this command.")
only_owner = config.get('messages', 'only_owner', fallback="You must be the owner of this server to use this command.")
annoyed = config.get('messages', 'nuisance_msg', fallback="Nice try.")
bot = commands.Bot(command_prefix=cmd_prefix, description=description, pm_help=pm_help)

last_loaded = [] #last loaded cog

with open(os.path.join(info_dir, 'admins.info'), 'r') as admins_file:
	admins = admins_file.read().split(',')

with open(os.path.join(info_dir, 'no_delete.info'), 'r') as nd_file:
	no_delete = nd_file.read().split(',')

with open(os.path.join(info_dir, 'command_sets.info'), 'r') as cs_file:
	command_sets = cs_file.read().split(',')

with open(os.path.join(info_dir, "no_welcome.info"), 'r') as nw_file:
	no_welcome = nw_file.read().split(":")

os.system("title PingBot2 (Loading...)")

#-----------------------------

#Logging
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

#-----------------------------
#Extension load commands
@bot.command(pass_context=True, hidden=True)
async def load(ctx, extension_name : str):
	"""Loads an extension."""
	if is_dev(ctx) == True:
		try:
			bot.load_extension(extension_name)
			last_loaded.append(extension_name)
		except (AttributeError, ImportError) as e:
			await bot.say("```py\n{}: {}\n```".format(type(e).__name__, str(e)))
			print(colors.cred+e+colors.cwhite)
			return
		await bot.say("Successfully loaded `{}`.".format(extension_name))
	else:
		await bot.say(no_perm_msg)

@bot.command(pass_context=True, hidden=True)
async def unload(ctx, extension_name : str):
	"""Unloads an extension."""
	if is_dev(ctx) == True:
		if extension_name in last_loaded:
		    last_loaded.remove(extension_name)
		bot.unload_extension(extension_name)
		await bot.say("Successfully unloaded `{}`.".format(extension_name))
	else:
		await bot.say(no_perm_msg)

@bot.command(pass_context=True, hidden=True)
async def reload(ctx):
	"""Reloads all loaded extensions"""
	if is_dev(ctx) == True:
		reset(ctx)
		if reset(ctx) == True:
			await bot.say("Successfully reloaded!")
		else:
			await bot.say("Failed to reload!")

@bot.command(pass_context=True, hidden=True)
async def show_cogs(ctx):
	"""Shows a list of loaded cogs."""
	if is_dev(ctx) == True:
		await bot.say("Default command sets:")
		for i in command_sets:
			await bot.say(i)
		await bot.say("Recently loaded sets:")
		for i in last_loaded:
			await bot.say(i)

@bot.command(pass_context=True, hidden=True)
async def announce(ctx, *, string : str):
	"""Sends this message to all servers the bot is currently connected to."""
	sub_dir = "./core/config"
	with open(os.path.join(sub_dir, "banned_words.info"), 'r') as bw_file:
		banned_words = bw_file.read().split('|')

	if is_dev(ctx) == True:
		if any(word in string for word in banned_words):
			await bot.say(annoyed)
		else:
			for i in bot.servers:
				await bot.send_message(i, string) #bot.say(string)
	else:
		await bot.say(no_perm_msg)

@bot.command(pass_context=True, hidden=True)
async def servers(ctx):
	"""Returns all servers the bot is currently connected to."""
	if is_dev(ctx) == True:
		servers = len(bot.servers)
		for i in bot.servers:
			await bot.say("`{}` : `{}`" .format(i.name, i.id))
		await bot.say("Currently connected to `%s` server(s)." % servers)
	else:
		await bot.say(no_perm_msg)

#-----------------------------
#Bot events

#display information when the bot is ready.
@bot.event
async def on_ready():
	print(colors.cgreen+"User: %s" % bot.user.name)
	print("ID: %s" % bot.user.id+colors.cwhite)
	servers = len(bot.servers) #get amount of servers connected to
	print("Servers ({}):".format(servers))
	for server in bot.servers: #show a list of servers that the bot is currently connected to
		print("	{} : {}".format(server.name,server.id))
	for extension_name in command_sets: #load default extensions
		bot.load_extension(extension_name)

	sub_dir = "./core/docs/list"
	with open(os.path.join(sub_dir, "games.list"), 'r') as games_file:
			games = games_file.read().split(',')
	await bot.change_status(discord.Game(name="{}".format(random.choice(games)),idle=None))

	title = bot.user.name #Set command prompt window caption to bot name

	
	os.system("title "+title+" (PingBot2)")
	WindowNotify.balloon_tip(title, "Bot started successfully!")

	print(" ")

@bot.event
async def on_message(msg):
	if msg.content.startswith("!join"):
		invite = msg.content[len("!join "):].strip()
		await bot.accept_invite(invite)

	#leave the server
	if msg.content.startswith("!leave"):
		if msg.author.id == msg.server.owner.id or msg.author.id in admins:
			await bot.leave_server(msg.server)
		else:
			await bot.say(only_owner)

	#rip message
	if msg.content.startswith("!rip"):
		try:
			name = msg.content[len("!rip "):].strip()
			name_l = len(name)
			name_length = int(128/name_l*4/3)
			await bot.send_message(msg.channel, name_length)
			img = Image.open("./core/images/rip.jpg")
			draw = ImageDraw.Draw(img)
				# font = ImageFont.truetype(<font-file>, <font-size>)
			font = ImageFont.truetype("comic.ttf", name_length)
				# draw.text((x, y),"Sample Text",(r,g,b))
			draw.text((58, 149),"{} :(".format(name),(0,0,0),font=font)
			img.save('./core/images/rip-radioedit.jpg')
			await bot.send_file(msg.channel, "./core/images/rip-radioedit.jpg")
		except IndexError:
			await bot.send_typing(msg.channel)
			await bot.send_message(msg.channel, "http://i.imgur.com/Ij5lWrM.png")

	#message the user if the user mentioned is offline
	if len(msg.mentions) > 0:
		for user in msg.mentions:
			if user.status == user.status.offline:
				server = msg.server
				channel = msg.channel
				await bot.send_typing(msg.channel)
				await bot.send_message(msg.channel, "`{}` is currently offline!\r\nYour message has been sent via PM.".format(user.name))
				await bot.send_typing(user)
				await bot.send_message(user, "`{}` mentioned you while you were away in the server: {} (#{}).\r\n\r\n{}".format(msg.author.name, server, channel, msg.content))

	#edit the welcome message of a server.
	if msg.content.startswith('!welcome_edit'):
		if msg.author.id == msg.server.owner.id or msg.author.id in admins:
			servw = msg.content[len("!welcome_edit "):].strip()
			sub_dir = "./core/docs/welcome"
			with open(os.path.join(sub_dir, msg.server.id+".txt"), 'w') as welcome_file:
				welcome_file.write(servw)
			await bot.send_message(msg.channel, "Successfully modified server welcome message!")
		else:
			await bot.send_message(msg.channel, only_owner)

	await bot.process_commands(msg)
	print("[{}][{}][{}]: {}".format(msg.server, msg.channel, msg.author, msg.content))

#welcome message
@bot.event
async def on_member_join(member):
	if member.server.id not in no_welcome:
		server_id = member.server.id
		server = member.server
		sub_dir = "./core/docs/welcome"
		try:
			with open(os.path.join(sub_dir, server_id+".txt"),'r') as welcome_file:
				welcome = welcome_file.read()
		except FileNotFoundError:
			with open(os.path.join(sub_dir, "0.txt"),'r') as welcome_file:
				welcome = welcome_file.read()
		await bot.send_typing(server)
		await bot.send_message(server, "Welcome {} to {}!\r\n{}".format(member.mention, server.name, welcome))

@bot.event
async def on_message_delete(msg):
	if msg.server.id not in no_delete: #if the server is not equal to any of the servers above, then enable the on_message_delete feature.
		await bot.send_message(msg.channel, "`{0.author.name}` deleted the message:\r\n`{0.content}`".format(msg))


#-----------------------------
#Other bot functions

#returns a boolean depending on if the message author is a developer
def is_dev(ctx):
	if ctx.message.author.id in admins:
		return True
	else:
		print(colors.cred+"USER ATTEMPTED UNAUTHORIZED DEV COMMAND!"+colors.cwhite)
		return False

#returns a boolean depending on if the message author is an owner
def is_owner(ctx):
	if ctx.message.channel.is_private:
		return "PRIV"
	else:
		if ctx.message.author.id == ctx.message.server.owner.id:
			return True
		else:
			return False

#reloads the extensions.
def reset(ctx):
	if is_dev(ctx) == True:
		for i in command_sets:
			bot.unload_extension(i)
			bot.load_extension(i)
		for i in last_loaded:
			bot.unload_extension(i)
			bot.load_extension(i)
		return True
	else:
		return False

#random game loop
async def random_game():
	await bot.wait_until_ready()
	while not bot.is_closed:
		sub_dir = "./core/docs/list"
		with open(os.path.join(sub_dir, "games.list"), 'r') as games_file:
			games = games_file.read().split(',')
		await bot.change_status(discord.Game(name="{}".format(random.choice(games)),idle=None))
		await asyncio.sleep(100)

#random messages loop (Disabled for now.)
loop = asyncio.get_event_loop()

try:
	loop.create_task(random_game())
	try:
		loop.run_until_complete(bot.login(email, password))
		loop.run_until_complete(bot.connect())
	except discord.errors.LoginFailure:
		print(colors.cred+"ERROR! Failed to login!")
		print("The information you set in bot.info is wrong."+colors.cwhite)
		WindowNotify.balloon_tip(title, "Failed to login! (Check console.)")
except Exception:
	WindowNotify.balloon_tip(title, "Something went wrong!")
	loop.run_until_complete(bot.close())
except ConnectionResetError as e:
	print(colors.cred+"ERROR! PingBot unexpectedly closed!"+colors.cwhite)
	print(e)
	WindowNotify.balloon_tip(title, "Unexpectedly closed! (Check console.)")
finally:
	loop.close()