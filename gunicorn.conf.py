import multiprocessing
import os

timeout = 120
port = os.getenv("PORT")
bind = f"0.0.0.0:{port}"
workers = 10