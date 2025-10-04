import os

class Settings:
    DATABASE_URL = "sqlite:///giraffe_quality.db"
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    SECRET_KEY = os.getenv("SECRET_KEY", "giraffe-secret-key")
    
    BRANCHES = [
        "חיפה", "הרצליה", "רמהח", "פתח תקווה", 
        "ראשלצ", "סביון", "מודיעין", "לנדמרק", "נס ציונה"
    ]

settings = Settings()
