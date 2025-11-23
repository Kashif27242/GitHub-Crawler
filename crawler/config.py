import os
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.environ.get('DATABASE_URL','postgresql://postgres:postgres@localhost:5432/github')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN','')
RUN_MODE = os.environ.get('RUN_MODE', 'preview')
TARGET = int(os.environ.get('TARGET', '10'))
BATCH_SIZE = int(os.environ.get('BATCH_SIZE', '1'))
