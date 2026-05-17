"""
🎓 TUTOR MATEMATICA - API BACKEND
Backend Flask con PostgreSQL (Supabase)
Deploy su Render - Chiamabile da qualsiasi sito
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import hashlib
import re
import time
import random
from datetime import datetime
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
CORS(app)  # Permette chiamate da qualsiasi dominio

# Database PostgreSQL (Supabase)
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db():
    """Connessione database PostgreSQL"""
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
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
        data_creazione TIMESTAMP NOT NULL
    )''')
    
    # Tabella assessment
    cur.execute('''CREATE TABLE IF NOT EXISTS assessment (
        id SERIAL PRIMARY KEY,
        username TEXT NOT NULL,
        classe INTEGER NOT NULL,
        problema TEXT NOT NULL,
        risposte JSONB NOT NULL,
        livello_assegnato TEXT NOT NULL,
        esito TEXT NOT NULL,
        tempo_secondi REAL NOT NULL,
        punteggio_spiegazione INTEGER,
        da_rivedere BOOLEAN,
        data TIMESTAMP NOT NULL,
        FOREIGN KEY (username) REFERENCES utenti(username)
    )''')
    
    # Tabella quesiti
    cur.execute('''CREATE TABLE IF NOT EXISTS quesiti (
        id SERIAL PRIMARY KEY,
        username TEXT NOT NULL,
        numero_quesito INTEGER NOT NULL,
        livello_numerico INTEGER NOT NULL,
        classe INTEGER NOT NULL,
        problema TEXT NOT NULL,
        risposte JSONB NOT NULL,
        ragionamento TEXT NOT NULL,
        esito TEXT NOT NULL,
        tempo_secondi REAL NOT NULL,
        punteggio_spiegazione INTEGER,
        da_rivedere BOOLEAN,
        data TIMESTAMP NOT NULL,
        FOREIGN KEY (username) REFERENCES utenti(username)
    )''')
    
    # Crea docente default
    cur.execute("SELECT * FROM utenti WHERE username = 'docente'")
    if not cur.fetchone():
        password_hash = hashlib.sha256("admin123".encode()).hexdigest()
        cur.execute('''INSERT INTO utenti (username, password_hash, classe, ruolo, data_creazione)
                       VALUES (%s, %s, %s, %s, %s)''', 
                    ("docente", password_hash, 0, "docente", datetime.now()))
    
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

# Carica problemi (hardcoded per semplicità)
PROBLEMI = {
    "classe_1": {
        "assessment": [{"testo": "Marco ha 5 caramelle. Ne riceve altre 3. Quante caramelle ha ora?", "risposta": "8", "indizio_1": "Devi sommare le caramelle", "indizio_2": "Fai 5 + 3", "soluzione": "Marco aveva 5 caramelle e ne riceve 3. Totale: 5 + 3 = 8 caramelle"}],
        "facile": [{"testo": "Sara ha 7 pennarelli. Ne regala 2. Quanti pennarelli le rimangono?", "risposta": "5", "indizio_1": "Devi togliere i pennarelli regalati", "indizio_2": "Fai 7 - 2", "soluzione": "Sara aveva 7 pennarelli e ne regala 2. Rimangono: 7 - 2 = 5 pennarelli"}],
        "medio": [{"testo": "Emma ha 12 matite. Ne regala 5. Quante matite le rimangono?", "risposta": "7", "indizio_1": "Devi sottrarre le matite regalate", "indizio_2": "Fai 12 - 5", "soluzione": "Emma aveva 12 matite e ne regala 5. Rimangono: 12 - 5 = 7 matite"}],
        "difficile": [{"testo": "Paolo ha 18 figurine. Ne regala 6 a Marco e 4 a Sara. Quante ne rimangono?", "risposta": "8", "indizio_1": "Devi togliere le figurine regalate a entrambi", "indizio_2": "Prima somma 6 + 4 = 10, poi fai 18 - 10", "soluzione": "Figurine regalate: 6 + 4 = 10. Figurine rimaste: 18 - 10 = 8"}]
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
    cur.execute('SELECT classe, ruolo FROM utenti WHERE username = %s AND password_hash = %s', 
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
                       VALUES (%s, %s, %s, %s, %s)''', 
                    (username, password_hash, classe, "studente", datetime.now()))
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
    tipo = data.get('tipo')  # assessment, facile, medio, difficile
    
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
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                (data['username'], data['classe'], data['problema'], json.dumps(data['risposte']),
                 data['livello'], data['esito'], data['tempo'], data.get('punteggio'),
                 data.get('da_rivedere'), datetime.now()))
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
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                (data['username'], data['numero'], data['livello_num'], data['classe'],
                 data['problema'], json.dumps(data['risposte']), data['ragionamento'],
                 data['esito'], data['tempo'], data.get('punteggio'), data.get('da_rivedere'), datetime.now()))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/adatta_livello', methods=['POST'])
def api_adatta_livello():
    data = request.get_json()
    nuovo = adatta_livello(data['livello'], data['successo'], data['tentativi'])
    return jsonify({'livello': nuovo})

if __name__ == '__main__':
    if DATABASE_URL:
        init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
