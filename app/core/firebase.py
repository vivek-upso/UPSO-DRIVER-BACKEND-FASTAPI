# core/firebase.py
import firebase_admin
from firebase_admin import credentials
from app.core.config import settings

cred = credentials.Certificate(settings.FIREBASE_CREDENTIAL)
firebase_admin.initialize_app(cred)
