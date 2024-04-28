from telegram import Update
from telegram.ext import ContextTypes
import json
from datetime import datetime


ADMIN_IDS = [5145402317, 87654321]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  welcome_message = (
      "<code>Hey brother, welcome to Daviinci Bot. This bot is made by </code> @daviinci_b\n"
      "<code>How to use? </code>\n"
      "<code>Tag bot in any group chat and follow this structure </code>\n"
      "<code>@botusername url time port </code>"
  )
  await update.message.reply_text(welcome_message, parse_mode='HTML')

async def modify_ban_status(update: Update, context: ContextTypes.DEFAULT_TYPE, ban_status: bool) -> None:
  user_id = update.effective_user.id
  if user_id not in ADMIN_IDS:
      return

  args = context.args
  if len(args) != 1:
      await update.message.reply_text("Usage:<code> /ban [user_id] or /unban [user_id]</code>",parse_mode='HTML')
      return

  target_id = args[0]
  try:
      with open('users.json', 'r+') as file:
          users = json.load(file)
          if target_id in users:
              users[target_id]['banned'] = ban_status
              file.seek(0)
              json.dump(users, file, indent=4)
              file.truncate()
              action = "banned" if ban_status else "unbanned"
              await update.message.reply_text(f"User <code>{target_id}</code> has been <code>{action}</code>.",parse_mode='HTML')
          else:
              await update.message.reply_text("User ID not found.")
  except Exception as e:
      await update.message.reply_text(f"Error modifying ban status: {e}")

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  await modify_ban_status(update, context, True)

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  await modify_ban_status(update, context, False)

async def blacklist_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  args = context.args
  if not args:
      await update.message.reply_text('Usage: /bl [list|rm target|target]\nExample:<code> /bl fbi.gov</code>\nExample:<code> /bl rm fbi.gov</code>',parse_mode="HTML")
      return

  command = args[0].lower()

  if command == 'list':
      await list_blacklist(update)
  elif command == 'rm' and len(args) > 1:
      await remove_from_blacklist(update, args[1])
  elif '.' in command or command.isnumeric():
      await add_to_blacklist(update, command)
  else:
      await update.message.reply_text('Invalid command or missing argument.')

async def list_blacklist(update: Update) -> None:
  with open('blacklist.json', 'r') as file:
      blacklist = json.load(file)
  if blacklist:
      message = "<code>" + "\n".join(blacklist) + "</code>"
  else:
      message = "Blacklist is empty."
  await update.message.reply_text(message,parse_mode="HTML")

async def add_to_blacklist(update: Update, target: str) -> None:
  with open('blacklist.json', 'r+') as file:
      blacklist = json.load(file)
      if target not in blacklist:
          blacklist.append(target)
          file.seek(0)
          json.dump(blacklist, file)
          file.truncate()
          await update.message.reply_text(f"Added <code>{target}</code> to blacklist.",parse_mode="HTML")
      else:
          await update.message.reply_text(f"<code>{target}</code> is already in the blacklist.",parse_mode="HTML")

async def remove_from_blacklist(update: Update, target: str) -> None:
  with open('blacklist.json', 'r+') as file:
      blacklist = json.load(file)
      if target in blacklist:
          blacklist.remove(target)
          file.seek(0)
          json.dump(blacklist, file)
          file.truncate()
          await update.message.reply_text(f"Removed <code>{target}</code> from blacklist.",parse_mode="HTML")
      else:
          await update.message.reply_text(f"<code>{target}</code> is not in the blacklist.",parse_mode="HTML")
      
async def running_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  user_id = update.effective_user.id
  now = datetime.utcnow()

  with open('running.json', 'r') as file:
      running_attacks = json.load(file)

  user_attacks = [details for key, details in running_attacks.items() if details["user_id"] == user_id and datetime.fromisoformat(details["end_time"]) > now]


  if not user_attacks:
      await update.message.reply_text("You have no running attacks.")
      return

  message = ""
  for attack in user_attacks:
      time_left = (datetime.fromisoformat(attack["end_time"]) - now).total_seconds()
      message += f"URL: {attack['url']}\nTime left: {int(time_left)}s\nPort: {attack['port']}\nMethod: {attack['method_name']}\n\n+---+----—————-----+---+"

  await update.message.reply_text(message)

async def method_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  user_id = update.effective_user.id
  if user_id not in ADMIN_IDS:
      return

  args = context.args
  if not args:
      await update.message.reply_text("Usage:<code> /method [add|list|rm] [parameters]</code>",parse_mode='HTML')
      return

  command = args[0].lower()

  if command == "add":
      await add_method(args[1:], update)
  elif command == "list":
      await list_methods(update)
  elif command == "rm":
      await remove_method(args[1:], update)
  else:
      await update.message.reply_text("Invalid command. Use <code>/method <add|list|rm> [parameters]</code>",parse_mode='HTML')

async def add_method(args, update: Update) -> None:
  if len(args) < 3:
      await update.message.reply_text("Usage:<code> /method [name] [description] [vip]</code>\nExample: <code> /method HTTPS HTTPS Attack true</code>",parse_mode='HTML')
      return

  method_name, description, vip_status = args[0], " ".join(args[1:-1]), args[-1].lower()

  if vip_status not in ['true', 'false']:
      await update.message.reply_text(" <code>VIP status must be either 'true' or 'false' </code>", parse_mode='HTML')
      return
  vip = vip_status == 'true'

  try:
      with open('methods.json', 'r') as file:
          methods = json.load(file)
  except FileNotFoundError:
      methods = []

  if any(method['name'] == method_name for method in methods):
      await update.message.reply_text(f"Method <code>'{method_name}'</code> already exists.", parse_mode='HTML')
      return

  new_method = {
      "name": method_name,
      "description": description,
      "vip": vip
  }

  methods.append(new_method)
  with open('methods.json', 'w') as file:
      json.dump(methods, file, indent=4)

  await update.message.reply_text(f"Method '{method_name}' added successfully.")

async def list_methods(update: Update) -> None:
  try:
      with open('methods.json', 'r') as file:
          methods = json.load(file)
  except FileNotFoundError:
      await update.message.reply_text("No methods available.")
      return

  if not methods:
      await update.message.reply_text("No methods available.")
      return

  method_list = "\n".join([f"<code>{method['name']}</code>: {method['description']} (VIP: {method['vip']})" for method in methods])
  await update.message.reply_text(f"{method_list}",parse_mode='HTML')

async def remove_method(args, update: Update) -> None:
  if len(args) < 1:
      await update.message.reply_text("Usage:<code> /method rm <name></code>",parse_mode='HTML')
      return

  method_name = args[0]

  try:
      with open('methods.json', 'r') as file:
          methods = json.load(file)
  except FileNotFoundError:
      await update.message.reply_text("No methods file found.")
      return


  method_found = False
  updated_methods = []
  for method in methods:
      if method['name'] == method_name:
          method_found = True
      else:
          updated_methods.append(method)

  if not method_found:
      await update.message.reply_text(f"Method <code>'{method_name}'</code> not found.", parse_mode='HTML')
      return


  with open('methods.json', 'w') as file:
      json.dump(updated_methods, file, indent=4)

  await update.message.reply_text(f"Method <code>'{method_name}'</code> has been removed.", parse_mode='HTML')

async def list_banned(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  user_id = update.effective_user.id
  if user_id not in ADMIN_IDS:
      return

  try:
      with open('users.json', 'r') as file:
          users = json.load(file)

      banned_users = [f"ID: <code>{uid} </code>" for uid, user in users.items() if user.get('banned', False)]

      if not banned_users:
          await update.message.reply_text("No banned users.")
      else:
          banned_users_text = "\n".join(banned_users)
          await update.message.reply_text(f"{banned_users_text}",parse_mode='HTML')

  except FileNotFoundError:
      await update.message.reply_text("User data file not found.")
  except json.JSONDecodeError:
      await update.message.reply_text("Error reading the user data.")


async def plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  user_id = str(update.effective_user.id)  

  try:
      with open('users.json', 'r') as file:
          users = json.load(file)

      user_plan = users.get(user_id)  
      

      if not user_plan:
          await update.message.reply_text("You do not have an active plan") 
      else:
          expire_datetime = datetime.fromisoformat(user_plan['expire'].replace('Z', '+00:00'))
          formatted_expire = expire_datetime.strftime('%H:%M:%S %d-%m-%Y')
          plan_details = (
              f"<b>Time: </b> <code>{user_plan['time']}s </code>\n"
              f"<b>Concurrent: </b> <code>{user_plan['concurrent']} </code>\n"
              f"<b>VIP: </b> <code>{'Yes' if user_plan['vip'] else 'No'} </code>\n"
              f"<b>Expires: </b> <code>{formatted_expire} </code>\n"
              f"<b>Banned: </b> <code>{'Yes' if user_plan['banned'] else 'No'} </code>\n"
              f"<b>Bypass Blacklist: </b> <code>{'Yes' if user_plan.get('bypass_blacklist', False) else 'No'} </code>"
          )
          await update.message.reply_text(f"{plan_details}",parse_mode='HTML')  

  except FileNotFoundError:
      await update.message.reply_text("User data file not found.")  
  except json.JSONDecodeError:
      await update.message.reply_text("Error reading the user data.")  


