import dash
import dash_bootstrap_components as dbc
from layout import create_layout
from callbacks import register_callbacks
import pandas as pd
import os

# ============================================================
# Chargement des variables d'environnement
# En local : depuis le fichier .env (non publié sur GitHub)
# Sur Render : depuis les Environment Variables du dashboard
# ============================================================
try:
    from dotenv import load_dotenv
    load_dotenv()  # Charge .env en local uniquement
except ImportError:
    pass  # dotenv pas installé en prod = normal, Render gère

# Variables d'environnement sécurisées
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
PORT = int(os.environ.get('PORT', 8070))

# ============================================================
# Initialisation de l'application Dash
# ============================================================
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ]
)

# Configuration du serveur Flask sous-jacent
server = app.server
server.secret_key = SECRET_KEY
app.title = "DATA CARE - Optimisation des Soins Hospitaliers"

# ============================================================
# Chargement des données
# Render cherche les fichiers relatifs au dossier du projet
# ============================================================
def load_data():
    """Charge les données hospitalières avec gestion robuste des encodages."""
    # Chemins possibles (local vs Render)
    possible_paths = [
        'data/hospital_data.csv',
        'hospital_data.csv',
        os.path.join(os.path.dirname(__file__), 'data', 'hospital_data.csv'),
        os.path.join(os.path.dirname(__file__), 'hospital_data.csv'),
    ]
    
    encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'iso-8859-1', 'cp1252']
    separators = [';', ',', '\t']
    
    for path in possible_paths:
        if not os.path.exists(path):
            continue
        for encoding in encodings:
            for sep in separators:
                try:
                    df = pd.read_csv(path, encoding=encoding, sep=sep)
                    if len(df.columns) > 1:
                        print(f"✅ Fichier chargé : {path} | encodage={encoding} | sep='{sep}'")
                        df.columns = df.columns.str.strip()
                        df['DateAdmission'] = pd.to_datetime(df['DateAdmission'], format='%d/%m/%Y', dayfirst=True)
                        df['DateSortie'] = pd.to_datetime(df['DateSortie'], format='%d/%m/%Y', dayfirst=True)
                        print(f"📊 {len(df)} patients | {df['Departement'].nunique()} départements")
                        return df
                except Exception:
                    continue
    
    print("❌ Impossible de charger hospital_data.csv")
    return pd.DataFrame()

df = load_data()

# ============================================================
# Layout et Callbacks
# ============================================================
app.layout = create_layout()
register_callbacks(app, df)

# ============================================================
# Lancement
# Render utilise gunicorn avec la variable `server`
# ============================================================
if __name__ == '__main__':
    app.run(debug=DEBUG, port=PORT, host='0.0.0.0')