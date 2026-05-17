"""
🎓 TUTOR MATEMATICA - API BACKEND
Backend Flask con SQLite (SEMPLICE!)
Deploy su Render - Zero configurazione database
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import hashlib
import re
import time
import random
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)
CORS(app)  # Permette chiamate da qualsiasi dominio

# Database SQLite
DB_PATH = 'tutor_matematica.db'

def get_db():
    """Connessione database SQLite"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inizializza tabelle database"""
    conn = get_db()
    cur = conn.cursor()
    
    # Tabella utenti
    cur.execute('''CREATE TABLE IF NOT EXISTS utenti (
        username TEXT PRIMARY KEY,
        password_hash TEXT NOT NULL,
        classe INTEGER NOT NULL,
        ruolo TEXT NOT NULL CHECK(ruolo IN ('studente', 'docente')),
        data_creazione TEXT NOT NULL
    )''')
    
    # Tabella assessment
    cur.execute('''CREATE TABLE IF NOT EXISTS assessment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        classe INTEGER NOT NULL,
        problema TEXT NOT NULL,
        risposte TEXT NOT NULL,
        livello_assegnato TEXT NOT NULL,
        esito TEXT NOT NULL,
        tempo_secondi REAL NOT NULL,
        punteggio_spiegazione INTEGER,
        da_rivedere INTEGER,
        data TEXT NOT NULL,
        FOREIGN KEY (username) REFERENCES utenti(username)
    )''')
    
    # Tabella quesiti
    cur.execute('''CREATE TABLE IF NOT EXISTS quesiti (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        numero_quesito INTEGER NOT NULL,
        livello_numerico INTEGER NOT NULL,
        classe INTEGER NOT NULL,
        problema TEXT NOT NULL,
        risposte TEXT NOT NULL,
        ragionamento TEXT NOT NULL,
        esito TEXT NOT NULL,
        tempo_secondi REAL NOT NULL,
        punteggio_spiegazione INTEGER,
        da_rivedere INTEGER,
        data TEXT NOT NULL,
        FOREIGN KEY (username) REFERENCES utenti(username)
    )''')
    
    # Crea docente default
    cur.execute("SELECT * FROM utenti WHERE username = 'docente'")
    if not cur.fetchone():
        password_hash = hashlib.sha256("admin123".encode()).hexdigest()
        cur.execute('''INSERT INTO utenti (username, password_hash, classe, ruolo, data_creazione)
                       VALUES (?, ?, ?, ?, ?)''', 
                    ("docente", password_hash, 0, "docente", datetime.now().isoformat()))
    
    conn.commit()
    cur.close()
    conn.close()

# =====================================================================
# FUNZIONI VALIDAZIONE - IDENTICHE ALL'ORIGINALE
# =====================================================================

def estrai_numeri(testo):
    pattern = r'\d+[,.]?\d*'
    numeri_raw = re.findall(pattern, testo)
    numeri = []
    for n in numeri_raw:
        try:
            numeri.append(float(n.replace(',', '.')))
        except:
            pass
    return numeri

def rileva_operazioni_multiple(testo):
    testo_lower = testo.lower()
    operazioni = []
    keywords = {
        'addizione': ['somma', 'più', 'aggiungi', 'totale', '+', 'insieme', 'riceve', 'aumenta'],
        'sottrazione': ['sottrai', 'meno', 'togli', 'resta', '-', 'regala', 'spende', 'perde'],
        'moltiplicazione': ['moltiplica', 'per', 'volte', '×', '*', 'x ', 'prodotto'],
        'divisione': ['dividi', 'diviso', '÷', '/', 'parti', 'ciascun']
    }
    for op, kws in keywords.items():
        if any(kw in testo_lower for kw in kws):
            operazioni.append(op)
    return operazioni

def estrai_calcoli(testo):
    pattern = r'(\d+(?:[,.]\d+)?)\s*([+\-×*÷/])\s*(\d+(?:[,.]\d+)?)\s*=\s*(\d+(?:[,.]\d+)?)'
    matches = re.findall(pattern, testo)
    calcoli = []
    for match in matches:
        num1, op, num2, ris = match
        calcoli.append((float(num1.replace(',', '.')), op, float(num2.replace(',', '.')), float(ris.replace(',', '.'))))
    return calcoli

def verifica_calcolo_corretto(num1, operatore, num2, risultato):
    tolleranza = 0.01
    if operatore == '+': return abs((num1 + num2) - risultato) < tolleranza
    elif operatore == '-': return abs((num1 - num2) - risultato) < tolleranza
    elif operatore in ['×', '*', 'x']: return abs((num1 * num2) - risultato) < tolleranza
    elif operatore in ['÷', '/']:
        if num2 != 0: return abs((num1 / num2) - risultato) < tolleranza
    return False

def calcola_complessita_problema(problema):
    soluzione = problema.get('soluzione', '')
    operazioni = rileva_operazioni_multiple(soluzione)
    calcoli = estrai_calcoli(soluzione)
    num_step = max(len(operazioni), len(calcoli))
    if num_step <= 1: return 'semplice', num_step
    elif num_step == 2: return 'media', num_step
    else: return 'complessa', num_step

def valida_spiegazione_adattiva(spiegazione, problema, risposta_corretta):
    """VALIDAZIONE V2 COMPLETA - Identica all'originale"""
    spiegazione = spiegazione.strip()
    
    if len(spiegazione) < 3:
        return False, "La spiegazione è troppo corta. Spiega come hai risolto il problema!", 0, True
    
    if spiegazione.lower() in ['ok', 'si', 'sì', 'vai', 'boh', 'non lo so', 'non so']:
        return False, "Mi serve una vera spiegazione! Come hai fatto a trovare la risposta?", 0, True
    
    complessita, num_operazioni_necessarie = calcola_complessita_problema(problema)
    
    if complessita == 'semplice':
        soglia_ottima, soglia_buona, soglia_minima, soglia_da_rivedere = 70, 50, 30, 40
    elif complessita == 'media':
        soglia_ottima, soglia_buona, soglia_minima, soglia_da_rivedere = 60, 45, 25, 35
    else:
        soglia_ottima, soglia_buona, soglia_minima, soglia_da_rivedere = 50, 35, 20, 30
    
    punteggio = 0
    feedback = []
    
    numeri_problema = estrai_numeri(problema['testo'])
    numeri_spiegazione = estrai_numeri(spiegazione)
    if numeri_problema and numeri_spiegazione:
        numeri_comuni = set(numeri_problema) & set(numeri_spiegazione)
        perc = len(numeri_comuni) / len(numeri_problema)
        if perc >= 0.7: punteggio += 25
        elif perc >= 0.5: punteggio += 18
        elif perc >= 0.3: punteggio += 10
        else: feedback.append("Usa i numeri del problema")
    
    ops_necessarie = set(rileva_operazioni_multiple(problema['soluzione']))
    ops_spiegazione = set(rileva_operazioni_multiple(spiegazione))
    if ops_necessarie:
        ops_corrette = ops_necessarie & ops_spiegazione
        perc_ops = len(ops_corrette) / len(ops_necessarie)
        if perc_ops == 1.0: punteggio += 40
        elif perc_ops >= 0.5: punteggio += int(40 * perc_ops)
        else: punteggio += 10; feedback.append("Spiega quali operazioni hai usato")
    
    calcoli_spiegazione = estrai_calcoli(spiegazione)
    if calcoli_spiegazione:
        calcoli_corretti = sum(1 for c in calcoli_spiegazione if verifica_calcolo_corretto(*c))
        calcoli_sbagliati = len(calcoli_spiegazione) - calcoli_corretti
        if calcoli_sbagliati > 0: punteggio -= 10
        elif calcoli_corretti > 0: punteggio += 15
    
    if risposta_corretta.replace(',', '.').strip() in spiegazione.replace(',', '.'):
        punteggio += 10
    
    num_parole = len(spiegazione.split())
    min_parole = 5 if complessita == 'semplice' else 8 if complessita == 'media' else 10
    if num_parole >= min_parole + 5: punteggio += 10
    elif num_parole >= min_parole: punteggio += 5
    
    da_rivedere = punteggio < soglia_da_rivedere
    
    if punteggio >= soglia_ottima: return True, "Ottima spiegazione! 💡", punteggio, da_rivedere
    elif punteggio >= soglia_buona: return True, "Spiegazione buona. 👍", punteggio, da_rivedere
    elif punteggio >= soglia_minima:
        msg = "Accettabile" + (" per un problema difficile" if complessita == 'complessa' else "") + ". ⚠️"
        return True, msg, punteggio, da_rivedere
    else:
        msg = "Spiega meglio"
        if feedback: msg += ": " + ". ".join(feedback[:2])
        return False, msg + ". 🤔", punteggio, True

def valida_risposta(risposta_utente, risposta_corretta):
    u = risposta_utente.strip().lower().replace(',', '.').replace(' ', '')
    c = risposta_corretta.strip().lower().replace(',', '.').replace(' ', '')
    unita = ['euro', '€', 'eur', 'cm', 'm', 'km', 'kg', 'g', 'l', 'ml']
    for um in unita:
        u = u.replace(um, '')
        c = c.replace(um, '')
    if u == c: return True
    try: return float(u) == float(c)
    except: pass
    if '/' in u and '/' in c: return u == c
    return False

def adatta_livello(livello_corrente, successo, tentativi):
    livelli = ['facile', 'medio', 'difficile']
    idx = livelli.index(livello_corrente)
    if successo and tentativi == 1: idx = min(idx + 1, 2)
    elif successo and tentativi == 2: pass
    else: idx = max(idx - 1, 0)
    return livelli[idx]

# Problemi (database completo inline)
PROBLEMI = {
    "classe_1": {
        "assessment": [{"testo": "Marco ha 5 caramelle. Ne riceve altre 3. Quante caramelle ha ora?", "risposta": "8", "indizio_1": "Devi sommare le caramelle", "indizio_2": "Fai 5 + 3", "soluzione": "Marco aveva 5 caramelle e ne riceve 3. Totale: 5 + 3 = 8 caramelle"}],
        "facile": [{"testo": "Sara ha 7 pennarelli. Ne regala 2. Quanti pennarelli le rimangono?", "risposta": "5", "indizio_1": "Devi togliere i pennarelli regalati", "indizio_2": "Fai 7 - 2", "soluzione": "Sara aveva 7 pennarelli e ne regala 2. Rimangono: 7 - 2 = 5 pennarelli"}],
        "medio": [{"testo": "Emma ha 12 matite. Ne regala 5. Quante matite le rimangono?", "risposta": "7", "indizio_1": "Devi sottrarre le matite regalate", "indizio_2": "Fai 12 - 5", "soluzione": "Emma aveva 12 matite e ne regala 5. Rimangono: 12 - 5 = 7 matite"}],
        "difficile": [{"testo": "Paolo ha 18 figurine. Ne regala 6 a Marco e 4 a Sara. Quante ne rimangono?", "risposta": "8", "indizio_1": "Devi togliere le figurine regalate a entrambi", "indizio_2": "Prima somma 6 + 4 = 10, poi fai 18 - 10", "soluzione": "Figurine regalate: 6 + 4 = 10. Figurine rimaste: 18 - 10 = 8"}]
    },
    "classe_2": {
        "assessment": [{"testo": "Marco compra 3 gelati da 2 euro. Quanti euro spende?", "risposta": "6", "indizio_1": "Devi moltiplicare", "indizio_2": "Fai 3 × 2 oppure 2 + 2 + 2", "soluzione": "3 gelati × 2 euro = 6 euro"}],
        "facile": [{"testo": "Sara ha 12 caramelle. Le divide tra 4 amici. Quante per amico?", "risposta": "3", "indizio_1": "Devi dividere", "indizio_2": "Fai 12 ÷ 4", "soluzione": "12 caramelle ÷ 4 amici = 3 caramelle per amico"}],
        "medio": [{"testo": "Luca ha 4 scatole con 5 pennarelli. Quanti pennarelli in totale?", "risposta": "20", "indizio_1": "Devi moltiplicare", "indizio_2": "Fai 4 × 5", "soluzione": "4 scatole × 5 pennarelli = 20 pennarelli"}],
        "difficile": [{"testo": "Anna compra 3 libri a 4 euro e 2 penne a 2 euro. Quanto spende?", "risposta": "16", "indizio_1": "Calcola prima il costo dei libri, poi delle penne", "indizio_2": "Libri: 3 × 4 = 12. Penne: 2 × 2 = 4. Totale: 12 + 4", "soluzione": "Libri: 3 × 4 = 12 euro. Penne: 2 × 2 = 4 euro. Totale: 16 euro"}]
    },
    "classe_3": {
        "assessment": [{"testo": "Maria ha 24 figurine. Ne regala 1/4. Quante figurine regala?", "risposta": "6", "indizio_1": "1/4 di 24 significa dividere per 4", "indizio_2": "Fai 24 ÷ 4", "soluzione": "1/4 di 24 = 24 ÷ 4 = 6 figurine"}],
        "facile": [{"testo": "Paolo ha 15 euro. Compra un libro da 7 euro. Quanto resto?", "risposta": "8", "indizio_1": "Devi sottrarre", "indizio_2": "Fai 15 - 7", "soluzione": "15 - 7 = 8 euro di resto"}],
        "medio": [{"testo": "Un quadrato ha lato 6 cm. Qual è il perimetro?", "risposta": "24", "indizio_1": "Il perimetro è la somma di tutti i lati", "indizio_2": "Fai 6 + 6 + 6 + 6 oppure 6 × 4", "soluzione": "Perimetro = 6 × 4 = 24 cm"}],
        "difficile": [{"testo": "Giulia ha 30 euro. Spende 1/3 per un libro e 1/5 per una penna. Quanto spende?", "risposta": "16", "indizio_1": "Calcola 1/3 di 30 e 1/5 di 30 separatamente", "indizio_2": "1/3 di 30 = 10. 1/5 di 30 = 6. Totale: 10 + 6", "soluzione": "Libro: 30 ÷ 3 = 10 euro. Penna: 30 ÷ 5 = 6 euro. Totale: 16 euro"}]
    },
    "classe_4": {
        "assessment": [{"testo": "Un rettangolo ha base 8 cm e altezza 5 cm. Qual è l'area?", "risposta": "40", "indizio_1": "Area = base × altezza", "indizio_2": "Fai 8 × 5", "soluzione": "Area = 8 × 5 = 40 cm²"}],
        "facile": [{"testo": "Marco ha 3,5 euro. Riceve 2,3 euro. Quanto ha in totale?", "risposta": "5.8", "indizio_1": "Somma i decimali", "indizio_2": "Fai 3,5 + 2,3", "soluzione": "3,5 + 2,3 = 5,8 euro"}],
        "medio": [{"testo": "Un quadrato ha area 36 cm². Quanto è lungo il lato?", "risposta": "6", "indizio_1": "Lato = radice quadrata dell'area", "indizio_2": "Quale numero moltiplicato per sé stesso fa 36?", "soluzione": "Lato = √36 = 6 cm (perché 6 × 6 = 36)"}],
        "difficile": [{"testo": "In un negozio c'è uno sconto del 25% su un gioco da 40 euro. Quanto costa?", "risposta": "30", "indizio_1": "25% di 40 è lo sconto da togliere", "indizio_2": "25% di 40 = 10 euro. Prezzo finale: 40 - 10", "soluzione": "Sconto: 40 × 0,25 = 10 euro. Prezzo finale: 40 - 10 = 30 euro"}]
    },
    "classe_5": {
        "assessment": [{"testo": "Un parallelepipedo ha base 4 cm, larghezza 3 cm e altezza 5 cm. Qual è il volume?", "risposta": "60", "indizio_1": "Volume = base × larghezza × altezza", "indizio_2": "Fai 4 × 3 × 5", "soluzione": "Volume = 4 × 3 × 5 = 60 cm³"}],
        "facile": [{"testo": "Converti 3/5 in decimale", "risposta": "0.6", "indizio_1": "Dividi il numeratore per il denominatore", "indizio_2": "Fai 3 ÷ 5", "soluzione": "3 ÷ 5 = 0,6"}],
        "medio": [{"testo": "Un'auto viaggia a 60 km/h per 2,5 ore. Quanti km percorre?", "risposta": "150", "indizio_1": "Distanza = velocità × tempo", "indizio_2": "Fai 60 × 2,5", "soluzione": "Distanza = 60 × 2,5 = 150 km"}],
        "difficile": [{"testo": "Un cerchio ha raggio 7 cm. Qual è la circonferenza? (usa π ≈ 3,14)", "risposta": "43.96", "indizio_1": "Circonferenza = 2 × π × raggio", "indizio_2": "Fai 2 × 3,14 × 7", "soluzione": "Circonferenza = 2 × 3,14 × 7 = 43,96 cm"}]
    }
}

# =====================================================================
# API ENDPOINTS
# =====================================================================

@app.route('/api/health', methods=['GET'])
def health():
    """Check API status"""
    return jsonify({'status': 'ok', 'message': 'API online'})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    conn = get_db()
    cur = conn.cursor()
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    cur.execute('SELECT classe, ruolo FROM utenti WHERE username = ? AND password_hash = ?', 
                (username, password_hash))
    result = cur.fetchone()
    cur.close()
    conn.close()
    
    if result:
        return jsonify({'success': True, 'user': {'username': username, 'classe': result['classe'], 'ruolo': result['ruolo']}})
    return jsonify({'success': False, 'error': 'Username o password errati'})

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    classe = int(data.get('classe'))
    
    conn = get_db()
    cur = conn.cursor()
    try:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        cur.execute('''INSERT INTO utenti (username, password_hash, classe, ruolo, data_creazione)
                       VALUES (?, ?, ?, ?, ?)''', 
                    (username, password_hash, classe, "studente", datetime.now().isoformat()))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'success': True})
    except:
        cur.close()
        conn.close()
        return jsonify({'success': False, 'error': 'Username già esistente'})

@app.route('/api/get_problema', methods=['POST'])
def get_problema():
    data = request.get_json()
    classe = data.get('classe')
    tipo = data.get('tipo')
    
    chiave = f"classe_{classe}"
    if chiave in PROBLEMI and tipo in PROBLEMI[chiave]:
        problema = random.choice(PROBLEMI[chiave][tipo])
        return jsonify({'success': True, 'problema': problema})
    return jsonify({'success': False, 'error': 'Problema non trovato'})

@app.route('/api/valida_risposta', methods=['POST'])
def api_valida_risposta():
    data = request.get_json()
    risposta = data.get('risposta')
    corretta = data.get('corretta')
    return jsonify({'valida': valida_risposta(risposta, corretta)})

@app.route('/api/valida_spiegazione', methods=['POST'])
def api_valida_spiegazione():
    data = request.get_json()
    spiegazione = data.get('spiegazione')
    problema = data.get('problema')
    risposta = data.get('risposta')
    
    valida, msg, punteggio, da_rivedere = valida_spiegazione_adattiva(spiegazione, problema, risposta)
    return jsonify({
        'valida': valida,
        'messaggio': msg,
        'punteggio': punteggio,
        'da_rivedere': da_rivedere
    })

@app.route('/api/salva_assessment', methods=['POST'])
def api_salva_assessment():
    data = request.get_json()
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''INSERT INTO assessment (username, classe, problema, risposte, livello_assegnato, esito, 
                   tempo_secondi, punteggio_spiegazione, da_rivedere, data)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (data['username'], data['classe'], data['problema'], json.dumps(data['risposte']),
                 data['livello'], data['esito'], data['tempo'], data.get('punteggio'),
                 1 if data.get('da_rivedere') else 0, datetime.now().isoformat()))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/salva_quesito', methods=['POST'])
def api_salva_quesito():
    data = request.get_json()
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''INSERT INTO quesiti (username, numero_quesito, livello_numerico, classe, problema, risposte, 
                   ragionamento, esito, tempo_secondi, punteggio_spiegazione, da_rivedere, data)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (data['username'], data['numero'], data['livello_num'], data['classe'],
                 data['problema'], json.dumps(data['risposte']), data['ragionamento'],
                 data['esito'], data['tempo'], data.get('punteggio'), 
                 1 if data.get('da_rivedere') else 0, datetime.now().isoformat()))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/adatta_livello', methods=['POST'])
def api_adatta_livello():
    data = request.get_json()
    nuovo = adatta_livello(data['livello'], data['successo'], data['tentativi'])
    return jsonify({'livello': nuovo})

# Initialize database on startup (works with gunicorn)
init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
