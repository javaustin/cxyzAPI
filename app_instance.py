import asyncio
import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler

import boto3
from botocore.config import Config

from quart import Quart

from rich import print

app = Quart(__name__)

db = None
db_lock = asyncio.Lock()

scheduler = AsyncIOScheduler()

R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET = os.getenv("R2_BUCKET")

r2_client = boto3.client(
    "s3",
    endpoint_url = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
    aws_access_key_id=R2_ACCOUNT_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
    region_name="auto",
    config = Config(signature_version="s3v4")
)

print("[cyan]Starting app...[/cyan]")
