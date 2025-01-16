from dotenv import load_dotenv
import os
load_dotenv()

AUTH_JSON_PATH = "auth.json"
SLACK_WEBHOOK = os.environ["SLACK_WEBHOOK"]