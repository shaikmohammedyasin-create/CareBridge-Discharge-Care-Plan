GLOSSARY = {
    "BD": "2 times a day",
    "BID": "2 times a day",
    "TDS": "3 times a day",
    "TID": "3 times a day",
    "OD": "once a day",
    "QD": "once a day",
    "HS": "at bedtime",
    "PC": "after food",
    "AC": "before food",
    "SOS": "when needed",
}

TELUGU = {
    "2 times a day": "రోజుకు 2 సార్లు",
    "3 times a day": "రోజుకు 3 సార్లు",
    "once a day": "రోజుకు 1 సారి",
    "at bedtime": "నిద్రకు ముందు",
    "after food": "భోజనం తర్వాత",
    "before food": "భోజనం ముందు",
    "when needed": "అవసరమైనప్పుడు",
    "morning": "ఉదయం",
    "noon": "మధ్యాహ్నం",
    "night": "రాత్రి",
    "for": "పాటు",
    "days": "రోజులు",
}

def expand_frequency(token: str) -> str | None:
    return GLOSSARY.get(token.upper())

def telugu(text: str) -> str:
    return TELUGU.get(text, text)
