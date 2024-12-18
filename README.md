# Weather Station IoT by Alessandro BARBIERI 

## Introduction

This weather application is a comprehensive weather monitoring and forecasting system designed to collect, process, and display real-time weather data. It keeps you informed about the current weather conditions both outside and inside your home, thanks to sensors connected to the M5Stack device.

This system helps optimize your home's comfort and save money. It monitors air quality and alerts you when it's poor, prompting you to open a window to improve ventilation. Additionally, by providing precise information on indoor temperature, it allows you to adjust the heating, thereby reducing energy consumption and saving on heating bills.

Even if you don't check the device before leaving, it will vocally announce the outside weather conditions using the integrated motion sensor, recommending a jacket or umbrella in case of rain or cloudy weather. This way, you are always prepared for the weather conditions when you leave home. Never be caught off guard with this weather station.

Moreover, you can remotely track the weather data of your home and have a historical record of indoor and outdoor weather data through a wonderful dashboard.

#### **Click here to discover the streamlit dashboard:**  https://weather-dashboard-24-tq2avlclea-oa.a.run.app/

#### **Here de link for the youtube video:** https://youtu.be/oNOjebcqC2g

## How the Application Works

### Overview

- **M5Stack Device:** This device displays real-time weather data for both indoor and outdoor environments. It collects data via temperature, humidity, and CO2 sensors and sends it to the backend server.
- **Displayed Weather Data:** The M5Stack device shows indoor data such as temperature, humidity, and air quality (CO2), as well as outdoor weather conditions (temperature, weather conditions, wind speed, etc.) obtained via the OpenWeatherMap API.
- **Weather Forecasts:** The application also provides weather forecasts for the coming days, obtained via the OpenWeatherMap API.
- **Streamlit Dashboard:** The dashboard allows remote tracking of current and historical weather information. It displays graphs and visualizations of data collected by the M5Stack and stored in Google Cloud BigQuery. The dashboard is particularly useful for in-depth analysis and visualization of historical trends.

### Typical Use

The application is mainly intended for indoor use. The M5Stack collects and displays weather data for home or office use. Outdoor data is obtained via an IP address defined in the backend. The dashboard allows remote tracking and analysis of weather data, providing a clear view of current conditions and historical trends.

## Technical Details

### Backend

The backend is a Flask application that provides several endpoints to manage the retrieval, storage, and processing of weather data. It uses Google Cloud services for data storage and processing.

#### Key Features

- **Weather Data Retrieval:** Retrieves current weather data and forecasts via the OpenWeatherMap API.
- **Geolocation:** Determines location based on IP address using the IPInfo API.
- **Time Synchronization:** Retrieves and adjusts the current time via an NTP server.
- **Data Storage:** Stores weather data in Google Cloud BigQuery.
- **Audio Generation:** Uses Google Cloud Text-to-Speech and Vertex AI to generate audio responses about weather conditions.
- **Image and Audio File Management:** Manages the upload and download of images and audio files to/from Google Cloud Storage.

#### Main Endpoints

- `/get_time`: Retrieves the current time from an NTP server.
- `/weather_geoloc`: Retrieves weather data based on the client's geolocation.
- `/weather`: Retrieves weather data for a specified city.
- `/forecast`: Retrieves weather forecasts.
- `/upload`: Uploads sensor data from the M5Stack device to BigQuery.
- `/latest_data`: Retrieves the latest weather data from BigQuery.
- `/download_image`: Downloads an image from Google Cloud Storage.
- `/download_audio`: Downloads an audio file from Google Cloud Storage.

### Frontend (M5Stack)

The frontend is implemented on an M5Stack device using MicroPython. It connects to the backend server to fetch weather data and displays it on the device's screen. It also uploads sensor data (temperature, humidity, CO2) to the backend.

#### Key Features

- **WiFi Connectivity:** Connects to predefined WiFi networks.
- **Sensor Integration:** Reads data from temperature, humidity, and CO2 sensors.
- **LED Indicators:** Uses LEDs to indicate air quality based on CO2 levels.
- **Weather Data Display:** Retrieves and displays current weather data and forecasts.
- **Audio Playback:** Downloads and plays weather-related audio messages.

### Dashboard (Streamlit)

The dashboard is a Streamlit application that displays weather data and forecasts in a user-friendly manner. It also provides visualizations of historical data stored in BigQuery through various charts.

#### Key Features

- **Current Weather Data Display:** Shows current weather information for the user's location or a specified city.
- **City Weather Search:** Search for current weather and upcoming forecasts for a destination city.
- **Forecast Display:** Shows weather forecasts for the upcoming days.
- **Data Visualizations:** Displays various graphs and visualizations of weather data stored in BigQuery.

#### Visualizations

- **Temperature Heatmap:** Displays indoor temperature data as a heatmap.
- **Humidity chandelier:** Displays humidity data over time as a violin plot.
- **CO2 area plot:** Displays CO2 levels as a area.
- **External weather area plot:** Display outside temperature, wind speed  and humidity for the past days

## Installation and Configuration

### Prerequisites

- Python 3.7 or higher
- Google Cloud SDK
- M5Stack Device
- M5 stack sensors (Env III Sensor, Motion sensor, TVOC/eCO2)
- OpenWeatherMap API Key
- Ipinfo for the geolocation service
- Google Cloud Project with BigQuery, Buckets etc



### How to use this project ? 

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd <repository-directory>
2. **Change the configuration setup**
   1. SSID and password list in the M5 stack
   2. Change your IP address in the backend in aim to get the actual weahter from your **home location**
   3. Change the api key for openweathermap api
   4. Add some other api if you want
## Demo  
![Weather Dashboard](Icon/Animation.gif)
