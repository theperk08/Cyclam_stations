import streamlit as st
import numpy as np
import pandas as pd
import json
#import geopandas as gpd

import plotly.express as px
import plotly.graph_objects as go
import matplotlib as plt
import requests

# cd Documents\Data_Analyse\Cyclam
# streamlit run Cyclam_Stations.py

# mapbox_access_token = open(".mapbox_token").read()

from st_pages import Page, show_pages #, add_page_title


# import dataset
df_stations = pd.read_csv('df_stations_cyclam_2023_octobre_sorted.csv', sep = ';')

nb_jours = 31
heure_deb = '00:00'


heures = []
for h in range(24):
    for m in range(0, 60, 15): # toutes les 15 minutes
        heures.append(str(h).zfill(2) + ':' + str(m).zfill(2))

jour = 10
jour_choisi = '2023-10-{jour}'

liste_nb_vehi = list(df_stations['vehicules.total'].unique())
if '?' in liste_nb_vehi:
    liste_nb_vehi.remove('?')   
maxi_vehi = int(max(liste_nb_vehi, key = lambda x: int(x)))


valeurs = ['rgb(0,240,0)'] * (maxi_vehi - 2)
dico_colors = {  '?' : 'rgb(128,128,128)', '0' : 'rgb(255,0,0)', '1' : 'rgb(255,165,0)', '2' : 'rgb(170,220,0)'}
dico_colors.update({ str(nombre + 3) : valeur for nombre, valeur in zip(range(20), valeurs)})

color_names = ['?', '0', '1', '2', '3+']
color_vals = list(range(len(color_names)))
color_scale = [[0, 'rgb(128,128,128)'], [0.2, 'rgb(128,128,128)'], [0.2, 'rgb(255,0,0)'], [0.4, 'rgb(255,0,0)'],[0.4, 'rgb(255,165,0)'], [0.6, 'rgb(255,165,0)'], [0.6, 'rgb(170,220,0)'],[0.8, 'rgb(170,220,0)'], [0.8, 'rgb(0,240,0)'], [1, 'rgb(0,240,0)']]
num_colors = len(color_names)

def marker_color(x):
    return dico_colors[x]

def color_station_name(color, text):
    # couleur ou gras mais pas les 2 en même temps !?
    s = '$\color{' + str(color) + '}{' + str(text) + '}$'
    #s = '$\color{' + str(color) + '}{' + str(text) + '}$'
    #s = '$\\textbf{' + str(text) + '}$'
    return s

   
liste_nom_stations = sorted(list(df_stations['name'].unique()))
ticks = sorted(liste_nom_stations)
#keys = dict(zip(ticks, colors_stats))

fig = go.Figure()

ticktext_total = []

    
df = df_stations[(df_stations['Date_heure'] >= heure_deb) & (df_stations['Date_jour'] == jour_choisi.format(jour=str(step+1).zfill(2)))].copy()
    # pour attribuer la couleur la plus présente
    #ticktext_stat = [color_station_name(dico_colors[df[df['name'] == station].groupby('vehicules.total').count()['id'].idxmax()], station) for station in liste_nom_stations ]
    
    # pour attribuer la couleur la plus basse présente (si au moins un rouge alors rouge, si au moins un jaune, alors jaune, si au moins un vert..., si que du gris alors gris)
ticktext_stat = [color_station_name(dico_colors[ df[df['name'] == station].groupby('vehicules.total').count()['id'].first_valid_index()], station) for station in liste_nom_stations ]
    
ticktext_total += [ticktext_stat]
    
fig.add_trace(
    go.Scatter(
        mode = 'markers',
            marker=dict(size = 10,
                        symbol = 'square',
                color=df['vehicules.total'].apply(lambda x: marker_color(x)),
                        colorbar=dict(title='Nb vélos',
                                      tickvals= color_vals,
                                      ticktext= color_names),
                        colorscale = color_scale,
                        cmin =  - 0.5,
                cmax = num_colors - 0.5
                        ),
            visible=False,
            #line=dict(color="#00CED1", width=6),
            name="", #jour = " + str(step+1),
            x=df['Date_heure'],
            y=df['name'],    
            
            customdata = np.stack((df['name'], df['vehicules.total']),axis=-1),
            
            hovertemplate="<br>".join(["Station : %{customdata[0]}",
                                       "Heure : %{x}",
                                       "Nombre de vélos dispo : %{customdata[1]}",
                                       
                                      ])
        )
    )



#add_page_title()
# Specify what pages should be shown in the sidebar, and what their titles 
# and icons should be
show_pages(
    [
        Page("Cyclam_Stations.py", "Statistiques stations Cyclam", "🚲"),
        #Page("pages/2_Jour_et_heure.py", "Jour et Heure", ":calendar:"),
    ]
)


# DEBUT PAGE STREAMLIT
#st.set_page_config(
#    page_title = "Circulation à Charleville-Mézières",
#    layout = "wide",
#    page_icon = "🚗")



st.markdown("<h2><center>Statistiques Nombre de vélos dispos par station Cyclam</b></center></h2>", unsafe_allow_html = True)
st.markdown("<h3 style='text-align:center;'>par jour durant un mois d'octobre", unsafe_allow_html = True)
            
            #<strong style='color:blue'>dimanche</strong> et un <strong style='color:red'>lundi</strong></h3>", unsafe_allow_html = True)

liste_jours = list(range(1,32))

st.plotly_chart(fig, use_container_width=True)

col1, col2, col3 = st.columns(3)
with col2:
    st.markdown("Choisissez le jour:")
    

    with st.form('form_1'):
        jour = st.slider(label = "Jour:",
                                min_value = 1,
                                max_value = 31, 
                                value=10,
                               step = 1
                               )
        submit1 = st.form_submit_button("OK !")    

if submit1:
    st.markdown("Vous avez choisi le " + jour + " octobre " )
    


    
infos = """
<u><strong>Infos :</strong></u>

Statistiques recuillies via API
puis traitées

<span style='color:green;'>En vert </span>: les véhicules circulent à la vitesse maximale autorisée.</span>

<strong><span style='color:yellow;'>Du jaune</span></strong> vers <strong><span style='color:orange;'>l'orange</span></strong> et <strong><span style='color:red;'>le rouge</span></strong> : les véhicules circulent de moins en moins vite par rapport à la vitesse maximale autorisée.

<strong><span style='color:gray;'>En gris</span></strong>, les routes fermées.


-----------------------------------------
Données de circulation : <a href = 'https://developer.tomtom.com/api-explorer-index/documentation/product-information/introduction'>API TomTom</a>

Fonds de carte : <a href='https://geoservices.ign.fr/presentation'>IGN</a> (licence Etalab 2.0)
"""
st.markdown(infos, unsafe_allow_html = True)