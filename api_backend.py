# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, send_file
import json
import os
import time
import hashlib
import re
from datetime import datetime
from pathlib import Path
import random

app = Flask(__name__, static_folder='.', static_url_path='')

FILE_DB = "database_classe.json"
FILE_PROBLEMI = "problemi_per_classe.json"
FILE_OBIETTIVI = "OBIETTIVI_DIDATTICI_MATEMATICA.md"

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def carica_database() -> dict:
    if os.path.exists(FILE_DB):
        with open(FILE_DB, "r", encoding="utf-8") as f:
            return json.load(f)
    db_base = {
        "prof": {
            "password": hash_password("admin"),
            "ruolo": "docente"
        }
    }
    salva_database(db_base)
    return db_base

def salva_database(database: dict):
    with open(FILE_DB, "w", encoding="utf-8") as f:
        json.dump(database, f, indent=4, ensure_ascii=False)

def crea_problemi_base():
    problemi_base = {
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
    with open(FILE_PROBLEMI, "w", encoding="utf-8") as f:
        json.dump(problemi_base, f, indent=2, ensure_ascii=False)
    return problemi_base

def carica_pool_problemi():
    if not os.path.exists(FILE_PROBLEMI):
        return crea_problemi_base()
    with open(FILE_PROBLEMI, 'r', encoding='utf-8') as f:
        return json.load(f)

def salva_pool_problemi(pool: dict):
    with open(FILE_PROBLEMI, "w", encoding="utf-8") as f:
        json.dump(pool, f, indent=2, ensure_ascii=False)

def carica_obiettivi():
    if not os.path.exists(FILE_OBIETTIVI):
        # FIX FORMATTAZIONE: Usiamo veri a-capo per non far stampare " \n "
        obiettivi_base = (
            "# OBIETTIVI DIDATTICI MATEMATICA SCUOLA PRIMARIA\n\n"
            "## CLASSE 1ª\n"
            "- Contare fino a 20\n"
            "- Addizioni e sottrazioni entro il 10\n"
            "- Riconoscere forme geometriche base\n\n"
            "## CLASSE 2ª\n"
            "- Tabelline base (×2, ×5, ×10)\n"
            "- Addizioni e sottrazioni entro il 100\n"
            "- Prime divisioni semplici\n\n"
            "## CLASSE 3ª\n"
            "- Padroneggiare tutte le tabelline\n"
            "- Frazioni semplici (1/2, 1/4, 1/3)\n"
            "- Perimetro di figure semplici\n\n"
            "## CLASSE 4ª\n"
            "- Numeri decimali\n"
            "- Area di rettangoli e quadrati\n"
            "- Frazioni e percentuali base\n\n"
            "## CLASSE 5ª\n"
            "- Frazioni complesse\n"
            "- Volume di solidi\n"
            "- Proporzioni e percentuali avanzate\n"
        )
        with open(FILE_OBIETTIVI, "w", encoding="utf-8") as f:
            f.write(obiettivi_base)
        return obiettivi_base
    with open(FILE_OBIETTIVI, 'r', encoding='utf-8') as f:
        return f.read()

def salva_obiettivi(testo: str):
    with open(FILE_OBIETTIVI, "w", encoding="utf-8") as f:
        f.write(testo)

def normalizza_classe(classe_raw):
    if not classe_raw:
        return "5"
    s = str(classe_raw).strip().lower()
    if s.endswith('a'):
        s = s[:-1]
    numero = ''.join(c for c in s if c.isdigit())
    return numero if numero in ['1', '2', '3', '4', '5'] else "5"

def conta_quesiti_log(log_sessione):
    if not log_sessione or not isinstance(log_sessione, list):
        return 0
    count = 0
    for entry in log_sessione:
        if isinstance(entry, dict) and entry.get("tipo") == "QUESITO":
            count += 1
    return count

def estrai_numeri(testo: str) -> list:
    pattern = r'\d+[,.]?\d*'
    numeri_raw = re.findall(pattern, testo)
    numeri = []
    for n in numeri_raw:
        try:
            n_norm = n.replace(',', '.')
            numeri.append(float(n_norm))
        except:
            pass
    return numeri

def _strip_accenti(s: str) -> str:
    # FIX A: rimuove gli accenti cosi' "piu" matcha "più", "perche" matcha "perché", ecc.
    for a, b in (('à','a'),('á','a'),('è','e'),('é','e'),('ì','i'),
                 ('í','i'),('ò','o'),('ó','o'),('ù','u'),('ú','u')):
        s = s.replace(a, b)
    return s

def _build_numeri_parole() -> dict:
    # FIX B: mappa parola->numero per 0-100 (gestisce anche ventuno, ventotto, ventitre...)
    u = ['zero','uno','due','tre','quattro','cinque','sei','sette','otto','nove']
    teens = ['dieci','undici','dodici','tredici','quattordici','quindici','sedici',
             'diciassette','diciotto','diciannove']
    tens = {20:'venti',30:'trenta',40:'quaranta',50:'cinquanta',60:'sessanta',
            70:'settanta',80:'ottanta',90:'novanta'}
    d = {}
    for i, wn in enumerate(u): d[wn] = i
    for i, wn in enumerate(teens): d[wn] = 10 + i
    for t, tw in tens.items():
        d[tw] = t
        for ui in range(1, 10):
            base = tw[:-1] if ui in (1, 8) else tw   # ventuno, ventotto: cade la vocale
            w = base + ('tre' if ui == 3 else u[ui])
            d[w] = t + ui
    d['cento'] = 100
    for amb in ('una', 'un'):   # troppo ambigue (articoli)
        d.pop(amb, None)
    return d

NUMERI_PAROLE = _build_numeri_parole()
_NUM_PATTERN = re.compile(r'\b(' + '|'.join(sorted(NUMERI_PAROLE, key=len, reverse=True)) + r')\b')

def _parole_in_cifre(testo: str) -> str:
    # FIX B: converte i numeri scritti a parole in cifre prima dell'analisi
    t = _strip_accenti(testo.lower())
    return _NUM_PATTERN.sub(lambda mch: str(NUMERI_PAROLE[mch.group(1)]), t)

def rileva_operazioni_multiple(testo: str) -> list:
    testo_lower = _strip_accenti(testo.lower())
    operazioni = []
    # FIX A: liste senza accenti e arricchite con le storpiature piu' comuni dei bambini
    keywords_addizione = ['somma', 'sommo', 'sommato', 'piu', 'aggiungi', 'aggiunto', 'totale', '+',
                          'insieme', 'riceve', 'aumenta', 'unisci', 'addizione', 'addiziono']
    keywords_sottrazione = ['sottrai', 'sottra', 'sotra', 'sottrazione', 'sotrazione', 'meno', 'togli',
                           'tolto', 'tolgo', 'resta', '-', 'regala', 'regalo', 'spende', 'speso',
                           'perde', 'differenza', 'toglie']
    keywords_moltiplicazione = ['moltiplica', 'moltiplico', 'moltipico', 'moltiplicazione', 'per',
                               'volte', '×', '*', 'x ', 'prodotto', 'ogni']
    keywords_divisione = ['dividi', 'divido', 'diviso', 'divizione', 'divisione', '÷', '/',
                         'parti', 'ciascun', 'distribuisci']

    if any(kw in testo_lower for kw in keywords_addizione):
        operazioni.append('addizione')
    if any(kw in testo_lower for kw in keywords_sottrazione):
        operazioni.append('sottrazione')
    if any(kw in testo_lower for kw in keywords_moltiplicazione):
        operazioni.append('moltiplicazione')
    if any(kw in testo_lower for kw in keywords_divisione):
        operazioni.append('divisione')
    return operazioni

def estrai_calcoli(testo: str) -> list:
    pattern = r'(\d+(?:[,.]\d+)?)\s*([+\-×*÷/])\s*(\d+(?:[,.]\d+)?)\s*=\s*(\d+(?:[,.]\d+)?)'
    matches = re.findall(pattern, testo)
    calcoli = []
    for match in matches:
        num1, op, num2, ris = match
        calcoli.append((
            float(num1.replace(',', '.')),
            op,
            float(num2.replace(',', '.')),
            float(ris.replace(',', '.'))
        ))
    return calcoli

def verifica_calcolo_corretto(num1: float, operatore: str, num2: float, risultato: float) -> bool:
    tolleranza = 0.01
    if operatore in ['+']:
        return abs((num1 + num2) - risultato) < tolleranza
    elif operatore in ['-']:
        return abs((num1 - num2) - risultato) < tolleranza
    elif operatore in ['×', '*', 'x']:
        return abs((num1 * num2) - risultato) < tolleranza
    elif operatore in ['÷', '/']:
        if num2 != 0:
            return abs((num1 / num2) - risultato) < tolleranza
    return False

def calcola_complessita_problema(problema: dict) -> tuple:
    soluzione = problema.get('soluzione', '')
    operazioni = rileva_operazioni_multiple(soluzione)
    num_operazioni = len(operazioni)
    calcoli = estrai_calcoli(soluzione)
    num_calcoli = len(calcoli)
    num_step = max(num_operazioni, num_calcoli)
    if num_step <= 1:
        return 'semplice', num_step
    elif num_step == 2:
        return 'media', num_step
    else:
        return 'complessa', num_step

def valida_spiegazione_adattiva(spiegazione: str, problema: dict, risposta_corretta: str) -> tuple:
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
    da_rivedere_forzato = False  # FIX 2: forza la revisione se c'e' un calcolo errato esplicito

    spiegazione_norm = _parole_in_cifre(spiegazione)  # FIX B: numeri a parole -> cifre
    numeri_problema = estrai_numeri(problema['testo'])
    numeri_spiegazione = estrai_numeri(spiegazione_norm)
    if numeri_problema and numeri_spiegazione:
        numeri_comuni = set(numeri_problema) & set(numeri_spiegazione)
        percentuale_numeri = len(numeri_comuni) / len(numeri_problema)
        if percentuale_numeri >= 0.7: punteggio += 25
        elif percentuale_numeri >= 0.5: punteggio += 18
        elif percentuale_numeri >= 0.3: punteggio += 10
        else: feedback.append("Usa i numeri del problema")
    else:
        feedback.append("Menziona i numeri del problema")
        
    ops_necessarie = set(rileva_operazioni_multiple(problema['soluzione']))
    ops_spiegazione = set(rileva_operazioni_multiple(spiegazione_norm))
    if ops_necessarie:
        ops_corrette = ops_necessarie & ops_spiegazione
        percentuale_ops = len(ops_corrette) / len(ops_necessarie)
        if percentuale_ops == 1.0: punteggio += 40
        elif percentuale_ops >= 0.5:
            punteggio += int(40 * percentuale_ops)
            ops_mancanti = ops_necessarie - ops_spiegazione
            if ops_mancanti:
                traduzioni = {'addizione': 'somma/addizione', 'sottrazione': 'sottrazione', 'moltiplicazione': 'moltiplicazione', 'divisione': 'divisione'}
                ops_it = [traduzioni.get(op, op) for op in ops_mancanti]
                feedback.append(f"Menziona anche: {', '.join(ops_it)}")
        else:
            punteggio += 10
            feedback.append("Spiega quali operazioni hai usato")
            
    calcoli_spiegazione = estrai_calcoli(spiegazione_norm)
    if calcoli_spiegazione:
        calcoli_corretti = 0
        calcoli_sbagliati = 0
        for num1, op, num2, ris in calcoli_spiegazione:
            if verifica_calcolo_corretto(num1, op, num2, ris): calcoli_corretti += 1
            else:
                calcoli_sbagliati += 1
                feedback.append(f"Controlla: {int(num1)}{op}{int(num2)}≠{int(ris)}")
        if calcoli_sbagliati > 0:
            punteggio -= 10
            da_rivedere_forzato = True  # FIX 2: un calcolo errato va sempre segnalato al docente
        elif calcoli_corretti > 0: punteggio += 15
        
    risposta_norm = risposta_corretta.replace(',', '.').strip()
    if risposta_norm in spiegazione_norm.replace(',', '.'): punteggio += 10
    else:
        if complessita == 'semplice': feedback.append("Menziona il risultato finale")
        
    parole = spiegazione.split()
    num_parole = len(parole)
    min_parole = 5 if complessita == 'semplice' else 8 if complessita == 'media' else 10
    if num_parole >= min_parole + 5: punteggio += 10
    elif num_parole >= min_parole: punteggio += 5
    else:
        if complessita != 'semplice': feedback.append("Spiega i passaggi più in dettaglio")
        
    # FIX D: per il livello "ottima" serve una verbalizzazione reale, non solo il calcolo nudo
    # solo token con almeno 2 lettere di fila: esclude i simboli e la 'x' di '3x4=12'
    parole_alfabetiche = [t for t in spiegazione.split() if re.search(r'[a-zàèéìòù]{2,}', t.lower())]
    connettivi = ['perche', 'perke', 'xke', 'cosi', 'quindi', 'allora', 'siccome', 'infatti', 'dato', 'poi', 'prima', 'percio']
    testo_conn = _strip_accenti(spiegazione.lower())
    ha_connettivo = any(c in testo_conn for c in connettivi)
    verbalizzazione_ok = (len(parole_alfabetiche) >= 2) or ha_connettivo
    if ha_connettivo: punteggio += 5          # premia la giustificazione esplicita
    punteggio = max(0, min(100, punteggio))

    da_rivedere = (punteggio < soglia_da_rivedere) or da_rivedere_forzato
    if da_rivedere_forzato:
        # FIX D: un calcolo esplicitamente sbagliato non puo' essere "ottima": si segnala chiaramente
        return True, "Attenzione: c'è un errore in un calcolo, ricontrolla i passaggi. 🤔", punteggio, True
    if punteggio >= soglia_ottima and verbalizzazione_ok:
        return True, "Ottima spiegazione! 💡", punteggio, da_rivedere
    elif punteggio >= soglia_buona:
        if not verbalizzazione_ok:
            return False, "Hai fatto il calcolo giusto! Ora prova a spiegare a parole come hai ragionato. 👍", punteggio, da_rivedere
        return True, "Spiegazione buona. 👍", punteggio, da_rivedere
    elif punteggio >= soglia_minima:
        msg_base = "Accettabile" + (" per un problema difficile" if complessita == 'complessa' else "")
        return True, msg_base + ". ⚠️", punteggio, da_rivedere
    else:
        msg = "Spiega meglio" + (": " + ". ".join(feedback[:2]) if feedback else "")
        return False, msg + ". 🤔", punteggio, True

def valida_risposta(risposta_utente: str, risposta_corretta: str) -> bool:
    def pulisci(testo):
        t = testo.strip().lower().replace(',', '.')
        numeri = re.findall(r'\d+\.?\d*', t)
        return numeri[0] if numeri else t.replace(' ', '')
    u_raw = risposta_utente.strip().lower().replace(',', '.')
    c_raw = risposta_corretta.strip().lower().replace(',', '.')
    # 1) confronto stringa diretto (cattura anche le frazioni uguali, es. '3/4')
    if u_raw.replace(' ', '') == c_raw.replace(' ', ''): return True
    # 2) FIX 1: se entrambe sono frazioni e NON sono uguali, sono diverse.
    #    Va valutato PRIMA di estrarre i numeri: altrimenti '3/4' e '3/5'
    #    verrebbero confrontate solo sul numeratore e risulterebbero uguali.
    if '/' in u_raw and '/' in c_raw:
        return u_raw.replace(' ', '') == c_raw.replace(' ', '')
    u = pulisci(u_raw)
    c = pulisci(c_raw)
    if u == c: return True
    try:
        return abs(float(u) - float(c)) < 0.01
    except: pass
    return False

def adatta_livello(livello_corrente: str, successo: bool, tentativi: int) -> str:
    livelli_ordine = ['facile', 'medio', 'difficile']
    indice_corrente = livelli_ordine.index(livello_corrente)
    if successo and tentativi == 1: nuovo_indice = min(indice_corrente + 1, 2)
    elif successo and tentativi == 2: nuovo_indice = indice_corrente
    else: nuovo_indice = max(indice_corrente - 1, 0)
    return livelli_ordine[nuovo_indice]

@app.route('/')
def home_index():
    return send_file('index.html')

@app.route('/api/login', methods=['POST'])
def api_login():
    db = carica_database()
    dati = request.get_json() or {}
    u = dati.get('username', '').strip().lower()
    p = dati.get('password', '').strip()
    
    if u in db:
        # FIX 3: confronto solo con l'hash SHA-256, nessun fallback in chiaro
        if db[u].get('password') == hash_password(p):
            return jsonify({
                "status": "success", 
                "ruolo": db[u].get('ruolo'), 
                "classe": normalizza_classe(db[u].get('classe', '5'))
            })
    return jsonify({"status": "error", "message": "Credenziali errate!"})

@app.route('/api/register', methods=['POST'])
def api_register():
    db = carica_database()
    dati = request.get_json() or {}
    u = dati.get('username', '').strip().lower()
    p = dati.get('password', '').strip()
    classe = dati.get('classe', '').strip()
    
    if not u or not p:
        return jsonify({"status": "error", "message": "Username e password obbligatori!"})
    if u in db:
        return jsonify({"status": "error", "message": "Username già esistente!"})
    if classe not in ['1', '2', '3', '4', '5']:
        return jsonify({"status": "error", "message": "Seleziona una classe valida (1-5)!"})
        
    db[u] = {
        "password": hash_password(p),
        "ruolo": "studente",
        "classe": classe,
        "livello_attuale": 0,
        "livello_massimo": 0,
        "log_sessione": []
    }
    salva_database(db)
    return jsonify({"status": "success", "ruolo": "studente", "classe": classe})

@app.route('/api/teacher/dashboard', methods=['GET'])
def teacher_dashboard():
    db = carica_database()
    studenti = []
    for username, dati in db.items():
        if dati.get('ruolo') == 'studente':
            log = dati.get('log_sessione', [])
            studenti.append({
                "username": username,
                "classe": normalizza_classe(dati.get('classe', '5')),
                "livello_massimo": dati.get('livello_massimo', 0),
                "n_quesiti": conta_quesiti_log(log)
            })
    return jsonify({"status": "success", "studenti": studenti})

@app.route('/api/teacher/student_logs', methods=['POST'])
def teacher_student_logs():
    db = carica_database()
    dati = request.get_json() or {}
    studente = dati.get('username', '').strip().lower()
    if studente in db:
        return jsonify({"status": "success", "log_sessione": db[studente].get('log_sessione', [])})
    return jsonify({"status": "error", "message": "Studente non trovato"})

@app.route('/api/teacher/get_content', methods=['GET'])
def teacher_get_content():
    pool = carica_pool_problemi()
    obiettivi = carica_obiettivi()
    return jsonify({"status": "success", "pool_problemi": pool, "obiettivi": obiettivi})

@app.route('/api/teacher/save_content', methods=['POST'])
def teacher_save_content():
    dati = request.get_json() or {}
    if 'pool_problemi' in dati:
        salva_pool_problemi(dati['pool_problemi'])
    if 'obiettivi' in dati:
        salva_obiettivi(dati['obiettivi'])
    return jsonify({"status": "success", "message": "Contenuti aggiornati correttamente!"})

@app.route('/api/chat_flow', methods=['POST'])
def chat_flow():
    db = carica_database()
    pool = carica_pool_problemi()
    payload = request.get_json() or {}
    
    username = payload.get('username', '').strip().lower()
    message = payload.get('message', '').strip()
    state = payload.get('state', {})
    
    if not state or not state.get('fase'):
        state = {
            "fase": "dialogo_iniziale",
            "dialogo_step": 0,
            "classe_studente": normalizza_classe(db.get(username, {}).get('classe', '5')),
            "livello_corrente": "medio",
            "quesito_numero": 0,
            "assess_tentativi": 0,
            "assess_risposte": [],
            "assess_problema": None,
            "assess_esito": "",
            "assess_t_start": time.time(),
            "problema_corrente": None,
            "tentativi_correnti": 0,
            "risposte_correnti": [],
            "quesito_t_start": time.time(),
            "allenamento_t_start": time.time(),
            "corretti_sessione": 0,
            "problemi_usati": {"facile": [], "medio": [], "difficile": []}
        }
        return jsonify({
            "messages": [
                {"tipo": "tutor", "testo": f"Ciao {username.capitalize()}! 👋"},
                {"tipo": "tutor", "testo": f"Vedo che sei in classe {state['classe_studente']}ª. Come va oggi?"}
            ],
            "state": state
        })
        
    messages_out = []
    fase = state['fase']
    classe_key = f"classe_{state['classe_studente']}"
    
    if fase == "dialogo_iniziale":
        if state['dialogo_step'] == 0:
            state['dialogo_step'] = 1
            messages_out.extend([
                {"tipo": "tutor", "testo": "Bene! Sono qui per aiutarti con la matematica. 😊"},
                {"tipo": "tutor", "testo": "Ti farò alcuni problemi e se avrai difficoltà ti darò degli indizi."},
                {"tipo": "tutor", "testo": "La difficoltà si adatta a te: se rispondi bene aumenta, altrimenti scende."},
                {"tipo": "tutor", "testo": "Prima inizieremo con UN problema di prova, poi ne farai altri 10. Va bene?"}
            ])
        elif state['dialogo_step'] == 1:
            if message.lower() in ['ok', 'si', 'sì', 'vai', 'va bene', 'certo', 'yes']:
                state['fase'] = "assessment"
                state['assess_tentativi'] = 0
                state['assess_risposte'] = []
                state['assess_t_start'] = time.time()
                
                options = pool.get(classe_key, {}).get('assessment', [])
                if options:
                    state['assess_problema'] = random.choice(options)
                else:
                    state['assess_problema'] = {"testo": "Marco ha 5 caramelle. Ne riceve altre 3. Quante caramelle ha ora?", "risposta": "8", "indizio_1": "Fai 5+3", "indizio_2": "Somma", "soluzione": "5+3=8"}
                
                messages_out.append({"tipo": "tutor", "testo": "Perfetto! Ecco il problema iniziale. Prenditi il tuo tempo! 💪"})
                messages_out.append({
                    "tipo": "tutor", 
                    "testo": state['assess_problema']['testo'], 
                    "immagine": state['assess_problema'].get('immagine')
                })
            else:
                messages_out.append({"tipo": "tutor", "testo": "Nessun problema! Scrivi 'ok' quando sei pronto a iniziare. 😊"})

    elif fase == "assessment":
        state['assess_tentativi'] += 1
        state['assess_risposte'].append(message)
        prob = state['assess_problema']
        
        if valida_risposta(message, prob['risposta']):
            state['assess_esito'] = "CORRETTO"
            if state['assess_tentativi'] == 1:
                state['livello_corrente'] = "difficile"
                feedback = "Ottimo! Risposta esatta al primo tentativo! 🎉"
            else:
                state['livello_corrente'] = "medio"
                feedback = "Bravo! Hai trovato la risposta! 🙂"
                
            state['fase'] = "attesa_spiegazione_assessment"
            messages_out.append({"tipo": "tutor", "testo": feedback})
            messages_out.append({"tipo": "tutor", "testo": "Spiega come ci sei arrivato."})
        else:
            if state['assess_tentativi'] == 1:
                messages_out.append({"tipo": "tutor", "testo": f"Non è corretto. {prob['indizio_1']}"})
            elif state['assess_tentativi'] == 2:
                messages_out.append({"tipo": "tutor", "testo": f"Ancora non è corretto. {prob['indizio_2']}"})
            else:
                state['livello_corrente'] = "facile"
                state['fase'] = "attesa_ok"
                tempo_assess = time.time() - state['assess_t_start']
                
                entry = {
                    "data": datetime.now().strftime("%d/%m/%Y"), "ora": datetime.now().strftime("%H:%M"),
                    "tipo": "ASSESSMENT", "classe": state['classe_studente'], "domanda": prob['testo'],
                    "tentativi": state['assess_risposte'], "livello_assigned": "facile", "esito": "ERRATO",
                    "tempo_secondi": round(tempo_assess, 1)
                }
                if username in db:
                    db[username].setdefault("log_sessione", []).append(entry)
                    salva_database(db)
                    
                messages_out.extend([
                    {"tipo": "tutor", "testo": "Hai esaurito i tentativi. Ecco la soluzione:"},
                    {"tipo": "tutor", "testo": prob['soluzione']},
                    {"tipo": "sistema", "testo": "Assessment completato! 🚀"},
                    {"tipo": "sistema", "testo": "Ora iniziano i 10 quesiti. Scrivi 'ok' quando sei pronto!"}
                ])

    elif fase == "attesa_spiegazione_assessment":
        prob = state['assess_problema']
        valida, feedback_err, punteggio, da_rivedere = valida_spiegazione_adattiva(message, prob, prob['risposta'])
        if not valida:
            messages_out.append({"tipo": "tutor", "testo": feedback_err})
        else:
            state['fase'] = "attesa_ok"
            tempo_assess = time.time() - state['assess_t_start']
            entry = {
                "data": datetime.now().strftime("%d/%m/%Y"), "ora": datetime.now().strftime("%H:%M"),
                "tipo": "ASSESSMENT", "classe": state['classe_studente'], "domanda": prob['testo'],
                "tentativi": state['assess_risposte'], "livello_assegnato": state['livello_corrente'], 
                "esito": state['assess_esito'], "tempo_secondi": round(tempo_assess, 1),
                "ragionamento": message,
                "punteggio_spiegazione": punteggio, "da_rivedere": da_rivedere
            }
            if username in db:
                db[username].setdefault("log_sessione", []).append(entry)
                salva_database(db)
                
            messages_out.extend([
                {"tipo": "tutor", "testo": feedback_err},
                {"tipo": "sistema", "testo": "Assessment completato! 🚀"},
                {"tipo": "sistema", "testo": "Ora iniziano i 10 quesiti. Scrivi 'ok' quando sei pronto!"}
            ])

    elif fase == "attesa_ok":
        if message.lower() in ['ok', 'si', 'sì', 'vai']:
            state['fase'] = "allenamento"
            state['quesito_numero'] = 1
            state['allenamento_t_start'] = time.time()
            
            prob = get_next_problema(pool, state)
            state['problema_corrente'] = prob
            state['tentativi_correnti'] = 0
            state['risposte_correnti'] = []
            state['quesito_t_start'] = time.time()
            
            messages_out.append({"tipo": "sistema", "testo": "Avvio Allenamento..."})
            messages_out.append({
                "tipo": "tutor", 
                "testo": prob['testo'], 
                "immagine": prob.get('immagine')
            })
        else:
            messages_out.append({"tipo": "tutor", "testo": "Scrivi 'ok' quando sei pronto per iniziare i 10 quesiti! 😊"})

    elif fase == "allenamento":
        state['tentativi_correnti'] += 1
        state['risposte_correnti'].append(message)
        prob = state['problema_corrente']
        
        if valida_risposta(message, prob['risposta']):
            state['fase'] = "attesa_spiegazione"
            messages_out.append({"tipo": "tutor", "testo": "CORRETTO! 🎉 Spiega come ci sei arrivato."})
        else:
            if state['tentativi_correnti'] == 1:
                messages_out.append({"tipo": "tutor", "testo": f"Non è corretto. {prob['indizio_1']}"})
            elif state['tentativi_correnti'] == 2:
                messages_out.append({"tipo": "tutor", "testo": f"Ancora non è corretto. {prob['indizio_2']}"})
            else:
                state['fase'] = "attesa_ok_prossimo"
                tempo_q = time.time() - state['quesito_t_start']
                liv_num = {'facile': 3, 'medio': 6, 'difficile': 9}[state['livello_corrente']]
                
                entry = {
                    "data": datetime.now().strftime("%d/%m/%Y"), "ora": datetime.now().strftime("%H:%M"),
                    "tipo": "QUESITO", "numero_quesito": state['quesito_numero'], "livello": liv_num,
                    "classe": state['classe_studente'], "domanda": prob['testo'], "tentativi": state['risposte_correnti'],
                    "ragionamento": "", "esito": "ERRATO", "tempo_secondi": round(tempo_q, 1),
                    "punteggio_spiegazione": 0, "da_rivedere": True
                }
                if username in db:
                    db[username].setdefault("log_sessione", []).append(entry)
                    # FIX 4: rimossa condizione morta (qui esito e' sempre ERRATO)
                    salva_database(db)
                
                messages_out.extend([
                    {"tipo": "tutor", "testo": "Hai esaurito i tentativi. Ecco la soluzione:"},
                    {"tipo": "tutor", "testo": prob['soluzione']},
                    {"tipo": "sistema", "testo": f"Quesito {state['quesito_numero']} completato ❌"}
                ])
                
                state['quesito_numero'] += 1
                state['livello_corrente'] = adatta_livello(state['livello_corrente'], False, state['tentativi_correnti'])
                
                if state['quesito_numero'] > 10:
                    messages_out.append({"tipo": "sistema", "testo": f"🏁 Hai finito! Hai risposto bene a {state.get('corretti_sessione', 0)} quesiti su 10. Ottimo lavoro! 🎉"})
                else:
                    messages_out.append({"tipo": "sistema", "testo": "Scrivi 'ok' per il prossimo."})

    elif fase == "attesa_spiegazione":
        prob = state['problema_corrente']
        valida, feedback_err, punteggio, da_rivedere = valida_spiegazione_adattiva(message, prob, prob['risposta'])
        if not valida:
            messages_out.append({"tipo": "tutor", "testo": feedback_err})
        else:
            state['fase'] = "attesa_ok_prossimo"
            tempo_q = time.time() - state['quesito_t_start']
            liv_num = {'facile': 3, 'medio': 6, 'difficile': 9}[state['livello_corrente']]
            
            entry = {
                "data": datetime.now().strftime("%d/%m/%Y"), "ora": datetime.now().strftime("%H:%M"),
                "tipo": "QUESITO", "numero_quesito": state['quesito_numero'], "livello": liv_num,
                "classe": state['classe_studente'], "domanda": prob['testo'], "tentativi": state['risposte_correnti'],
                "ragionamento": message, "esito": "CORRETTO", "tempo_secondi": round(tempo_q, 1),
                "punteggio_spiegazione": punteggio, "da_rivedere": da_rivedere
            }
            if username in db:
                db[username].setdefault("log_sessione", []).append(entry)
                if liv_num > db[username].get('livello_massimo', 0):
                    db[username]['livello_massimo'] = liv_num
                salva_database(db)
                
            messages_out.extend([
                {"tipo": "tutor", "testo": feedback_err},
                {"tipo": "sistema", "testo": f"Quesito {state['quesito_numero']} completato ✅"}
            ])
            
            state['corretti_sessione'] = state.get('corretti_sessione', 0) + 1
            state['quesito_numero'] += 1
            state['livello_corrente'] = adatta_livello(state['livello_corrente'], True, state['tentativi_correnti'])
            
            if state['quesito_numero'] > 10:
                messages_out.append({"tipo": "sistema", "testo": f"🏁 Hai finito! Hai risposto bene a {state.get('corretti_sessione', 0)} quesiti su 10. Ottimo lavoro! 🎉"})
            else:
                messages_out.append({"tipo": "sistema", "testo": "Scrivi 'ok' per il prossimo."})

    elif fase == "attesa_ok_prossimo":
        if state['quesito_numero'] > 10:
            messages_out.append({"tipo": "sistema", "testo": f"🏁 Sessione completata! {state.get('corretti_sessione', 0)} risposte giuste su 10. 👏 Puoi chiudere: la maestra vedrà i tuoi risultati."})
        elif message.lower() in ['ok', 'si', 'sì', 'vai']:
            state['fase'] = "allenamento"
            prob = get_next_problema(pool, state)
            state['problema_corrente'] = prob
            state['tentativi_correnti'] = 0
            state['risposte_correnti'] = []
            state['quesito_t_start'] = time.time()
            
            messages_out.append({
                "tipo": "tutor", 
                "testo": prob['testo'], 
                "immagine": prob.get('immagine')
            })
        else:
            messages_out.append({"tipo": "tutor", "testo": "Scrivi 'ok' per procedere al prossimo quesito! 😊"})

    return jsonify({"messages": messages_out, "state": state})

def get_next_problema(pool, state):
    classe_key = f"classe_{state['classe_studente']}"
    liv = state['livello_corrente']
    problemi_livello = pool.get(classe_key, {}).get(liv, [])
    
    if not problemi_livello:
        return {"testo": "Risolvi: 10 + 5", "risposta": "15", "indizio_1": "Somma", "indizio_2": "Fai 10+5", "soluzione": "10+5=15"}
        
    usati = state['problemi_usati'].get(liv, [])
    disponibili = [p for p in problemi_livello if p['testo'] not in usati]
    
    if not disponibili:
        state['problemi_usati'][liv] = []
        disponibili = problemi_livello
        
    scelto = random.choice(disponibili)
    state['problemi_usati'].setdefault(liv, []).append(scelto['testo'])
    return scelto

FILE_ROBOT = "robot_stato.json"

def _carica_stato_robot() -> dict:
    if os.path.exists(FILE_ROBOT):
        try:
            with open(FILE_ROBOT, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def _salva_stato_robot(d: dict):
    with open(FILE_ROBOT, "w", encoding="utf-8") as f:
        json.dump(d, f)

@app.route('/api/robot/comando', methods=['POST'])
def robot_comando():
    # Chiamato dalla pagina del tutor: memorizza l'ultimo comando per quel codice robot.
    dati = request.get_json() or {}
    codice = (dati.get('codice') or 'DASHBOT').strip().upper()
    try:
        cmd = int(dati.get('cmd'))
    except (TypeError, ValueError):
        return jsonify({"status": "error", "message": "cmd non valido"}), 400
    if not (1 <= cmd <= 6):
        return jsonify({"status": "error", "message": "cmd fuori range (1-6)"}), 400
    stato = _carica_stato_robot()
    seq = stato.get(codice, {}).get("seq", 0) + 1
    stato[codice] = {"seq": seq, "cmd": cmd, "ts": time.time()}
    _salva_stato_robot(stato)
    return jsonify({"status": "success", "seq": seq, "cmd": cmd})

@app.route('/api/robot/stato', methods=['GET'])
def robot_stato():
    # Interrogato dal robot ogni ~0,8s. Con fmt=txt risponde "SEQ,CMD" (facile da parsare su Arduino).
    codice = (request.args.get('codice') or 'DASHBOT').strip().upper()
    voce = _carica_stato_robot().get(codice, {"seq": 0, "cmd": 0})
    seq = voce.get("seq", 0)
    cmd = voce.get("cmd", 0)
    if request.args.get('fmt') == 'txt':
        return (f"{seq},{cmd}", 200, {'Content-Type': 'text/plain'})
    return jsonify({"seq": seq, "cmd": cmd})

if __name__ == '__main__':
    carica_database()
    carica_pool_problemi()
    carica_obiettivi()
    port = int(os.environ.get("PORT", 5000))
    # FIX 5: debug disattivato di default; attivabile con FLASK_DEBUG=1 in sviluppo
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
