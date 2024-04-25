import pyodbc
import pandas as pd
import streamlit as st
import sys
import plotly.express as px
import numpy as np

o_db_dwh = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};SERVER=10.1.1.32;DATABASE=DWH;UID=sa;PWD=sas"
)
o_db_ur = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};SERVER=ur-bdd;DATABASE=UnitedRetail;UID=sa;PWD=cylande"
)

# ---------------------------------------------------------------------------------------------
# Fonctions SQL - f_getMagasinEnseigne
# ---------------------------------------------------------------------------------------------
# fonction pour récuperer la liste des magasins d'une ou plusieurs enseignes
def f_getMagasinEnseigne(p_Enseignes):
    # Préparer la liste des enseignes pour la requête SQL
    enseignes = "','".join(p_Enseignes)

    # SQL + connexion
    v_SQL = f"""
    select ENSEIGNE,CODE,NOM,PAYS,TELEPHONE
    ,cast(cast(case when LATITUDE IS not null then LATITUDE else '0.0' end as float) as decimal(18,2)) as LATITUDE
    ,cast(cast(case when LONGITUDE IS not null then LONGITUDE else '0.0' end as float) as decimal(18,2)) as LONGITUDE
    from dwh_magasin.dbo.mag_magasin 
    where date_ferme is null and TYPE<>'ENTREPOT' and ENSEIGNE IN ('{enseignes}') 
    ORDER BY ENSEIGNE,CODE ;"""

    p_DataFrame = pd.read_sql(v_SQL, o_db_dwh)

    # Reformater  
    p_DataFrame["ENSEIGNE"] = p_DataFrame["ENSEIGNE"].apply(str)
    p_DataFrame["CODE"] = p_DataFrame["CODE"].apply(str)
    p_DataFrame["NOM"] = p_DataFrame["NOM"].apply(str)
    p_DataFrame["PAYS"] = p_DataFrame["PAYS"].apply(str)

    # Renommer    
    p_DataFrame = p_DataFrame.rename(columns={"NOM": "Libellé MAG"})
    return p_DataFrame

# Variables application
# ---------------------------------------------------------------------------------------------
v_app_state = 0
v_debug_flag = True
v_app_version = 0.91

# ---------------------------------------------------------------------------------------------
# 00 - layout et titre
# ---------------------------------------------------------------------------------------------
st.title("Afficher ligne des magasins d'un enseigne")

info_col1, info_col2, info_col3, info_col4 = st.columns(4)
with info_col1:
    st.write("Streamlit : ", st.__version__)
with info_col2:
    st.write("Python : ", sys.version_info.major, ".", sys.version_info.minor)
with info_col3:
    st.write("Debug : ", v_debug_flag)
with info_col4:
    st.write("App version : ", v_app_version)


if v_app_state == 0:
    # Ajout de la checkbox pour filtrer les résultats
    w_input_cmd=st.sidebar.multiselect("Liste des enseignes", ["DPAM", "Sergent Major", "Natalys"])

    if w_input_cmd:
        st.session_state["w_cmd_input"] = w_input_cmd

        v_app_state = 1
if v_app_state == 1:
    for enseigne in st.session_state.w_cmd_input:
        w_lines_cmd_df = f_getMagasinEnseigne([enseigne])

        po=pd.DataFrame(w_lines_cmd_df['TELEPHONE'])

        #st.write(po)
        def format_with_tooltip(val, row, show_phone):
                if show_phone:
                  return f'{val} (Tél: {row["TELEPHONE"]})'
                else:
                   return val
                
        if w_lines_cmd_df is not None:  
            st.divider()
            st.subheader(f"Magasins de l'enseigne {enseigne}")
            show_phone = st.checkbox("Afficher les numéros de téléphone")

              # Vérifier si la colonne TELEPHONE existe dans le DataFrame
            if 'TELEPHONE' in w_lines_cmd_df.columns:
                 # Appliquer la fonction de formatage à la colonne "Libellé MAG"
                 w_lines_cmd_df["Libellé MAG"] = w_lines_cmd_df.apply(lambda row: format_with_tooltip(row["Libellé MAG"], row, show_phone), axis=1)

            pg=pd.DataFrame({
                "Enseigne": w_lines_cmd_df['ENSEIGNE'],
                "Code": w_lines_cmd_df['CODE'],
                "Libellé mag": w_lines_cmd_df['Libellé MAG'],
                "Pays": w_lines_cmd_df['PAYS'],
                }
              )    
            st.dataframe(pg, width=1000)
       
        # Création du camembert des pays et de leur pourcentage
        pays_counts = w_lines_cmd_df['PAYS'].value_counts()
        fig = px.pie(pays_counts, values=pays_counts.values, names=pays_counts.index, title=f'Répartition des magasins par pays pour {enseigne}')
        st.plotly_chart(fig, use_container_width=True)

        # Affichage de la carte avec des marqueurs
        #if not w_lines_cmd_df.empty:
        pf=pd.DataFrame({
              "col1": w_lines_cmd_df['LATITUDE'].values,
              "col2": w_lines_cmd_df['LONGITUDE'].values,
              #"col1": np.random.randn(1000) / 50 + 37.76,
              #"col2": np.random.randn(1000) / 50 + -122.4,
              "col3": np.random.randn(w_lines_cmd_df['CODE'].count()) * 100,
              "col4": np.random.rand(w_lines_cmd_df['CODE'].count(), 4).tolist(),
          })
        st.map(pf,
               latitude='col1',
               longitude='col2',
               size='col3',
               color='col4')
        v_app_state = 2

        #st.write(pf)

if v_app_state == 7:
    o_db_dwh.close()