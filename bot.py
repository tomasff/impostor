import discord
from discord.ext import commands

from config import Config
from cogs.markov import Ingestor, MarkovChain

from neo4j import GraphDatabase

intents = discord.Intents.default()

bot = commands.Bot(command_prefix='i!', description='Impostor', intents=intents)

database = GraphDatabase.driver(Config.DB_URI, auth=(Config.DB_USER, Config.DB_PASS))
markov_chain = MarkovChain(database)

bot.add_cog(Ingestor(markov_chain))

bot.run(Config.DISCORD_TOKEN)
database.close()