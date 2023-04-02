import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import plotly.express as px
import folium
from streamlit_folium import folium_static
import datetime
import plotly.graph_objects as go



st.set_page_config(page_title="NYC Motor Collision Analysis",page_icon=":car:", layout = "wide")


def add_bg_from_url():
    st.markdown(
         f"""
         <style>
         .stApp {{
             background-image: url("https://lh3.googleusercontent.com/crF-YalvNyu8MwaTtlsfR5BN-vBwZoY3FhIwIypMTLZdW4-R1DnXwmP6ujWV2hW5RXIhwATmcxfwztHxPAMszJ5N=w640-h400-e365-rj-sc0x00ffffff");
             background-attachment: fixed;
             background-size: cover
         }}
         </style>
         """,
         unsafe_allow_html=True
     )

add_bg_from_url()



data_url = ("https://github.com/jns1406/NYC_motor_collison_StreamlitWebApp/blob/main/NYC_Motor_Collision_2022.csv?raw=True")




st.title("Motor Vehicle Collisions in NewYork City")
st.markdown(" > This application is streamlit dashboard that can be used to "
"analyse motor 🚗 collisions 💥 in NYC 🗽")

@st.cache_data

def load_data():
    data = pd.read_csv(data_url, parse_dates = [['CRASH DATE', 'CRASH TIME']])
    data.columns = data.columns.str.replace(' ','_')
    data.dropna(subset = ["LATITUDE","LONGITUDE"], inplace = True)
    lowercase = lambda x: str(x).lower()
    data.rename(lowercase,axis = "columns",inplace = True)
    data.rename(columns = {"crash_date_crash_time":"date/time"}, inplace=True)
    return data

data= load_data()
duplicate_data = data


# Visualize--->pydeck

# Set up initial view of the map
ny_coord = (40.712776, -74.005974)
ny_map = folium.Map(location=ny_coord, zoom_start=11)

st.subheader("Where in NYC do injuries occur most frequently?")
injured_people = st.slider("Number of people hurt in vehicle accidents",0,int(data["number_of_persons_injured"].max()))

filtered_data = data.query("number_of_persons_injured >= @injured_people")[["latitude","longitude"]]
if not filtered_data.empty:
    injured_map = folium.Map(location=ny_coord, zoom_start=10)
    folium.plugins.HeatMap(filtered_data, radius=10).add_to(injured_map)
    folium_static(injured_map, width = 1200)


st.subheader("Where in NYC do deaths occur most frequently?")
died_people = st.slider("Number of people died in vehicle accidents",0,int(data["number_of_persons_killed"].max()))

filtered_data2 = data.query("number_of_persons_killed >= @died_people")[["latitude","longitude"]]
if not filtered_data2.empty:
    died_map = folium.Map(location=ny_coord, zoom_start=10)
    folium.plugins.HeatMap(filtered_data2, radius=10).add_to(died_map)
    folium_static(died_map, width = 1200)


st.subheader("How many accidents occuring during a given time in a day?")
time = st.slider("Hour to look at",0,23)
data = data[data["date/time"].dt.hour==time]

if not data.empty:
    # Create a Hexbin map
    accident_map = folium.Map(location=ny_coord, zoom_start=10)
    mc = folium.plugins.MarkerCluster(control=False)
    mc.add_child(folium.plugins.FastMarkerCluster(data[["latitude", "longitude"]].values))
    hexbin = folium.plugins.HeatMap(data[["latitude", "longitude"]], radius=25, min_opacity=0.5, max_val=10, show=True, overlay=True, control=False)
    hexbin.layer_name = 'Accident Density'
    hexbin.add_to(accident_map)
    mc.add_to(accident_map)
    folium.LayerControl().add_to(accident_map)
    folium_static(accident_map, width=1200)
else:
    st.warning("No results found for the specified time.")




st.markdown("Vehicle collisions between %i:00 to %i:00" % (time,(time+1) % 24))

st.pydeck_chart(pdk.Deck(
height = 1000,
width= 1000,
initial_view_state = {
                        "latitude" : ny_coord[0],
                        "longitude":ny_coord[1],
                        "zoom":9,
                        "pitch" :40.5,
                        "bearing":27.36


                    },
layers = [ pdk.Layer(
                    'HexagonLayer',
                    data = data[['date/time','latitude','longitude']],
                    get_position = ['longitude','latitude'],
                    radius=200,
                    coverage=1,
                    auto_highlight=True,
                    extruded=True,
                    elevation_scale=100,
                    elevation_range=[0, 1000],
                    pickable=True,
                    color_range=[
                    [255, 255, 178, 200], # yellow
                    [254, 204, 92, 200], # orange
                    [253, 141, 60, 200], # red-orange
                    [240, 59, 32, 200], # red
                    [189, 0, 38, 200], # dark red
                    [127, 0, 47, 200] # maroon
                ],

                color_domain=[0, 10, 20, 30, 60,90,150,300,600, 750]
                ,
                    ),
            ],
))


st.subheader("Breakdown by minute between %i:00 and %i:00" % (time,(time+1) %24))
filtered = data[
                (data["date/time"].dt.hour>=time) & (data["date/time"].dt.hour<(time+1))
]
hist = np.histogram(filtered["date/time"].dt.minute, bins=60, range=(0,60))[0]
chart_data = pd.DataFrame({"minute":range(60),"crashes":hist})

fig = go.Figure()
fig.add_trace(go.Scatter(x=chart_data["minute"], y=chart_data["crashes"],
                    mode='lines+markers',
                    name='Crashes'))
fig.update_layout(
    xaxis_title='Minute',
    yaxis_title='Crashes',
    width=1200,
    height=500,
    hovermode='x',
)
st.plotly_chart(fig)




st.header("Top 5 most dangerous streets in NewYork")
select = st.selectbox("Affected type of people",["Pedestrains","Cyclists","Motorists"])

if select == "Pedestrains":
    st.write(duplicate_data.query("number_of_pedestrians_injured>=1")[["on_street_name","number_of_pedestrians_injured"]].sort_values(by=["number_of_pedestrians_injured"],ascending=False).dropna(how="any")[:5])
elif select == "Cyclists":
    st.write(duplicate_data.query("number_of_cyclist_injured>=1")[["on_street_name","number_of_cyclist_injured"]].sort_values(by=["number_of_cyclist_injured"],ascending=False).dropna(how="any")[:5])
elif select =="Motorists":
    st.write(duplicate_data.query("number_of_motorist_injured>=1")[["on_street_name","number_of_motorist_injured"]].sort_values(by=["number_of_motorist_injured"],ascending=False).dropna(how="any")[:5])




if st.checkbox("Show Raw Data"):
    st.subheader("Raw Data")
    st.write(data)

# Add a note in the sidebar
st.sidebar.markdown("### Story:")
st.sidebar.markdown("This project is still in progress.")

# Add a disclaimer in the footer
st.write(" ")
st.write(" ")
st.write(" ")
st.write(" ")
st.write(" ")
st.write(" ")
st.write(" ")
st.write(" ")
st.write(" ")
st.write(" ")
st.markdown("***")
st.write(" ")
st.write(" ")
st.write(" ")
st.write(" ")
st.write(" ")
st.write(" ")

st.write(" ")
st.markdown("Created by Nithin Sai Jalukuru and Venkata Sai Phaneesha Chilaveni")
st.markdown("This project is still in progress......... ")
