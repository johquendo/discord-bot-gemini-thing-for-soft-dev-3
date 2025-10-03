import os
import nextcord
from nextcord.ext import commands
from google import genai
from dotenv import load_dotenv
import json
import random

load_dotenv()

discord_token = os.getenv("DISCORD_TOKEN")
discord_guild = os.getenv("DISCORD_GUILD")
gemini_api_key = os.getenv("GEMINI_API_KEY")

question_tracker = set()

intents = nextcord.Intents.default()
intents.message_content = True

client = genai.Client(api_key=gemini_api_key)
bot = commands.Bot(command_prefix='!',intents = intents)

def json_thing(block: str):
    block = block.strip()

    if block.startswith("```json"):
        block = block[len("```json"):]

    if block.endswith("```"):
            block = block[:-3]

    return block.strip()

def generate_something(prompt: str):
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="in not 200 words, also access urls if given " + prompt
    ).text
    return response

def generate_question_and_answer(prompt: str):    
    print(list(question_tracker))
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="with the prompt " + prompt + " as topic, generate a question and an answer in json obj {question: <question>, answer: <answer>} make it that it is readable by json.load, make the questions, simple and the answers straight to the point, also add a number of items if asking for multiple items in the question, don't add any other phrases, just the json" + f" also do not repeat questions found in this list: {list(question_tracker)}"
    ).text
    data = json.loads(json_thing(response))
    question_tracker.add(data["question"])
    print(response)
    return data
        
def generate_multiple_choice_question(prompt: str):
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="with the prompt: " + prompt + " as topic, if none just choose a random topic, generate a question and 4 choices with one being the correct answer, format it as {question: <question>, a: <choice1>, b: <choice2>, c: <choice3>, d: <choice4>, answer: <answer>} and return as json," + f" also do not repeat questions found in this list: {list(question_tracker)}"
    ).text
    print(list(question_tracker))
    return response

def multiple_choice_embed(question: str, a: str, b: str, c: str, d: str):
    embed = nextcord.Embed(
         title="Multiple Choice Question",
         description=f"**{question}** \n a: {a} \n b: {b} \n c: {c} \n d: {d} \n "
    )     
    return embed
        
def validate_answer(question: str, answer: str):
     response = client.models.generate_content(
          model="gemini-2.5-flash",
          contents=f"verify if the answer is correct to the question, be strict and use known facts, question: {question}, answer: {answer}" + " respond in json {answer: <'true' or 'false'>, explanation: <explain>}"
     ).text
     print(f"verify if the answer is correct to the question, question: {question}, answer: {answer}")
     data = json.loads(json_thing(response))
     print(data)
     return response

def number_to_emoji(num: int):
     match num:
          case 0:
               return ":zero:"
          case 1:
               return ":one:"
          case 2:
               return ":two:"
          case 3:
               return ":three:"
          case 4:
               return ":four:"
          case 5:
               return ":five:"
          case 6:
               return ":six:"
          case 7:
               return ":seven:"
          case 8:
               return ":eight:"
          case 9:
               return ":nine:"
          
def slots_embed(a: int, b: int, c: int, message: str):
     embed = nextcord.Embed(
          title="**Slots Result**",
          description=f"{a} {b} {c} \n {message}",
          color=nextcord.Color.blue()
     )
     return embed

@bot.command()
async def generatesomething(ctx, arg):
    await ctx.send(generate_something(arg))

@bot.command()
async def commands(ctx):
     await ctx.send(embed=nextcord.Embed(title="Bot Help", description="**Bot Commands** \n Bot Prefix: '!' \n generatesomething <prompt>: generates a message based on the prompt \n generatemultiplechoicequestion <prompt> <amount>: generates a multiple choice quiz based on the prompt and amount \n generatequestion <prompt>: generates a question using the prompt"))

@bot.command()
async def generatemultiplechoicequestion(ctx, prompt="", amount=1):
        score = 0
        for i in range(amount):
            multiple_choice = generate_multiple_choice_question(prompt)
            print(multiple_choice)
            data = json.loads(json_thing(multiple_choice))
            question_tracker.add(data["question"])
            await ctx.send(embed = multiple_choice_embed(data["question"], data["a"], data["b"], data["c"], data["d"]))

            def check(message: str):
                return message.author == ctx.author and message.channel == ctx.channel
            
            msg = await bot.wait_for("message", check=check)
            if msg.content == "stop":
                 await ctx.send("Quiz Stopped")
                 break
            elif msg.content == data["answer"]:
                 score += 1
                 await ctx.send("Correct")
            else:
                 await ctx.send("Wrong")

        await ctx.send(f"Score: {score} out of {amount}")
    

@bot.command()
async def generatequestion(ctx, prompt=""):
    question_answer = generate_question_and_answer(prompt)
    await ctx.send(question_answer["question"])

    def check(message: str):
        return message.author == ctx.author and message.channel == ctx.channel
    
    msg = await bot.wait_for("message", check=check)
    await ctx.send(validate_answer(question_answer["question"], msg.content))

@bot.command()
async def test(ctx, arg):
    await ctx.send(arg)

@bot.command()
async def roll(ctx):
     await ctx.send(f"{ctx.author.mention} rolled a {random.randint(0, 10)}")

@bot.command()
async def one(ctx):
     await ctx.send(":one:")

@bot.command()
async def slots(ctx):
     a = number_to_emoji(random.randint(0, 9))
     b = number_to_emoji(random.randint(0, 9))
     c = number_to_emoji(random.randint(0, 9))
     result = None
     if a == b == c:
            result = "You win!"
     else:
            result = "Try again or something"
    
     await ctx.send(embed=slots_embed(a, b, c, result))

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

bot.run(discord_token)
