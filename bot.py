import os
import json
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)
from telegram.error import TimedOut, NetworkError

CONFIG_FILE = "config.json"
ADMINS_FILE = "admins.json"
OWNERS_FILE = "owners.json"
LOGS_FILE = "logs.txt"

# Загрузка конфигурации
def load_json(filename):
    if not os.path.exists(filename):
        return []
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def log_action(message):
    with open(LOGS_FILE, "a", encoding="utf-8") as f:
        f.write(message + "\n")

admins = load_json(ADMINS_FILE)
owners = load_json(OWNERS_FILE)
config = {"authorized": load_json(CONFIG_FILE)}

MAIN_OWNER = "poshelnahuldalbaeb"

def is_owner(username):
    return username in owners

def is_main_owner(username):
    return username == MAIN_OWNER

def is_admin_or_owner(username):
    return username in admins or username in owners

async def log_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message.text
    if message.startswith("/") and is_admin_or_owner(user.username):
        log_action(f"{user.username} выполнил команду: {message}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот активен.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    username = user.username
    if is_owner(username):
        text = (
            "/addadmin @username — Добавить администратора\n"
            "/removeadmin @username — Удалить администратора\n"
            "/addauth @username — Добавить авторизованного\n"
            "/removeauth @username — Удалить авторизованного\n"
            "/addowner @username — Добавить владельца\n"
            "/listadmins — Показать список администрации\n"
            "/getlogs — Скачать логи"
        )
    elif username in admins:
        text = "/listadmins — Показать список администрации"
    elif username in config["authorized"]:
        text = "Вы авторизованы, но не имеете специальных прав."
    else:
        text = "Нет доступа к командам."
    await update.message.reply_text(text)

async def addowner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_owner(user.username) or not is_main_owner(user.username):
        await update.message.reply_text("Недостаточно прав.")
        return
    if not context.args:
        await update.message.reply_text("Укажите имя пользователя.")
        return
    new_owner = context.args[0].lstrip("@")
    if new_owner not in owners:
        owners.append(new_owner)
        save_json(OWNERS_FILE, owners)
        log_action(f"{user.username} добавил владельца: {new_owner}")
        await update.message.reply_text(f"Пользователь @{new_owner} добавлен в владельцы.")
    else:
        await update.message.reply_text("Пользователь уже владелец.")

async def addauth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_owner(user.username):
        await update.message.reply_text("Недостаточно прав.")
        return
    if not context.args:
        await update.message.reply_text("Укажите имя пользователя.")
        return
    auth_user = context.args[0].lstrip("@")
    if auth_user not in config["authorized"]:
        config["authorized"].append(auth_user)
        save_json(CONFIG_FILE, config["authorized"])
        log_action(f"{user.username} авторизовал: {auth_user}")
        await update.message.reply_text(f"@{auth_user} теперь авторизован.")
    else:
        await update.message.reply_text("Уже авторизован.")

async def removeauth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_owner(user.username):
        await update.message.reply_text("Недостаточно прав.")
        return
    if not context.args:
        await update.message.reply_text("Укажите имя пользователя.")
        return
    auth_user = context.args[0].lstrip("@")
    if auth_user in config["authorized"]:
        config["authorized"].remove(auth_user)
        save_json(CONFIG_FILE, config["authorized"])
        log_action(f"{user.username} удалил из авторизованных: {auth_user}")
        await update.message.reply_text(f"@{auth_user} удалён из авторизованных.")
    else:
        await update.message.reply_text("Пользователь не найден.")

async def listadmins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_owner(user.username) and user.username not in admins:
        await update.message.reply_text("Недостаточно прав.")
        return
    text = "Владельцы:\n" + "\n".join(owners) + "\n\nАдминистраторы:\n" + "\n".join(admins) + "\n\nАвторизованные:\n" + "\n".join(config["authorized"])
    await update.message.reply_text(text)

async def getlogs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_owner(user.username):
        await update.message.reply_text("Недостаточно прав.")
        return
    if os.path.exists(LOGS_FILE):
        await update.message.reply_document(document=open(LOGS_FILE, "rb"))
    else:
        await update.message.reply_text("Файл логов не найден.")

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Неизвестная команда.")

def main():
    application = ApplicationBuilder().token("7449302077:AAEcgPw2Xdu62JtJ4gtxHs05q5UFZBykkeQ").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("addowner", addowner))
    application.add_handler(CommandHandler("addauth", addauth))
    application.add_handler(CommandHandler("removeauth", removeauth))
    application.add_handler(CommandHandler("listadmins", listadmins))
    application.add_handler(CommandHandler("getlogs", getlogs))
    application.add_handler(MessageHandler(None, unknown))

    # Логирование команд админов и владельцев
    application.add_handler(MessageHandler(filters.TEXT & filters.COMMAND, log_user_command))

    application.run_polling()

if __name__ == "__main__":
    main()
