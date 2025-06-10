import os
from dotenv import load_dotenv

load_dotenv()  #.env dosyasını yükleme

HERE_API_KEY = os.getenv("HERE_API_KEY")  # .env dosyasında ki here api değişkeni ile eşleşir
