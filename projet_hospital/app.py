import dash
import dash_bootstrap_components as dbc
from layout import create_layout
from callbacks import register_callbacks
import pandas as pd

# Initialisation de l'application Dash
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ]
)

# Configuration du serveur
server = app.server
app.title = "DATA CARE - Optimisation des Soins Hospitaliers"

# Chargement des données
try:
    # Essayer différents encodages et séparateurs
    encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'iso-8859-1', 'cp1252']
    separators = [';', ',', '\t']
    df = None
    
    for encoding in encodings:
        for sep in separators:
            try:
                df = pd.read_csv('data/hospital_data.csv', encoding=encoding, sep=sep)
                # Vérifier si on a bien plusieurs colonnes
                if len(df.columns) > 1:
                    print(f"✅ Fichier chargé avec l'encodage {encoding} et séparateur '{sep}'")
                    break
            except:
                continue
        if df is not None and len(df.columns) > 1:
            break
    
    if df is None or len(df.columns) == 1:
        raise Exception("Impossible de charger le fichier avec les encodages/séparateurs testés")
    
    # Afficher les colonnes pour déboguer
    print(f"📊 Colonnes détectées : {df.columns.tolist()}")
    print(f"📊 Nombre de colonnes : {len(df.columns)}")
    print(f"📊 Nombre de lignes : {len(df)}")
    
    # Nettoyer les noms de colonnes (enlever espaces et caractères spéciaux)
    df.columns = df.columns.str.strip()
    
    # Convertir les dates au format dd/mm/yyyy
    df['DateAdmission'] = pd.to_datetime(df['DateAdmission'], format='%d/%m/%Y', dayfirst=True)
    df['DateSortie'] = pd.to_datetime(df['DateSortie'], format='%d/%m/%Y', dayfirst=True)
    
    print(f"✅ Données chargées avec succès : {len(df)} patients")
    print(f"📅 Période couverte : {df['DateAdmission'].min().strftime('%d/%m/%Y')} à {df['DateAdmission'].max().strftime('%d/%m/%Y')}")
    print(f"🏥 Départements : {df['Departement'].nunique()} départements uniques")
    
except Exception as e:
    print(f"❌ Erreur lors du chargement des données : {e}")
    import traceback
    traceback.print_exc()
    df = pd.DataFrame()

# Création du layout
app.layout = create_layout()

# Enregistrement des callbacks
register_callbacks(app, df)

if __name__ == '__main__':
    app.run(debug=True, port=8070)