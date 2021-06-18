import random

from discord import Message, TextChannel
from discord.ext import commands

from nltk import ngrams
from nltk.tokenize import TweetTokenizer
from nltk.tokenize.treebank import TreebankWordDetokenizer

class Ingestor(commands.Cog):
    def __init__(self, markov, owner_id, cmd_channel):
        self._tokenizer = TweetTokenizer()
        self._detokenizer = TreebankWordDetokenizer()
        self._markov = markov

        self._owner_id = owner_id
        self._cmd_channel = cmd_channel

    @commands.command()
    async def generate(self, ctx):
        if ctx.channel.id == self._cmd_channel:
            await ctx.reply(self._detokenizer.detokenize(self._markov.generate(50)))
        else:
            await ctx.message.add_reaction('❌')

    @commands.command()
    async def ingest(self, ctx, ch: TextChannel):
        if ctx.author.id != self._owner_id:
            return

        await ctx.reply(f'<a:loading:755494890070081656> Ingesting messages from {ch.name}')

        count = 0
        async for msg in ch.history(limit=None).filter(lambda m: not m.author.bot):
            self._markov.ingest(msg)
            print(f'Ingested {count} messages from {ch.name}')

            count += 1

        await ctx.reply(f'✅ Ingestion finished for {ch.name}. {count} messages ingested.')

    @commands.Cog.listener()
    async def on_message(self, msg: Message):
        if msg.author.bot:
            return

        self._markov.ingest(msg)

class MarkovChain:
    N_GRAM_LEN = 3

    START = ''
    END = '\0'

    def __init__(self, db):
        self._tokenizer = TweetTokenizer()
        self._detokenizer = TreebankWordDetokenizer()
        self._db = db

    def ingest(self, sentence: str):
        tokens = self._tokenizer.tokenize(sentence.clean_content)

        if len(tokens) < 2:
            return

        tokens.insert(0, self.START)
        tokens.append(self.END)

        tokens_num = len(tokens)
        
        for i in range(0, tokens_num - 1):
            self.add(tokens[i], tokens[i+1])

            if i + self.N_GRAM_LEN < tokens_num:
                self.add(tokens[i], tokens[i + self.N_GRAM_LEN])

    def add(self, token1: str, token2: str):
        with self._db.session() as session:
            self._increment_token(session, token1)
            self._add_token(session, token2)
            self._increment_relationship(session, token1, token2)

    def generate(self, size: int):
        with self._db.session() as session:
            sentence = [self.START]

            while size > 0:
                tokens, frequencies = self._get_token(session, sentence[-1])

                if not tokens:
                    tokens, frequencies = self._get_next(session, self.START)

                sentence.append(random.choices(tokens, k=1, weights=frequencies)[0])

                if sentence[-1] == self.END:
                    sentence.pop()
                    sentence.append('.')
                else:
                    size -= 1

            return sentence

    @staticmethod
    def _get_next(tx, token: str):
        records = tx.run("MATCH (t1:Token)-[r:FOLLOWED_BY]->(t2:Token) "
                            "WHERE t1.name = $t1 "
                            "RETURN t2.name as name, r.frequency as freq", t1=token)

        tokens = []
        frequencies = []

        for r in records:
            tokens.append(r['name'])
            frequencies.append(r['freq'])

        return tokens, frequencies

    @staticmethod
    def _increment_relationship(tx, token1: str, token2: str):
        query = (
            "MATCH (t1:Token {name: $t1}), (t2: Token {name: $t2}) "
            "MERGE (t1)-[r:FOLLOWED_BY]->(t2) "
            "ON CREATE "
            "SET r.frequency = 1 "
            "ON MATCH "
            "SET r.frequency = r.frequency + 1"
        )

        tx.run(query, t1=token1, t2=token2)
    
    @staticmethod
    def _increment_token(tx, token: str):
        query = (
            "MERGE (t:Token {name: $t}) "
            "ON CREATE "
            "SET t.frequency = 1 "
            "ON MATCH "
            "SET t.frequency = t.frequency + 1"
        )

        tx.run(query, t=token)

    @staticmethod
    def _add_token(tx, token: str):
        query = (
            "MERGE (t:Token {name: $t}) "
            "ON CREATE "
            "SET t.frequency = 0"
        )

        tx.run(query, t=token)