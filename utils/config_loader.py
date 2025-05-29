import yaml
import os
from dotenv import load_dotenv

with open('C:/Users/school/PycharmProjects/capston/config.yaml', encoding='UTF-8') as f:
    _cfg = yaml.load(f, Loader=yaml.FullLoader)
APP_KEY = _cfg['APP_KEY']
APP_SECRET = _cfg['APP_SECRET']
CANO = _cfg['CANO']
ACNT_PRDT_CD = _cfg['ACNT_PRDT_CD']
URL_BASE = _cfg['URL_BASE']
HTS_ID = _cfg['HTS_ID']
API_KEY = _cfg['API_KEY']
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
