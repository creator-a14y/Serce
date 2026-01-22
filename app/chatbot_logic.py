import sqlite3
import string
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class ChatBot:
    def __init__(self, db_path='chatbot.db'):
        self.db_path = db_path
        self.son_anlasilmayan_mesaj = ""
        # Hafif zeka motoru (TF-IDF)
        self.vectorizer = TfidfVectorizer()
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS Intents (Id INTEGER PRIMARY KEY AUTOINCREMENT, Tag TEXT UNIQUE)')
        c.execute('CREATE TABLE IF NOT EXISTS Patterns (Id INTEGER PRIMARY KEY AUTOINCREMENT, IntentId INTEGER, PatternText TEXT)')
        c.execute('CREATE TABLE IF NOT EXISTS Responses (Id INTEGER PRIMARY KEY AUTOINCREMENT, IntentId INTEGER, ResponseText TEXT)')
        conn.commit()
        conn.close()

    def predict(self, user_sentence):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT P.PatternText, R.ResponseText FROM Patterns P JOIN Responses R ON P.IntentId = R.IntentId")
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            self.son_anlasilmayan_mesaj = user_sentence
            return None

        patterns = [row[0] for row in rows]
        responses = [row[1] for row in rows]
        
        # Cümleleri karşılaştırma (Kosinüs Benzerliği)
        # Formül: cos(theta) = (A . B) / (||A|| ||B||)
        tfidf = self.vectorizer.fit_transform(patterns + [user_sentence])
        similarities = cosine_similarity(tfidf[-1], tfidf[:-1])[0]
        
        en_yuksek_skor = max(similarities)
        en_iyi_index = similarities.argmax()

        if en_yuksek_skor > 0.25: # TF-IDF için 0.40 güçlü bir benzerliktir
            return responses[en_iyi_index]
        
        self.son_anlasilmayan_mesaj = user_sentence
        return None

    def teach(self, etiket, cevap):
        soru = self.son_anlasilmayan_mesaj if self.son_anlasilmayan_mesaj else etiket
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO Intents (Tag) VALUES (?)", (etiket,))
        cursor.execute("SELECT Id FROM Intents WHERE Tag = ?", (etiket,))
        intent_id = cursor.fetchone()[0]
        cursor.execute("INSERT INTO Patterns (IntentId, PatternText) VALUES (?, ?)", (intent_id, soru))
        cursor.execute("INSERT INTO Responses (IntentId, ResponseText) VALUES (?, ?)", (intent_id, cevap))
        conn.commit()
        conn.close()
        self.son_anlasilmayan_mesaj = ""
        return soru

