import time
import board
import busio
import csv
import datetime
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# --- 1. PREPARATION DU FICHIER LOG ---
# On crée un nom unique avec l'heure
date_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
nom_fichier = f"rheomix_test_{date_str}.csv"

print(f"Création du fichier de sauvegarde : {nom_fichier}")

# On écrit l'en-tête des colonnes pour Excel
with open(nom_fichier, mode='w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["Heure", "Voltage_V", "Seuil_Alerte_V", "Etat_Detecte"])

# --- 2. CONFIGURATION MATERIEL ---
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)
ads.gain = 16  # Zoom Max (Indispensable pour ton batteur)
chan = AnalogIn(ads, 0, 1)

# --- 3. CALIBRAGE (Tes valeurs) ---
SEUIL_DEMARRAGE = 0.010 
SEUIL_ALERTE = 0.0370  # La frontière entre 0.034 (Liquide) et 0.040 (Visqueux)

print(f"--- RHEOMIX ENREGISTREUR ---")
print(f"Seuil Viscosité réglé à : {SEUIL_ALERTE} V")
print("CTRL+C pour arrêter et récupérer le fichier.")

def lire_vrai_voltage(duree_scan=0.5):
    max_v = 0
    start = time.time()
    while (time.time() - start) < duree_scan:
        v = abs(chan.voltage)
        if v > max_v:
            max_v = v
    return max_v

try:
    while True:
        # A. Lecture
        volts = lire_vrai_voltage(0.4)
        now = datetime.datetime.now().strftime("%H:%M:%S")
        
        # B. Analyse
        etat_texte = ""
        
        if volts < SEUIL_DEMARRAGE:
            etat_texte = "OFF"
            print(f"[{now}] V:{volts:.4f} | OFF (Veille)")
        
        elif volts < SEUIL_ALERTE:
            # Zone 0.0344
            etat_texte = "LIQUIDE"
            print(f"[{now}] V:{volts:.4f} | 🟢 LIQUIDE (Normal)")
            
        else:
            # Zone 0.0402
            etat_texte = "VISQUEUX"
            # Petit calcul pour voir si on dépasse beaucoup
            depassement = (volts - SEUIL_ALERTE) * 1000
            alerte = "!" * int(depassement)
            print(f"[{now}] V:{volts:.4f} | 🔴 VISCOSITÉ DÉTECTÉE {alerte}")

        # C. Enregistrement dans le fichier
        with open(nom_fichier, mode='a', newline='') as f:
            writer = csv.writer(f)
            # On note tout : l'heure, le voltage précis, le seuil utilisé, et le verdict
            writer.writerow([now, f"{volts:.4f}", f"{SEUIL_ALERTE}", etat_texte])

except KeyboardInterrupt:
    print(f"\nTerminé ! Tes données sont dans le fichier : {nom_fichier}")
