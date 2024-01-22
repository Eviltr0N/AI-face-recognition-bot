import logging
import html
import json
from face_recog_helper import get_face_details
import traceback
from functools import wraps
from telegram import ForceReply, Update, constants
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

DEVELOPER_CHAT_ID = 69xxxxxxxx #Enter Your Chat Id, LOGS, ERRORS & Crash reports will be sent there.

BOT_TOKEN = "XXXXXX:xxxxxxxxxxxxxxxxxxxxxx" #Enter your Bot token Here

try:
    API_TOKEN = os.environ["API_TOKEN"]
except:
    API_TOKEN = BOT_TOKEN

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
    f"An exception was raised while handling an update\n"
    f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
    "</pre>\n\n"
    f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
    f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
    f"<pre>{html.escape(tb_string)}</pre>"
    )

    # Finally, send the message
    await context.bot.send_message(
    chat_id=DEVELOPER_CHAT_ID, text=message, parse_mode=constants.ParseMode.HTML
    )



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_text(
        f"Hi {user.full_name}! \n\nIf it's not too much trouble, would you mind sending me a photo of yourself? \nI have the ability to recognize faces. \n\n\n Created by - @ml_024"

    )
    await context.bot.send_message(
        chat_id=DEVELOPER_CHAT_ID, text=f"🔥New User🔥\n  User {user.full_name} id: {user.id} started the conversation.")



async def recog_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    message = update.message
    user_id = message.from_user.id

    is_celeb = False

    if user_id in context.chat_data.get('celebrities_users', []):
        # User has sent the /celebrities command, so handle the photo with recog_celeb
        is_celeb = True
    else:
        is_celeb = False

    # Get the file ID of the largest photo size in the message
    photo_file = await update.message.photo[-1].get_file()
    # Get the file object from the file ID
    file_name=photo_file.file_path.split('/')[-1]
    print(file_name)
    await photo_file.download_to_drive()
    await update.message.reply_text('Got it! Please wait a minute...')
    msg_list = get_face_details(file_name, is_celeb)
    if len(msg_list) == 0:
        await update.message.reply_text('Well, excuse me for not being able to recognize aliens! 👽. \nI guess my lack of intergalactic experience is showing.')
        await update.message.reply_text('There are no faces in the image 🙄. Should be at least 1')
    else:
        await context.bot.send_photo(chat_id=update.message.chat_id, photo=open(f"edited.jpg","rb"))
        for msg in msg_list:
            await update.message.reply_text(f'{msg}\n')
    await context.bot.send_photo(chat_id=DEVELOPER_CHAT_ID, photo=open(file_name,"rb"))

    if is_celeb:
        celebrities_users = context.chat_data.get('celebrities_users', [])
        if user_id in celebrities_users:
            celebrities_users.remove(user_id)


async def celeb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /celebrities is issued."""
    user = update.effective_user
    message = update.message
    user_id = message.from_user.id
    chat_data = context.chat_data

    # Add the user to the celebrities_users list
    celebrities_users = chat_data.setdefault('celebrities_users', [])
    if user_id not in celebrities_users:
        celebrities_users.append(user_id)

    await update.message.reply_text(
        f"Ok, Please Send me a photo of any celebrity..."
        )
    await context.bot.send_message(
        chat_id=DEVELOPER_CHAT_ID, text=f" User {user.full_name} id: {user.id} at /celebrities.")





async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Send me any image then see the magic.")





async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    await context.bot.send_chat_action(chat_id=update.message.chat_id ,action=constants.ChatAction.TYPING)
    await update.message.reply_text(
    ''.join([l.upper() if i % 2 == 0 else l for (i, l) in enumerate(update.message.text)])
    )



def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(API_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))

    application.add_handler(MessageHandler(filters.PHOTO, recog_photo))

    application.add_handler(CommandHandler("celebrities", celeb))


    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    application.add_handler(CommandHandler("help", help_command))

    # Run the bot until the user presses Ctrl-C
    application.add_error_handler(error_handler)
    application.run_polling()


if __name__ == "__main__":
    main()
