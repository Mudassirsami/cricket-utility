import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.main import app
from fastapi import FastAPI
from mangum import Mangum

handler = Mangum(app)
