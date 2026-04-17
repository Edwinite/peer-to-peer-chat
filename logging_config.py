import logging

def setup_logging():
    logging.basicConfig(filename='chat.log', level=logging.INFO,
                        format='%(asctime)s - %(message)s')

setup_logging()

def log_message(sender, message):
    logging.info(f"{sender}: {message}")
