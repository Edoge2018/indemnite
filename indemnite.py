import streamlit as st
import pandas as pd

# ------------------------------
# Configuration de la page
# ------------------------------
st.set_page_config(
    page_title="Calcul des indemnités de transport",
    page_icon="🚗",
    layout="wide"
)

# ------------------------------
# Style personnalisé
# ------------------------------
st.markdown(
    """
    <style>
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 8px 16px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 14px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 6px;
    }
    .stSelectbox, .stMultiSelect, .stTextInput, .stDataFrame {
        border-radius: 6px;
        border: 1px solid #ddd;
        padding: 8px;
    }
    .stWarning, .stError {
        border-radius: 6px;
        padding: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ------------------------------
# Fonctions utilitaires
# ------------------------------
def normalize(name):
    """Normaliser les noms : minuscules, sans espaces, sans tirets, sans accents."""
    if not isinstance(name, str):
        return ""
    name = str(name).strip().lower()
    name = name.replace(" ", "").replace("-", "")
    name = name.replace("é", "e").replace("è", "e").replace("ê", "e")
    name = name.replace("à", "a").replace("â", "a")
    name = name.replace("ù", "u").replace("û", "u")
    name = name.replace("î", "i").replace("ï", "i")
    name = name.replace("ô", "o")
    return name

# ------------------------------
# Chargement des données
# ------------------------------
@st.cache_data
def load_data(file_input):
    df_distances = pd.read_excel(file_input, sheet_name='Distances inter-communes km')
    df_tarifs = pd.read_excel(file_input, sheet_name='Tarif aller simple')

    # Normaliser les noms des communes dans les deux DataFrames
    df_distances['Commune_norm'] = df_distances['Unnamed: 1'].fillna("").apply(normalize)
    df_tarifs['Commune_norm'] = df_tarifs['Unnamed: 1'].fillna("").apply(normalize)

    return df_distances, df_tarifs

# ------------------------------
# Interface Streamlit
# ------------------------------
st.title("🚗 Calcul des indemnités de transport")
st.markdown("---")

# Charger le fichier Excel
file_input = st.file_uploader(
    "**Importer le fichier Excel des distances et tarifs**",
    type=["xlsx"],
    key="file_uploader"
)

if file_input:
    df_distances, df_tarifs = load_data(file_input)

    # Liste des communes d'arrivée disponibles
    communes_arrivee_disponibles = df_tarifs['Unnamed: 1'].dropna().unique().tolist()

    # Sélection d'une seule commune d'arrivée
    commune_arrivee = st.selectbox(
        "**Sélectionnez la commune d'arrivée**",
        options=communes_arrivee_disponibles,
        key="commune_arrivee"
    )

    if commune_arrivee:
        # Trouver la ligne de tarif pour la commune d'arrivée
        commune_arrivee_norm = normalize(commune_arrivee)
        ligne_tarif_arrivee = df_tarifs[df_tarifs['Commune_norm'] == commune_arrivee_norm]

        if ligne_tarif_arrivee.empty:
            st.error(f"Erreur : La commune d'arrivée **{commune_arrivee}** n'a pas été trouvée dans la feuille 'Tarif aller simple'.")
        else:
            ligne_tarif_arrivee = ligne_tarif_arrivee.iloc[0]

            # Liste des communes de départ disponibles
            communes_depart_disponibles = df_distances['Unnamed: 1'].dropna().unique().tolist()

            # Sélection multiple des communes de départ
            communes_depart = st.multiselect(
                "**Sélectionnez une ou plusieurs communes de départ**",
                options=communes_depart_disponibles,
                key="communes_depart"
            )

            if communes_depart:
                # Calcul des indemnités pour toutes les combinaisons
                all_results = []
                communes_non_trouvees = []

                for dep in communes_depart:
                    try:
                        dep_norm = normalize(dep)
                        code_dep = df_distances[df_distances['Commune_norm'] == dep_norm]['Unnamed: 0'].values
                        if len(code_dep) == 0:
                            communes_non_trouvees.append(dep)
                            continue
                        code_dep = code_dep[0]

                        if str(code_dep) in ligne_tarif_arrivee.index:
                            tarif_aller = ligne_tarif_arrivee[str(code_dep)]
                            total_ar = tarif_aller * 2 + 2000  # Forfait interne de 2000 FCFA
                            all_results.append({
                                'Commune d\'arrivée': commune_arrivee,
                                'Commune de départ': dep,
                                'Total Aller-Retour + Forfait 2000 FCFA': total_ar
                            })
                        else:
                            communes_non_trouvees.append(dep)
                    except Exception as e:
                        communes_non_trouvees.append(dep)
                        st.error(f"Erreur pour {dep}: {str(e)}")

                # Afficher le bloc DataFrame unique
                if all_results:
                    df_all_results = pd.DataFrame(all_results)
                    st.subheader("**Résultats des indemnités**")
                    st.dataframe(df_all_results, use_container_width=True)

                    # Bouton pour exporter vers Excel
                    st.markdown("---")
                    if st.button("📥 Exporter vers Excel", key="exporter_excel"):
                        df_all_results.to_excel("Indemnites_aller_retour_avec_forfait.xlsx", index=False)
                        st.success("Fichier exporté avec succès : **Indemnites_aller_retour_avec_forfait.xlsx**")
                else:
                    st.warning("Aucun résultat à afficher. Vérifiez les communes sélectionnées.")

                # Afficher les communes de départ non trouvées
                if communes_non_trouvees:
                    st.subheader("**Communes de départ introuvables**")
                    for c in set(communes_non_trouvees):
                        st.warning(f"- {c}")