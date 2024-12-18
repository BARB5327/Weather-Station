import streamlit as st
import requests
from datetime import *
from PIL import Image
from io import BytesIO
import base64
import pandas as pd
import pandas_gbq
import plotly.express as px
import plotly.graph_objects as go


API_BASE_URL = "https://backend-609365116577.europe-west6.run.app"



st.set_page_config(layout="wide")

col1, col2, col3 = st.columns([5, 10, 1])
with col2:
    st.title("Weather Dashboard")
st.markdown('<hr style="border:2px; margin-bottom:40;"/>', unsafe_allow_html=True)

# Initialize different pages
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'weather_info'

if 'current_weather_data' not in st.session_state:
    st.session_state.current_weather_data = None

# Initialize state for forecast plot
if 'forecast_data' not in st.session_state:
    st.session_state.forecast_data = None

if 'current_metric' not in st.session_state:
    st.session_state.current_metric = 'Température maximale'


# Page changment
def change_page(page_name):
    st.session_state.current_page = page_name

# Changment of the type of chart (temperature, humidity, wind)
def change_metric(metric_name):
    st.session_state.current_metric = metric_name

# Boutons pour changer de page
st.sidebar.title("Navigation")
st.sidebar.button("Weather Info", on_click=change_page, args=('weather_info',))
st.sidebar.button("BigQuery Data", on_click=change_page, args=('big_query_data',))

def unify_weather_data(weather_data):
    if 'weather' in weather_data:
        return weather_data['weather']
    return weather_data

def get_weather_by_backend():
    try:
        response = requests.get(f"{API_BASE_URL}/weather_geoloc")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Failed to get weather data: {e}")
        return None

#Get icon from bucket
def get_image_from_backend(image_name):
    response = requests.get(f"{API_BASE_URL}/download_image_dashboard", params={"image_name": image_name})
    if response.status_code == 200:
        image_data = response.json().get('image_data', '')
        image_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_bytes))
        return image
    else:
        st.error(f"Failed to fetch image from backend. Status code: {response.status_code}")
        return None


#Get the last date in the bigquery tables
def fetch_latest_data():
    response = requests.get(f"{API_BASE_URL}/latest_data")
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Failed to fetch latest data from backend.")
        return {}

#Fonction to display the weather and the forecast
def display_weather():
    current_weather_data = unify_weather_data(st.session_state.current_weather_data)
    forecast_data = st.session_state.forecast_data

    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader(f"Current weather in {current_weather_data.get('city_name', 'N/A')}")
        icon_code = current_weather_data.get('icon', '')
        icon_url = f"http://openweathermap.org/img/wn/{icon_code}@4x.png"
        st.image(icon_url, width=100)
        date = datetime.now().strftime("%Y-%m-%d %H:%M")
        st.write(f"**Date :** {date}")
        st.write(f"**Current weather :** {current_weather_data.get('temperature', 'N/A')}°C")
        st.write(f"**Minimum temperature :** {current_weather_data.get('min_temp', 'N/A')}")
        st.write(f"**Maximum temperature :** {current_weather_data.get('max_temp', 'N/A')}")
        st.write(f"**Description :** {current_weather_data.get('description', 'N/A')}")
        st.write(f"**Humidity :** {current_weather_data.get('humidity', 'N/A')}%")
        st.write(f"**Wind speed :** {current_weather_data.get('wind_speed', 'N/A')} km/h")

    with col2:
        st.subheader("Forecast weather")
        forecast_days = forecast_data.get('forecasts', [])[:10]
        cols = st.columns(len(forecast_days))
        for idx, forecast in enumerate(forecast_days):
            f_icon_url = f"http://openweathermap.org/img/wn/{forecast['icon']}@4x.png"
            with cols[idx]:
                st.image(f_icon_url, width=100)
                st.write(f"**Date :** {forecast['date']}")
                st.write(f"**Temp. Max :** {forecast['max_temperature']}°C")
                st.write(f"**Temp. Min :** {forecast['min_temperature']}°C")
                st.write(f"**Description :** {forecast['description']}")
                st.write(f"**Min. wind speed :** {forecast['min_wind_speed']} km/h")
                st.write(f"**Max wind speed :** {forecast['max_wind_speed']} km/h")

#Fonctions to get the different chart for the forecasts
def plot_metric(forecast_data, metric, title, y_label, color):
    df = pd.DataFrame({
        'date': [pd.to_datetime(forecast['date'], format='%d-%m') for forecast in forecast_data[:5] if 'date' in forecast],
        metric: [forecast.get(metric, None) for forecast in forecast_data[:5]]
    })

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df[metric],
        mode='lines+markers',
        fill='tozeroy',
        name=title,
        line=dict(color=color, width=2),
        marker=dict(size=8, color=color, opacity=0.7)
    ))

    x_range = [df['date'].min()-pd.Timedelta(days=0.1), df['date'].max() + pd.Timedelta(days=0.1)]

    fig.update_layout(
        title={'text': title, 'font': {'size': 20}},  # Augmenter la taille du titre
        xaxis_title='Date',
        yaxis_title=y_label,
        template='plotly_white',
        xaxis=dict(showgrid=True, tickvals=df['date'], ticktext=df['date'].dt.strftime('%d-%m'), fixedrange=True, range=x_range),
        yaxis=dict(showgrid=True, fixedrange=True),
        plot_bgcolor='white',
        xaxis_gridcolor='lightgrey',
        yaxis_gridcolor='lightgrey',
        width=1000
    )

    st.plotly_chart(fig, use_container_width=True)

def plot_temperature(forecast_data):
    plot_metric(forecast_data, 'max_temperature', 'Forecast of the temperature', 'Temperature (°C)', 'firebrick')

def plot_wind_speed(forecast_data):
    plot_metric(forecast_data, 'max_wind_speed', 'Forecast of the wind speed', 'Wind speed (km/h)', 'royalblue')

def plot_humidity(forecast_data):
    plot_metric(forecast_data, 'max_humidity', 'Forecast of the humidity rate', 'Humidity rate (%)', 'green')


def fetch_bigquery_data(query):
    df = pandas_gbq.read_gbq(query, project_id='cloud-advanced-analytics-1')
    return df

#Temperature heatmap
def temperature_heatmap(df):
    df = df.sort_values(by='timestamp')
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    df['date'] = df['timestamp'].dt.date
    df['hour'] = df['timestamp'].dt.hour

    fig = px.density_heatmap(
        df,
        x='date',
        y='hour',
        z='temperature',
        histfunc='avg',
        text_auto='.2f',
        color_continuous_scale='YlOrRd',
        labels={'date': 'Date', 'hour': 'Hour of Day', 'temperature': 'Temperature (°C)'},
    )

    fig.update_layout(
        xaxis_title='Date',
        yaxis_title='Hour of Day',
        coloraxis_colorbar=dict(title='Temperature (°C)'),
        xaxis=dict(tickmode='array', tickvals=df['date'].unique(), tickangle=45, tickfont=dict(size=10)),
        yaxis=dict(tickmode='array', tickvals=df['hour'].unique(), tickfont=dict(size=10)),
        font=dict(size=12),
        width=600,
        height=600,
        margin=dict(l=0, r=0, t=40, b=0)
    )

    st.plotly_chart(fig, use_container_width=True)


def humidity_plot(df):
    df = df.sort_values(by='timestamp')
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['date'] = df['timestamp'].dt.date

    daily_summary = df.groupby('date').agg({
        'humidity': ['min', 'max', 'median', lambda x: x.quantile(0.25), lambda x: x.quantile(0.75)]
    }).reset_index()

    daily_summary.columns = ['date', 'min_humidity', 'max_humidity', 'median_humidity', 'q1_humidity', 'q3_humidity']

    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=daily_summary['date'],
        open=daily_summary['q1_humidity'],
        high=daily_summary['max_humidity'],
        low=daily_summary['min_humidity'],
        close=daily_summary['q3_humidity'],
        increasing_line_color='red',
        decreasing_line_color='blue',
        increasing_fillcolor='red',
        decreasing_fillcolor='blue',
        line=dict(width=1.5),
        whiskerwidth=0.8,
        opacity=0.8,
        name='Humidity'
    ))

    fig.add_trace(go.Scatter(
        x=daily_summary['date'],
        y=daily_summary['median_humidity'],
        mode='lines+markers',
        line=dict(color='black', width=2, dash='dash'),
        marker=dict(symbol='circle', size=8, color='black'),
        name='Median Humidity'
    ))

    fig.update_layout(
        yaxis_title='Humidity (%)',
        xaxis_title='Date',
        xaxis_rangeslider_visible=False,
        width=800,
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)
#
def Co2_plot(df):
    df = df.sort_values(by='timestamp')
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['date'] = df['timestamp'].dt.date

    daily_avg = df.groupby('date')['co2'].mean().reset_index()

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=daily_avg['date'],
        y=daily_avg['co2'],
        mode='lines+markers+text',
        fill='tozeroy',
        text=daily_avg['co2'].round(2),
        textposition='top center',
        line=dict(color='royalblue', width=2),
        marker=dict(size=8, color=daily_avg['co2'], colorscale='Viridis', showscale=True)
    ))

    fig.update_yaxes(range=[0, 1000], fixedrange=True)
    fig.update_xaxes(fixedrange=True)

    fig.add_shape(
        type="line",
        x0=daily_avg['date'].min(),
        y0=800,
        x1=daily_avg['date'].max(),
        y1=800,
        line=dict(
            color="Red",
            width=2,
            dash="dashdot",
        ),
    )

    fig.add_annotation(
        x=daily_avg['date'].max(),
        y=800,
        text="Critical Level",
        showarrow=False,
        yshift=10,
        font=dict(
            size=12,
            color="Red"
        )
    )

    fig.update_layout(
        xaxis_title='Date',
        yaxis_title='Average CO2 (PPM)',
        showlegend=False,
        xaxis=dict(tickfont=dict(size=14)),
        yaxis=dict(tickfont=dict(size=14)),
        plot_bgcolor='white',
        xaxis_gridcolor='lightgrey',
        yaxis_gridcolor='lightgrey',
    )

    st.plotly_chart(fig, use_container_width=True)

#3 charts for the outdoor data
def plot_weather_charts(df):
    df = df.sort_values(by='timestamp')
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['date'] = df['timestamp'].dt.date

    daily_avg = df.groupby('date').agg({
        'temperature': 'mean',
        'wind': 'mean',
        'humidity': 'mean'
    }).reset_index()

    fig_temp = go.Figure()
    fig_temp.add_trace(go.Scatter(
        x=daily_avg['date'],
        y=daily_avg['temperature'],
        mode='lines+markers',
        fill='tozeroy',
        name='Temperature',
        line=dict(color='firebrick', width=2),
        marker=dict(size=4, color='firebrick', opacity=0.7)
    ))
    fig_temp.update_layout(
        title='Daily Average Temperature',
        xaxis_title='Date',
        yaxis_title='Temperature (°C)',
        template='plotly_white',
        yaxis=dict(showgrid=True, range=[daily_avg['temperature'].min()-2, daily_avg['temperature'].max()+2])
    )

    fig_wind = go.Figure()
    fig_wind.add_trace(go.Scatter(
        x=daily_avg['date'],
        y=daily_avg['wind'],
        mode='lines+markers',
        fill='tozeroy',
        name='Wind Speed',
        line=dict(color='royalblue', width=2),
        marker=dict(size=4, color='royalblue', opacity=0.7)
    ))
    fig_wind.update_layout(
        title='Daily Average Wind Speed',
        xaxis_title='Date',
        yaxis_title='Wind Speed (km/h)',
        template='plotly_white',
        xaxis=dict(showgrid=True),
        yaxis=dict(showgrid=True, range=[0, daily_avg['wind'].max()+5])
    )

    fig_humidity = go.Figure()
    fig_humidity.add_trace(go.Scatter(
        x=daily_avg['date'],
        y=daily_avg['humidity'],
        mode='lines+markers',
        fill='tozeroy',
        name='Humidity',
        line=dict(color='green', width=2),
        marker=dict(size=4, color='green', opacity=0.7)
    ))
    fig_humidity.update_layout(
        title='Daily Average Humidity',
        xaxis_title='Date',
        yaxis_title='Humidity (%)',
        template='plotly_white',
        xaxis=dict(showgrid=True),
        yaxis=dict(showgrid=True, range=[0, 100])
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.plotly_chart(fig_temp, use_container_width=True)
    with col2:
        st.plotly_chart(fig_wind, use_container_width=True)
    with col3:
        st.plotly_chart(fig_humidity, use_container_width=True)


# Implémentation user interface of the streamlit
house = get_image_from_backend("dashboard_house.png")
humidity_img = get_image_from_backend("dashboard_humidty.png")
co2 = get_image_from_backend("dashboard_co2.png")
data = fetch_latest_data()

st.markdown("""
<style>
.column-container {
    display: flex;
    flex-direction: column;
    justify-content: flex-start; 
    align-items: center; 
    height: auto; 
}
.column-image {
    height: auto; 
    width: auto; 
}
.column-text {
    height: 30%; 
    display: flex;
    align-items: center; 
    justify-content: center; 
    width: 100%; 
}
.big-font {
    font-size: 40px; 
    font-weight: bold;
    text-align: left;
}
</style>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown('<div class="column-container">', unsafe_allow_html=True)
    st.image(house, width=200)
    st.markdown('<div class="column-text">', unsafe_allow_html=True)
    st.markdown(f'<p class="big-font">Temperature: {data.get("temperature", "N/A")}°C</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="column-container">', unsafe_allow_html=True)
    st.image(humidity_img, width=200)
    st.markdown('<div class="column-text">', unsafe_allow_html=True)
    st.markdown(f'<p class="big-font">Humidity: {data.get("humidity", "N/A")}%</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="column-container">', unsafe_allow_html=True)
    st.image(co2, width=200)
    st.markdown('<div class="column-text">', unsafe_allow_html=True)
    st.markdown(f'<p class="big-font">CO2: {data.get("co2", "N/A")} PPM</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.current_page == 'weather_info':
    city_name = st.text_input("Enter a city name")
    if st.button("Get Weather for Entered City"):
        if city_name:
            current_weather_response = requests.get(f"{API_BASE_URL}/weather", params={"city_name": city_name})
            if current_weather_response.ok:
                st.session_state.current_weather_data = unify_weather_data(current_weather_response.json())
                forecast_response = requests.get(f"{API_BASE_URL}/forecast", params={"city_name": city_name})
                if forecast_response.ok:
                    st.session_state.forecast_data = forecast_response.json()
                else:
                    st.error("Failed to fetch forecast data.")
            else:
                st.error("Failed to fetch current weather data.")
        else:
            st.error("Please enter a city name.")

    # Button to use geolocation
    if st.button("📍 Use your Location"):
        current_weather_response = requests.get(f"{API_BASE_URL}/weather_geoloc")
        if current_weather_response.ok:
            st.session_state.current_weather_data = unify_weather_data(current_weather_response.json())
            forecast_response = requests.get(f"{API_BASE_URL}/forecast")
            if forecast_response.ok:
                st.session_state.forecast_data = forecast_response.json()
            else:
                st.error("Failed to fetch forecast data.")
        else:
            st.error("Failed to fetch current weather data.")

    if st.session_state.current_weather_data and st.session_state.forecast_data:
        display_weather()
        st.title("Forecast visualisation")
        metric = st.selectbox(
            'Select metric to display:',
            ('Temperature', 'Wind speed', 'Humidity rate'),
            key='metric_selector'
        )

        if metric == 'Temperature':
            plot_temperature(st.session_state.forecast_data['forecasts'])
        elif metric == 'Wind speed':
            plot_wind_speed(st.session_state.forecast_data['forecasts'])
        elif metric == 'Humidity rate':
            plot_humidity(st.session_state.forecast_data['forecasts'])

if st.session_state.current_page == 'big_query_data':
    st.title("BigQuery Weather Data")

    query_weather = """
        SELECT temperature, humidity, timestamp 
        FROM `cloud-advanced-analytics-1.project.internal-weather`
        ORDER BY timestamp DESC
        LIMIT 1000
    """
    query_co2 = """
        SELECT co2, timestamp 
        FROM `cloud-advanced-analytics-1.project.co2`
        ORDER BY timestamp DESC
        LIMIT 1000
    """

    df_weather = fetch_bigquery_data(query_weather)
    df_co2 = fetch_bigquery_data(query_co2)

    if not df_weather.empty:
        st.write("### Heatmap of Indoor Temperature over time")
        temperature_heatmap(df_weather)

        st.write("### Humidity Levels Over Time")
        humidity_plot(df_weather)
    else:
        st.write("No weather data available.")

    if not df_co2.empty:
        st.write("### CO2 Levels Over Time")
        Co2_plot(df_co2)
    else:
        st.write("No CO2 data available.")

    query_external_weather = """
        SELECT timestamp, temperature, humidity, wind 
        FROM `cloud-advanced-analytics-1.project.outdoor_weather`
        ORDER BY timestamp DESC
        LIMIT 1000
    """

    df_external_weather = fetch_bigquery_data(query_external_weather)

    if not df_external_weather.empty:
        st.write("### External Weather Data")
        plot_weather_charts(df_external_weather)
    else:
        st.write("No external weather data available.")