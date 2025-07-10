from dotenv import load_dotenv
import os

load_dotenv()


class Config:
    API_ID = int(os.getenv("API_ID"))
    API_HASH = os.getenv("API_HASH")
    PHONE = os.getenv("PHONE")
    USERNAME = os.getenv("USERNAME")
    LINK = os.getenv("LINK")
    FROM = list(map(int, os.getenv("FROM").split(",")))
    TO = list(map(int, os.getenv("TO").split(",")))
