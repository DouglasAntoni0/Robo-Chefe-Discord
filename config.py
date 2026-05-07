import os
import logging
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

CORES = {
    "sucesso":     0x2ECC71,
    "erro":        0xE74C3C,
    "info":        0x3498DB,
    "aviso":       0xF39C12,
    "principal":   0x9B59B6,
    "moderacao":   0xE74C3C,
    "ticket":      0x1ABC9C,
    "log":         0x95A5A6,
    "boas_vindas": 0x2ECC71,
    "despedida":   0xE67E22,
    "cargo":       0xF1C40F,
}

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s │ %(name)-25s │ %(levelname)-8s │ %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('bot.log', encoding='utf-8', mode='a'),
        ]
    )
    logging.getLogger('discord').setLevel(logging.WARNING)
    logging.getLogger('discord.http').setLevel(logging.WARNING)
    logging.getLogger('discord.gateway').setLevel(logging.WARNING)
