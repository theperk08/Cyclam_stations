import streamlit as st

import numpy as np
import pandas as pd
import json

import folium
from streamlit_folium import st_folium

from PIL import Image
import base64

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib as plt

# cd Documents\Data_Analyse\Cyclam
# streamlit run Cyclam_Stations.py

st.set_page_config(page_title = "Statistiques stations Cyclam",
                   page_icon = "🚲",
                   layout = 'wide',
                  )

# import dataset
df_stations = pd.read_csv('df_stations_cyclam_2023_octobre_sorted.csv', sep = ';')
df_positions = pd.read_csv('df_positions_stations.csv', sep = ';')

# initialisation variables
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


# palette couleurs
c_gray = 'gray'
c_red = '#D70464'
c_orange = '#C8EEFB'  #'#C8EEFB'
c_lightblue = '#44CCED' #♥'#C8EEFB'
c_blue = '#21BBEF'

valeurs = [c_blue] * (maxi_vehi - 2)
dico_colors = {  '?' : c_gray, '0' : c_red, '1' : c_orange, '2' : c_lightblue}


dico_colors.update({ str(nombre + 3) : valeur for nombre, valeur in zip(range(20), valeurs)})

# colorbar
color_names = ['?', '0', '1', '2', '3+']
color_vals = list(range(len(color_names)))
color_scale = [[0, c_gray], [0.2, c_gray], [0.2, c_red], [0.4, c_red],[0.4, c_orange], [0.6, c_orange], [0.6, c_lightblue],[0.8, c_lightblue], [0.8, c_blue], [1, c_blue]]
num_colors = len(color_names)

liste_nom_stations = sorted(list(df_stations['name'].unique()))

# fonctions utiles

def marker_color(x):
    return dico_colors[x]


def color_station_name(color, text):   
    s = "<span style='color:{color}'>".format(color=color) + str(text) + "</span>"    
    return s
   

def df_choisi(jour, heure_deb):
    """
    récupère les données du dataset pour le #jour choisi et à partir de #heure_deb choisie
    """
    return df_stations[(df_stations['Date_heure'] >= heure_deb) & (df_stations['Date_jour'] == jour_choisi.format(jour=str(jour).zfill(2)))].copy()


def conv_h_min(hr):
    """
    convertit une durée #hr exprimée en heures, en chaîne de caractères d'heures et minutes,
    en tenant compte si 0h ou si 0min
    4.5 -> 4h30min
    6 -> 6h
    0.25 -> 15min
    """
    heure0 = ''
    hr_r = int(hr)
    if hr_r > 0:
        heure0 += str(hr_r) + 'h'
    min_r = int(60*(hr - hr_r))
    if min_r > 0:
        heure0 += str(min_r) + 'min'
        
    return heure0


def heure_rouge(df):
    df_heure = df.groupby(['Date_heure','vehicules.total']).count().reset_index()
    df_heure = df_heure[df_heure['vehicules.total'] == '0']
    liste_heures = list(df_heure[df_heure['name'] == df_heure['name'].max()]['Date_heure'])
    
    return liste_heures


def plage_heures(liste_heures):
    """
    pour formater les heures ou les plages horaires contenues dans #liste_heures
    
    """
    plage = ''
    debut = False
    compte = 0
    for i, heure in enumerate(heures):
        if heure in liste_heures:
            # on n'a pas commencé encore de plage horaire
            if debut == False:
                plage += heure # on marque le début de la plage
                debut = True
            # on compte pour savoir s'il n'y aura qu'une seule heure ou plus dans la plage
            compte += 1
        else:
            # l'heure n'est pas dans la liste
            if debut: # on termine une plage
                if compte > 1 : # qui comptait plus d'une tranche horaire
                    plage += " à " + heures[i-1] 
                debut = False
                plage += ' / '
            compte = 0
    # fin de la journée
    if debut: 
        # si plage ouverte, on la termine à minuit
        plage += ' à 00:00'
    return plage


def format_list_plage(plage_heure):
    """
    pour formater l'affichage des #plage_heure
    """
    
    liste_hr = plage_heure.split('/')
    chaine_hr = ''
    
    if len(liste_hr[0]) < 12: # si on débute par une seule heure
        chaine_hr = ' à ' + liste_hr[0]
    else:
        chaine_hr = ' de ' + liste_hr[0]
    for hr in liste_hr[1:]:
        if len(hr) > 2:
            if len(hr) < 12:
                chaine_hr += ', à ' + hr
            else:
                chaine_hr += ', de ' + hr
    return chaine_hr


def nombre_stat(df):
    """
    pour obtenir les stats (nombre mini, nombre moy et nombre maxi)
    des stations du #df
    """
    nombre_stat_min = []
    nombre_stat_max = []
    nombre_stat_moy = []
    for station in liste_nom_stations:
        df4 = df[df['name'] == station].groupby('vehicules.total').count()['name']
        df4.drop(df4[df4.index == '?'].index, inplace = True)
        nombre_stat_min += [ df4.first_valid_index()]
        nombre_stat_max += [ df4.last_valid_index()]
        df4 = df4.reset_index()        
        df4['vehicules.total']= df4['vehicules.total'].astype('Int64')        
        nombre_stat_moy += [np.average(df4['vehicules.total'], weights = df4['name'])]
        
    return {'n_min': nombre_stat_min, 'n_moy' : nombre_stat_moy, 'n_max' : nombre_stat_max}


def bicolor(color1, color2, text):
    """
    fonction qui affiche les caractères d'une chaîne #text en couleurs alternées, #color1 puis #color2
    """
    chaine = ''.join(["<span style ='color:" + (color1 if i%2 == 0 else color2) + "'>" + text[i] + "</span>" for i in range(len(text))])
    return chaine


# fonctions pour créer les graphiques

def graphique(jour, df, nombre_stats):
    """
    graphique à bar horizontal du nombre de vélos dispo par station et par heure durant la journée
    en x : les heures
    en y : les noms des stations
     mais sur axe des y : remplacement des ticks par des annotations pour pouvoir formater l'affichage
    avec une colorbar
    """
    fig = go.Figure()
    
    ticktext_total = []   
    # affichage des yticks de la même couleur que la couleur de fond de l'appli (cf fichier config.toml)
    # pour qu'ils n'apparaissent pas mais qu'ils laissent leur place aux annotations
    ticktext_stat = [color_station_name("#F5F5FF", station) for k, station in enumerate(liste_nom_stations)]
      
    fig.add_trace(
        go.Scatter(
            mode = 'markers',
            marker = dict(size = 10,
                          symbol = 'square',
                          color = df['vehicules.total'].apply(lambda x: marker_color(x)),
                          colorbar = dict(title = 'Nb vélos',
                                        tickvals = color_vals,
                                        ticktext = color_names),
                          colorscale = color_scale,
                          cmin = - 0.5,
                          cmax = num_colors - 0.5
                         ),
            hoverlabel = dict(bgcolor = df['vehicules.total'].apply(lambda x: marker_color(x)),
                              font_color = df['vehicules.total'].apply(lambda x : 'black' if x != '0' else 'white')),
            visible = True,            
            name = "", 
            x = df['Date_heure'],
            y = df['name'],
            customdata = np.stack((df['name'], df['vehicules.total'], df['Date_heure']), axis = -1),
            hovertemplate = "<br>".join(["Station : %{customdata[0]}",
                                         "Heure : %{customdata[2]}",
                                         "Nombre de vélos dispo : %{customdata[1]}",
                                        ])
        )
    )
    
    annotations = [dict(x = 0,
                        y = station,
                        xref = 'paper',
                        yref = 'y',
                        text = station,
                        xanchor = 'right',
                        bgcolor = dico_colors[str(round(nombre_stats['n_moy'][k]))],
                        font_color = "#444444" if round(nombre_stats['n_moy'][k]) >0 else "#FFFFFF",
                        showarrow = False) for k, station in enumerate(liste_nom_stations)]
       
    fig.update_layout(title = dict({'text' : 'Nombre de vélos dispo par station durant la journée',  # <b>' + str(jour) + ' octobre</b>',
                                'x' : 0.5,
                                'xanchor': 'center'}),
                      # on affiche quand même les yticks, pour que les annotations puissent prendre leur place
                      yaxis = dict(showgrid = False, tickmode = 'array', ticktext = ticktext_stat, tickvals = liste_nom_stations),
                      annotations = annotations,
                      plot_bgcolor = 'rgba(0,0,0,0)',
                      width = 800,
                      height = 560,
                      xaxis = dict(showgrid = False,
                                   visible = True,
                                   showticklabels = True,
                                   tickmode = 'array',
                                   tickvals = [heure if j%4 == 0 else '' for j, heure in enumerate(heures[heures.index(heure_deb):])],
                                   ticktext = ['<span style="color:black">{}</span> '.format(heure) if j%4 == 0 else '' for j, heure in enumerate(heures[heures.index(heure_deb):])],
                                   ticks = "outside",
                                  ),
                      margin = dict(l = 5, r = 2, t = 35, b = 5),
                     )
    
    st.plotly_chart(fig, use_container_width=True)
    

def pie_rouge(df):
    """
    pour afficher (sous forme de pneu)
    la station le plus souvent sans vélo dispo
    """
    
    liste_rouge = [df[df['name'] == station].groupby('vehicules.total').count()['name'] for station in liste_nom_stations]
    numero_rouge = -1
    nb_rouge = 0
    for ni, liste_st in enumerate(liste_rouge):
        if '0' in liste_st.index: # si la station a été dans le rouge
            if liste_st.loc['0'] > nb_rouge:
                nb_rouge = liste_st.loc['0']
                numero_rouge = ni
    if numero_rouge >= 0:
        df_rouge = pd.DataFrame(liste_rouge[numero_rouge]).reset_index().sort_values('vehicules.total')
        df_rouge['Nombre_heures'] = df_rouge['name'].apply(lambda x : str((15*x)//60) + " h " + (str((15*x)%60) + ' m' if (15*x)%60 >0 else ''))
        temps_max = str(df_rouge.loc[df_rouge['vehicules.total'] == '0', 'Nombre_heures'].item())
        
        fig_rouge = fig = go.Figure(data=[go.Pie(labels = df_rouge['vehicules.total'],
                                                 values = df_rouge['name'],
                                                 hole = .4,
                                                 marker = dict(colors = df_rouge['vehicules.total'].apply(lambda x: marker_color(x))),
                                                 customdata = df_rouge['Nombre_heures'],
                                                 hovertemplate = "<br>".join(["Nb vélos dispos : %{label}",
                                                                            "pendant : %{customdata}",
                                                                            "soit %{percent} du temps",]),
                                                 hoverlabel = dict(bgcolor=df_rouge['vehicules.total'].apply(lambda x: marker_color(x)),
                                                                  font_color = df_rouge['vehicules.total'].apply(lambda x : 'black' if x != '0' else 'white')),
                                                 name = '',
                                                 domain = dict(x =[0.25, 0.75], y= [0.1, 0.9]),
                                                 sort = False, # pour ne pas retrier suivant les values, car je veux suivant les labels
                                                 direction ='clockwise' # et que ça s'affiche bien dans l'ordre horaire
                                                )],
                                   )
        
        fig_rouge.update_traces(textinfo ='none')
        
        fig_rouge.update_layout(height = 250,
                                width = 250,                                
                                autosize = False,
                                margin = dict(l = 0, t = 0, b = 0, r = 0),
                                showlegend = False,
                                xaxis = dict(showgrid = False,
                                             visible = False,
                                             showticklabels = False
                                            ),
                                yaxis = dict(showgrid = False,
                                             visible = False,
                                             showticklabels = False
                                            ),
                                uniformtext_minsize = 15, uniformtext_mode = 'hide',
                                annotations = [dict(text = temps_max, font_size = 18, bgcolor = c_red, font_color = 'white', showarrow = False)],
                                paper_bgcolor = 'rgba(0,0,0,0)', #transparence
                                plot_bgcolor = 'rgba(0,0,0,0)') 
        
        # on rajoute une image autour du pie
        fig_rouge.add_layout_image(dict(source = Image.open("images/pneu1.png"),
                                        # axes de référence
                                        xref = "x",
                                        yref = "y",
                                        # coordonnées (du centre car xanchor = 'center' et yanchor = 'middle')
                                        x = 2.5,
                                        y = 1.5,
                                        # taille image en x et y suivant les axes de référence
                                        sizex = 1.1,
                                        sizey = 2.1,
                                        xanchor = 'center',
                                        yanchor = 'middle',
                                        # façon de placer l'image
                                        sizing = 'contain', #  ['fill', 'contain', 'stretch']
                                        opacity = 0.75,
                                        layer = "above")) #below
        
        st.markdown("<h4 style='color:{c_red};text-align:center;'>".format(c_red = c_red) + liste_nom_stations[numero_rouge]  + "</h4><p style='text-align:center'> (Station le plus souvent sans vélo dispo :<br> pendant {:s})</p>".format(temps_max), unsafe_allow_html = True)
        
        st.plotly_chart(fig_rouge, use_container_width=True)
        
        return fig_rouge #.data, fig_rouge.layout        
        
    else:
        st.markdown('Aucune station dans le rouge pour ce jour-là')
        
        
def pie_bleu(df, nombre_stats):
    """
    pour afficher (sous forme de pneu)
    la station ayant le plus de vélos dispos en moyenne sur la journée
    """
    
    liste_bleu = [df[df['name'] == station].groupby('vehicules.total').count()['name'] for station in liste_nom_stations]
    
    n_moy_idxmaxi = pd.Series(nombre_stats['n_moy']).idxmax()
    n_moy_maxi = max(nombre_stats['n_moy'])                
   
    if True:
        df_bleu = pd.DataFrame(liste_bleu[n_moy_idxmaxi]).reset_index().sort_values('vehicules.total')
        df_bleu['Nombre_heures'] = df_bleu['name'].apply(lambda x : str((15*x)//60) + " h " + str((15*x)%60) + ' min')
        fig_bleue = fig = go.Figure(data=[go.Pie(labels = df_bleu['vehicules.total'],
                                                 values = df_bleu['name'],
                                                 hole = .4,
                                                 marker = dict(colors = df_bleu['vehicules.total'].apply(lambda x: marker_color(x))),
                                                 textinfo = 'percent+label',
                                                 customdata = df_bleu['Nombre_heures'],
                                                 hovertemplate="<br>".join(["Nb vélos dispos : %{label}",
                                                                            "pendant : %{customdata}",
                                                                            "soit %{percent} du temps",]),
                                                 hoverlabel = dict(bgcolor=df_bleu['vehicules.total'].apply(lambda x: marker_color(x)),
                                                                  font_color = 'black'),
                                                 name = '',
                                                 domain = dict(x = [0.25, 0.75], y = [0.1, 0.9]),
                                                 sort = False,
                                                 direction ='clockwise'
                                                )],
                                   )
        fig_bleue.update_traces(textinfo = 'none') #textposition='inside')
        fig_bleue.update_layout(height = 250,
                                width = 250,
                                autosize = False,
                                margin = dict(l = 0, t = 0, b = 0, r = 0),
                                showlegend = False,
                                xaxis = dict(showgrid = False,
                                             visible = False,
                                             showticklabels = False,
                                            ),
                                yaxis = dict(showgrid = False,
                                             visible = False,
                                             showticklabels = False,
                                            ),
                                uniformtext_minsize = 15, uniformtext_mode = 'hide',
                                annotations = [dict(text = str(round(n_moy_maxi,1)), font_size = 22, bgcolor = marker_color(str(int(n_moy_maxi))), font_color = 'white', showarrow = False)],
                                paper_bgcolor = 'rgba(0,0,0,0)', #transparence
                                plot_bgcolor = 'rgba(0,0,0,0)') 
        
        fig_bleue.add_layout_image(dict(source = Image.open("images/pneu1.png"),
                                        xref = "x",
                                        yref = "y",
                                        x = 2.5,
                                        y = 1.5,
                                        sizex = 1.1,
                                        sizey = 2.1,
                                        xanchor = 'center',
                                        yanchor = 'middle',
                                        sizing = 'contain', #  ['fill', 'contain', 'stretch']
                                        opacity = 0.75,
                                        layer = "above")) #below
        
        st.markdown("<h4 style='color:{c_blue};text-align:center;'>".format(c_blue=c_blue) + liste_nom_stations[n_moy_idxmaxi] + "</h4><p style='text-align:center'> (station ayant le plus de vélos dispos :<br>{:s} en moyenne)</p>".format(str(round(n_moy_maxi,1))), unsafe_allow_html = True)
        
        st.plotly_chart(fig_bleue, use_container_width=True)
        
        return fig_bleue        
        
    else:
        st.markdown('Aucune station dans le rouge pour ce jour-là')
        
    
def graph_jour_total(df):
    """
    graphique à bar vertical pour avoir le nombre d'heures
    pendant lesquelles les stations contiennent un certain nombre de vélos dispos
    en x : le nombre de vélos
    en y : heure totale cumulée pour toutes les stations
    """
    df_heure_tot = df.groupby(['vehicules.total']).count().reset_index()
    fig_jour = go.Figure(go.Bar(x = df_heure_tot["vehicules.total"],
                                y = df_heure_tot["name"]/4,
                                marker = dict(color = df_heure_tot['vehicules.total'].apply(lambda x: marker_color(x))),
                                #text_auto=True
                                customdata = np.stack(((df_heure_tot['name']/4).apply(conv_h_min), df_heure_tot['vehicules.total']), axis =-1),
                                hovertemplate="<br>".join(["Nb vélos dispo : %{customdata[1]}",
                                                                            "pendant : %{customdata[0]}",
                                                                            ]),
                                hoverlabel = dict(bgcolor=df_heure_tot['vehicules.total'].apply(lambda x: marker_color(x)),
                                                                  font_color = df_heure_tot['vehicules.total'].apply(lambda x : 'black' if x !='0' else 'white')),
                                name = '',
                                text = df_heure_tot["name"].apply(lambda x : str(x/4) + 'h')
                               )                         
                        )
    nb_hr_rouge0 = df_heure_tot[df_heure_tot['vehicules.total'] == '0']['name'].item() / 4    
    heure_rouge0 = conv_h_min(nb_hr_rouge0)    
    hr_r = int(nb_hr_rouge0)
    
    fig_jour.update_traces(textfont_color = 'black', textfont_size = 12, textangle = 0, textposition = "outside", cliponaxis = False)
    
    fig_jour.update_layout(height = 300,
                           xaxis = dict(showgrid = False,
                                      visible = True,
                                      tickmode = 'array',
                                      tickvals = list(df_heure_tot['vehicules.total'].unique()),
                                      ticktext = [color_station_name(dico_colors[nombre],nombre ) for nombre in list(df_heure_tot['vehicules.total'].unique())],
                                      ticks = 'outside'),
                           xaxis_title = dict(text = "Nombre de vélos dispos par station", font_size = 15, font_color = 'black'),
                           yaxis = dict(showgrid = False,
                                        visible = False,
                                        showticklabels = False
                                       ),                          
                           margin = dict(l = 0, r = 0, t = 40, b = 50),                           
                           paper_bgcolor = 'rgba(0,0,0,0)', #transparence
                           plot_bgcolor = 'rgba(0,0,0,0)'
                          )
    # une flèche pour montrer à quoi correspond le titre
    fig_jour.add_annotation(x = '0',
                            y = hr_r + 20,
                            ax = '0',
                            ay = 1.1*int(df_heure_tot['name'].max()/4),
                            xref = 'x',
                            yref = 'y',
                            axref = 'x',
                            ayref = 'y',
                            text = '',
                            showarrow = True,
                            arrowhead = 1, # une seule tête de flèche, et non pas 2
                            arrowsize = 1,
                            arrowwidth = 5,
                            arrowcolor = c_red
                           )
    
    title_text = "<h4 style='color:{c_red};font-size:20;text-align:center'>Pendant ".format(c_red=c_red) + heure_rouge0 + " il y a eu 0 vélo dispo aux stations</h4>"
    st.markdown(title_text , unsafe_allow_html = True)
    st.plotly_chart(fig_jour, use_container_width=True)
    
    
def graph_jour_heure(df, liste_heure_rouge):
    """
    graph à bar vertical (empilé)
    pour avoir la répartition horaire du nombre de stations
    ayant un certain nombre de vélos dispos
    en x : les heures
    en y : le nombre de station (empilé) par nombre(croissant) de vélos dispos
    """
    
    custom_dict = {i : (int(i) if i != '?' else 1000) for i in list(df['vehicules.total'].unique())}
    df['rank'] = df['vehicules.total'].map(custom_dict)   
    df_heure = df.groupby(['Date_heure','rank']).agg(name =('name', 'count'), vehicules = ('vehicules.total' , 'first')).reset_index()
    
    fig_jour_heure = go.Figure(go.Bar(x = df_heure["Date_heure"],
                                      y = df_heure["name"],
                                      marker = dict(color = df_heure['vehicules'].apply(lambda x: marker_color(x))),
                                      # les heures sont formatées par les ticks, mais j'en ai besoin sans formattage pour le hover
                                      customdata = np.stack((df_heure['vehicules'], df_heure['Date_heure']), axis = -1), #façon de regrouper plusieurs customdata  
                                      hovertemplate="<br>".join(["Nb vélos dispo : %{customdata[0]}",
                                                                 "Pour %{y} stations",
                                                                 "à %{customdata[1]}",
                                                                ]),
                                      hoverlabel = dict(bgcolor = df_heure['vehicules'].apply(lambda x: marker_color(x)),
                                                                  font_color = df_heure['vehicules'].apply(lambda x: 'black' if x!='0' else 'white')),
                                      name = '',
                                     )
                              )
    ticktext = [color_station_name( (c_red if heure in liste_heure_rouge else 'black'), heure) for heure in list(df_heure["Date_heure"].unique())[::4]]
    
    fig_jour_heure.update_layout(margin = dict(l = 0, r = 0, t = 0, b = 0),
                                 height = 250,
                                 xaxis = dict(showgrid = False,
                                              visible = True,
                                              tickmode = 'array',
                                              tickvals = list(df_heure['Date_heure'].unique())[::4],
                                              ticktext = ticktext,
                                              ticks = 'outside'
                                             ),
                                )
    
    st.plotly_chart(fig_jour_heure, use_container_width = True)   


def graph_classement(df, nombre_stats): 
    """
    affichage du classement des stations suivant le nombre moyen de vélos dispos
    encadré par une image de borne de recharge
    """
    dico_moy = {station : nombre_stats['n_moy'][k] for k, station in enumerate(liste_nom_stations)}
    dico_class = sorted(dico_moy.items(), key=lambda x: x[1])
    dico_class_noms =  [x[0] for x in dico_class]
    dico_class_1 = [1] * len(dico_class_noms)
    dico_class_val = [round(x[1],1) for x in dico_class]    
    fig_class = go.Figure()
    
    fig_class.add_trace(
        go.Bar(marker = dict(color = [marker_color(str(round(x[1]))) for x in dico_class],
                            ),
               hoverlabel = dict(bgcolor = [marker_color(str(round(x[1]))) for x in dico_class],
                                 font_color = ['black' if round(x[1]) >0 else 'white' for x in dico_class]),
               visible = True,
               name = "",
               x = dico_class_1,
               y = dico_class_1,
               text = dico_class_noms,
               customdata = np.stack((dico_class_noms, dico_class_val), axis = -1),
               hovertemplate = "<br>".join(["Station : %{customdata[0]}",
                                            "Nombre de vélos dispo en moyenne : %{customdata[1]}",
                                           ])
              )
    )
    
    fig_class.update_traces(textfont_size = 12, textangle = 0, textposition = "inside", cliponaxis = False)
    
    fig_class.update_layout(title = dict(text = 'Classement des stations par<br>nombre moyen de vélos dispo', x = 0.5, xanchor = 'center'  ),
                            height = 900,
                            width = 350,
                            autosize = False,
                            margin = dict(l = 0, t = 50, b = 0, r = 0),
                            showlegend = False,
                            xaxis = dict(showgrid = False,
                                         visible = False,
                                         showticklabels = False,
                                         range = [0.4, 1.6]
                                        ),
                            yaxis = dict(showgrid = False,
                                         visible = False,
                                         showticklabels = False,
                                         range = [-3, 25]
                                        ),
                            paper_bgcolor = 'rgba(0,0,0,0)', #transparence
                            plot_bgcolor = 'rgba(0,0,0,0)')
    
    # ajout image borne encadrant le graphique
    fig_class.add_layout_image(dict(source = Image.open("images/borne1.png"),
                                    xref = "x",
                                    yref = "y",
                                    x = 1.01,
                                    y = len(dico_class_noms) / 2,
                                    sizex = 1.12,
                                    sizey = 1.09*len(dico_class_noms),
                                    xanchor = 'center',
                                    yanchor = 'middle',
                                    sizing = 'stretch', #  ['fill', 'contain', 'stretch']
                                    opacity = 1,
                                    layer = "above")) #below
    
    st.plotly_chart(fig_class, use_container_width = True)


def map_folium(df, nombre_stats):
    """
    affichage des emplacements des stations
    avec un marker colorisé en fonction du nombre moyen de vélos dispos
    """
    
    dico_color_map = {'0' : 'red', '1' : 'lightblue', '2' : 'blue', '?': 'gray', '3': 'blue'}
    dico_color_map.update({str(4+i): 'blue' for i in range(maxi_vehi)})
    
    m = folium.Map(location = [49.74, 4.83], zoom_start = 10.5)   
    
    # on récupère les coord des stations
    #df_stat = df.groupby(['name']).agg({'position.latitude' : 'first', 'position.longitude' :'first'}).reset_index()
    
    for station in liste_nom_stations:
        pass
    
    # on place les stations sur la carte
    for k, station in enumerate(liste_nom_stations):        
        #point = [df_stat.loc[df_stat['name'] == station, 'position.latitude'], df_stat.loc[df_stat['name'] == station, 'position.longitude']] 
        point = [df_positions.loc[k, 'latitude'], df_positions.loc[k, 'longitude']]
        # création d'un bel affichage popup avec les stats de la station
        html = '<link rel="stylesheet" href="https://site-assets.fontawesome.com/releases/v6.4.2/css/all.css">' + station + '<br>' + '<br>'
        html += "<span style='color:{:s}'>Nb vélos dispo min : ".format(dico_color_map[str(nombre_stats['n_min'][k])]) + str(nombre_stats['n_min'][k]) + '</span><br>'
        html += "<span style='color:{:s}'>Nb vélos dispo moy : ".format(dico_color_map[str(round(nombre_stats['n_moy'][k]))]) + str(round(nombre_stats['n_moy'][k],1))  + '<br>'
        html += "<span style='color:{:s}'>Nb vélos dispo max : ".format(dico_color_map[str(nombre_stats['n_max'][k])]) +  str(nombre_stats['n_max'][k])  + '<br>'
   
        iframe = folium.IFrame(html,
                               width = 290,
                               height = 140)
        popup = folium.Popup(iframe,
                             max_width=270)
    
        # ajout du marker avec son popup personnalisé, colorisé suivant le nombre moyen de vélos dispos
        folium.Marker(location = point,
                      popup = popup,
                      icon=folium.Icon(color = dico_color_map[str(round(nombre_stats['n_moy'][k]))], icon = "fa-solid fa-bicycle",prefix='fa')
                     ).add_to(m)
               
    st_map = st_folium(m, width=390, height =400)     

        
# DEBUT PAGE STREAMLIT

col00, col01, col02, col03, col04 = st.columns([3,2,12,2,3])
with col01:
    st.image('images/Electric_bike_blue.png',use_column_width = True)
        
with col02:
    st.markdown("<h2><center>" + bicolor(c_blue, c_red, 'Statistiques du nombre de vélos dispos par station Cyclam') + "</b></center></h2>", unsafe_allow_html = True)
    st.markdown("<h5 style='text-align:center;'>par jour durant un mois d'octobre</h5>", unsafe_allow_html = True)
        
with col03:
    st.image('images/Electric_bike_red.png',use_column_width = True)
        
st.markdown("Choisissez le jour du mois :")
        
df = df_choisi(jour, heure_deb)
 
# pour éviter un pb de rafraîchement automatique de la folium.map
try:
    # check if the key exists in session state
    _ = st.session_state.keep_graphics
except AttributeError:
    # otherwise set it to false
    st.session_state.keep_graphics = False




#with st.form('form_1'):
    
jour = st.select_slider(label = "",
                        options = list(range(1, nb_jours + 1)),
                                #min_value = 1,
                                #max_value = nb_jours, 
                                value=10,                               
                               )
    #submit1 = st.form_submit_button("OK !")
            

if jour or st.session_state.keep_graphics: #submit1 or st.session_state.keep_graphics:
    st.session_state.keep_graphics = True
   
    df = df_choisi(jour, heure_deb)
    liste_heure_rouge = heure_rouge(df)
    nombre_stats = nombre_stat(df)
    
    jour_c = str(jour) if jour > 1 else '1er'
    
    st.markdown("<h4 style='text-align:center;background-color:#ededed'>" + bicolor(c_blue, c_red, "Journée du {jour} octobre".format(jour=jour_c)), unsafe_allow_html = True)
    
    col1, col2, col3 = st.columns([4,8,10])     
    with col1:
        cont0 = st.container()
        with cont0:
            graph_classement(df, nombre_stats)        
        
    with col2:
        cont1 = st.container()
        with cont1:
            col1b, col1c = st.columns(2)
            with col1b:
                f_rouge = pie_rouge(df)
            with col1c:
                f_bleu= pie_bleu(df, nombre_stats)
                
        cont1b = st.container()
        with cont1b:
            graphique(jour, df, nombre_stats)
        
    with col3:
        cont2 = st.container()
        with cont2:
            col2b, col2c = st.columns(2)
            with col2b:
                graph_jour_total(df)
            with col2c:
                map_folium(df, nombre_stats)
                
        cont2b = st.container()
        with cont2b:
            liste_plages_rouge = plage_heures(liste_heure_rouge)
            info_heure = "<p style='color:{c_red};text-align:center'>Il y a le plus de stations sans vélo dispo</p><h5 style ='text-align:center;color:{c_red}'>".format(c_red=c_red) + str(format_list_plage(liste_plages_rouge)) + "</h5>"
            st.markdown(info_heure, unsafe_allow_html = True)
            graph_jour_heure(df, liste_heure_rouge)
            
    
        
    
    
   
                                                     
    
    


    
infos = """
----------------------------------------


<u><strong>Infos :</strong></u>  
Les données affichées sont basées sur des données recueillies en temps réel via API toutes les 15 minutes,  
mais restent purement indicatives (des vélos peuvent être loués entre deux relevés).

- Statistiques recueillies toutes les 15 minutes via API
- traitement python : pandas
- graphiques : plotly, folium
- application et mise en ligne : streamlit
- images (vélo, pneu, borne) avec quelques modifications conformément à la license : <a href='https://pixabay.com'> Pixabay</a>



-----------------------------------------

"""
st.markdown(infos, unsafe_allow_html = True)
