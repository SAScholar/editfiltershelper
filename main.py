import logging
import func
import config
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

if __name__ == '__main__':
    application = ApplicationBuilder().token(config.token).build()
    start_handler = CommandHandler('start', func.start)
    auth_handler = CommandHandler('auth', func.auth)
    whois_handler = CommandHandler('whois', func.whois)
    link_handler = CommandHandler('link', func.link)
    application.add_handler(start_handler)
    application.add_handler(auth_handler)
    application.add_handler(whois_handler)
    application.add_handler(link_handler)
    
    application.run_polling()