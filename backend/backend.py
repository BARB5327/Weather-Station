# Configurez les identifiants et le client BigQuery
from flask import Flask, request, jsonify,send_file
from google.cloud import bigquery, texttospeech, storage
from vertexai.preview.language_models import TextGenerationModel
import vertexai
import base64
import requests
import ntplib
from datetime import *
from collections import defaultdict
from werkzeug.middleware.proxy_fix import ProxyFix
import os


# Retrieve the credentials from .env file
weather_api = os.getenv("weather_api_key")
ip_api = os.getenv("ip_api_key")
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

# Configure identifiers and the BigQuery Client
client = bigquery.Client(project="cloud-advanced-analytics-1")
weather_api_key = weather_api
openweathermap_url = "https://api.openweathermap.org/data/2.5/weather"
ip_api_key=ip_api
storage_client=storage.Client()

#Get NTP date and time
@app.route('/get_time')
def fetch_ntp_time(server="pool.ntp.org"):
    client = ntplib.NTPClient()
    try:
        response = client.request(server, version=3)
        utc_time = datetime.utcfromtimestamp(response.tx_time)
        adjusted_time = utc_time + timedelta(hours=2)
        test_time = adjusted_time.strftime('%Y-%m-%d %H:%M:%S')
        formatted_time = adjusted_time.strftime("%A, %d of %B at %H:%M")
        print("Adjusted time:", formatted_time)
        return jsonify({'time': formatted_time, 'test_time': test_time})
    except Exception as e:
        print("Failed to fetch NTP time:", e)
        return jsonify({'error': "Failed to fetch NTP time", 'details': str(e)})

#api for the geolocation if the geocoder doesn't work (too muche attempt with geocoder)
def get_location(ip_address,api_key):
    url = f'https://ipinfo.io/{ip_address}?token={api_key}'
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    print(f"Geolocation data: {data}")

    location = data['loc'].split(',')
    latitude = location[0]
    longitude = location[1]

    return latitude, longitude

@app.route('/weather_geoloc', methods=['GET'])
def get_weather_geoloc():
    try:
        # Obtenir les coordonnées de la requête
        if request.headers.getlist("X-Forwarded-For"):
            ip_address = request.headers.getlist("X-Forwarded-For")[0]
        else:
            ip_address = request.remote_addr
        print(f"Client IP: {ip_address}")
        #change here the ip address of your home
        lat, lng = get_location('188.60.236.126', ip_api_key)
        weather_url = f'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lng}&appid={weather_api_key}&units=metric'
        weather_response = requests.get(weather_url)
        weather_response.raise_for_status()
        weather = weather_response.json()
        print(f"Weather data: {weather}")  # Debugging line

        weather_details = {
            'city_name': weather['name'],
            'temperature': weather['main']['temp'],
            'max_temp': weather['main']['temp_max'],
            'min_temp': weather['main']['temp_min'],
            'weather_condition': weather['weather'][0]['main'],
            'description': weather['weather'][0]['description'],
            'humidity': weather['main']['humidity'],
            'wind_speed': weather['wind']['speed'],
            'icon': weather['weather'][0]['icon'],
            'lat': weather['coord']['lat']
        }

        questions = [
            "I want a What is the temperature outside the description and give a short recommendation? Don't say the city, just say outside. If it's rainy, tell me to take an umbrella. and don't say too much about the weather, just want to know the temperature and the description. NO more than 20 words",
        ]
        responses = generate_responses_internal(weather_details, questions)
        for idx, (question, response_text) in enumerate(responses.items()):
            audio_filename = f'audio_{idx}.wav'
            synthesize_text_to_storage(response_text, audio_filename)

        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sql_query = f"""
                INSERT INTO `cloud-advanced-analytics-1.project.outdoor_weather` (temperature, humidity, wind, timestamp)
                VALUES ({weather_details['temperature']},{weather_details['humidity']},{weather_details['wind_speed']},'{current_time}')"""

        job = client.query(sql_query)
        job.result()

        return jsonify({
            'weather': weather_details,
            'responses': responses,
        })
    except requests.RequestException as e:
        print(f"Error making API request: {e}")  # Debugging line
        return jsonify({'error': 'Failed to retrieve weather data', 'details': str(e)}), 500
    except Exception as e:
        print(f"Unhandled exception: {e}")  # Debugging line
        return jsonify({'error': 'Internal Server Error', 'details': str(e)}), 500



#Get all data with weather map api (forecast, weather geoloc, weather by typing a city)

@app.route('/weather', methods=['GET'])
def get_weather_details():
    try:
        city_name = request.args.get('city_name')

        weather_url = f'https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={weather_api_key}&units=metric'
        weather_response = requests.get(weather_url)
        weather_response.raise_for_status()
        weather = weather_response.json()

        weather_details = {
            'city_name': city_name,
            'temperature': weather['main']['temp'],
            'min_temp': weather['main']['temp_min'],
            'max_temp':weather['main']['temp_max'],
            'weather_condition': weather['weather'][0]['main'],
            'description': weather['weather'][0]['description'],
            'humidity': weather['main']['humidity'],
            'wind_speed': weather['wind']['speed'],
            'icon':weather['weather'][0]['icon']
        }

        return jsonify(weather_details)
    except requests.RequestException as e:
        print(f"Error making API request: {e}")
        return jsonify({'error': 'Failed to retrieve weather data'}), 500
    except Exception as e:
        print(f"Unhandled exception: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500

def get_city_name():
    lat, lng = get_location('188.60.236.126', ip_api_key)
    url = f'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lng}&appid={weather_api_key}&units=metric'
    response=requests.get(url)
    city_json=response.json()
    city_name=city_json['name']
    return city_name


@app.route('/forecast', methods=['GET'])
def get_forecast():
    try:
        city_name = request.args.get('city_name')
        if not city_name:
            city_name = get_city_name()

        forecast_url = f'https://api.openweathermap.org/data/2.5/forecast?q={city_name}&appid={weather_api_key}&units=metric'
        forecast_response = requests.get(forecast_url)
        forecast_response.raise_for_status()
        forecast_data = forecast_response.json()

        daily_data = defaultdict(list)
        today_date = datetime.now().date()

        for item in forecast_data['list']:
            date = datetime.fromtimestamp(item['dt']).date()
            if date > today_date:
                daily_data[date].append({
                    'temperature': item['main']['temp'],
                    'min_temperature': item['main']['temp_min'],
                    'max_temperature': item['main']['temp_max'],
                    'humidity': item['main']['humidity'],
                    'description': item['weather'][0]['description'],
                    'icon': item['weather'][0]['icon'],
                    'wind': item['wind']['speed']
                })

        forecasts = []
        for date, data in sorted(daily_data.items()):
            min_temp = min(data, key=lambda x: x['min_temperature'])
            max_temp = max(data, key=lambda x: x['max_temperature'])
            forecasts.append({
                'date': date.strftime('%d-%m'),
                'min_temperature': min_temp['min_temperature'],
                'max_temperature': max_temp['max_temperature'],
                'min_humidity': min_temp['humidity'],
                'max_humidity': max_temp['humidity'],
                'description': max_temp['description'],
                'icon': max_temp['icon'],
                'min_wind_speed': min_temp['wind'],
                'max_wind_speed': max_temp['wind']
            })

        response = {
            'city_name': forecast_data['city']['name'],
            'forecasts': forecasts
        }

        return jsonify(response)
    except requests.RequestException as e:
        print(f"Error making API request: {e}")
        return jsonify({'error': 'Failed to retrieve weather data', 'details': str(e)}), 500
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500

        #Upload the date from the m5stack sensors in aim to insert them in the bigquery tables
@app.route('/upload', methods=['POST'])
def upload_data():
    data = request.get_json()
    print("Data received:", data)
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    sql_query = f"""
        INSERT INTO `cloud-advanced-analytics-1.project.internal-weather` (temperature, humidity, timestamp)
        VALUES ({data['temperature']}, {data['humidity']}, '{data['time']}')
    """
    sql_query_co2 = f"""
        INSERT INTO `cloud-advanced-analytics-1.project.co2` (co2, timestamp)
        VALUES ({int(data['co2'])}, '{data['time']}')
    """

    job = client.query(sql_query)
    job_co2=client.query(sql_query_co2)
    job.result()
    job_co2.result()

    return jsonify({"success": True})

#Get the last temperature, co2 and humidity data to from bigquery to display in the dashboard
def get_temperature_data():
    query = """SELECT * FROM `cloud-advanced-analytics-1.project.internal-weather` ORDER BY timestamp DESC LIMIT 1"""
    result = client.query(query).result()
    for row in result:
        return {field.name: row[field.name] for field in result.schema}

    return {}

def get_humidity_data():
    query = """SELECT * FROM `cloud-advanced-analytics-1.project.internal-weather` ORDER BY timestamp DESC LIMIT 1"""
    result = client.query(query).result()
    for row in result:
        # Convertissez la ligne en dictionnaire (chaque champ à sa valeur)
        return {field.name: row[field.name] for field in result.schema}

    return {}  # Retourne un dictionnaire vide si aucun résultat n'est trouvédef get_temperature_data():
def get_co2_data():
    query = """SELECT * FROM `cloud-advanced-analytics-1.project.co2` ORDER BY timestamp DESC LIMIT 1"""
    result = client.query(query).result()
    for row in result:
        # Convertissez la ligne en dictionnaire (chaque champ à sa valeur)
        return {field.name: row[field.name] for field in result.schema}

    return {}  # Retourne un dictionnaire vide si aucun résultat n'est trouvédef get_temperature_data():

@app.route('/latest_data', methods=['GET'])
def get_latest_data():
    temperature_data = get_temperature_data()
    humidity_data = get_humidity_data()
    co2_data=get_co2_data()
    combined_data = {**temperature_data, **humidity_data,**co2_data}
    return jsonify(combined_data)

#Download the icon from a bucket google cloud in aim to use it for the m5stack and dashboard
@app.route('/download_image', methods=['GET'])
def download_image():
    image_name = request.args.get('image_name')
    if not image_name:
        print('Le nom de l\'image est requis.')
        return jsonify({'error': 'Le nom de l\'image est requis.'}), 400

    bucket_name = 'icon_m5stack'

    try:
        print('Attempting to download the image:', image_name)

        # Télécharger l'image depuis Google Cloud Storage
        bucket = storage_client.get_bucket(bucket_name)
        blob = bucket.blob(image_name)
        image_data = blob.download_as_string()

        print('Image successfully downloaded.')

        image_data_base64 = base64.b64encode(image_data).decode('utf-8')
        return jsonify({'image_data': image_data_base64}), 200
    except Exception as e:
        print('Error downloading image :', str(e))
        return jsonify({'error': str(e)}), 500
#Function to create an audio with text2speech who is saved on a bucket. The text is created with vertexAI
def synthesize_text_to_storage(text, file_path):
    try:
        audio_content = synthesize_text(text)
        if audio_content is None:
            print(f"Failed to synthesize text: {text}")
            return None

        bucket_name = 'icon_m5stack'
        bucket = storage_client.get_bucket(bucket_name)
        blob = bucket.blob(file_path)

        blob.upload_from_string(audio_content, content_type='audio/wav')
        return f"https://storage.googleapis.com/{bucket_name}/{file_path}"
    except Exception as e:
        print(f"Failed to upload audio file to storage: {e}")
        return None

def synthesize_text(text):
    try:
        client = texttospeech.TextToSpeechClient()
        input_text = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Wavenet-D",  # Utilisez une voix anglaise
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL,
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16,
            sample_rate_hertz=20000,
            speaking_rate = 1.0,
            pitch = 0.0,
        )
        response = client.synthesize_speech(
            request={"input": input_text, "voice": voice, "audio_config": audio_config}
        )

        return response.audio_content
    except Exception as e:
        print(f"Error in text-to-speech synthesis: {e}")
        return None

@app.route('/download_audio', methods=['GET'])
def download_audio():
    audio_name = request.args.get('audio_name')
    bucket_name = 'icon_m5stack'
    try:
        if not audio_name:
            return jsonify({'error': 'Le nom de l\'audio est requis.'}), 400

        bucket = storage_client.get_bucket(bucket_name)
        blob = bucket.blob(audio_name)

        if not blob.exists():
            return jsonify({'error': 'Fichier audio non trouvé.'}), 404

        audio_data = blob.download_as_string()
        audio_data_base64 = base64.b64encode(audio_data).decode('utf-8')
        return jsonify({'audio_data': audio_data_base64}), 200
    except Exception as e:
        print('Erreur lors du téléchargement de l\'audio :', str(e))
        return jsonify({'error': str(e)}), 500

#Download icons for the dashboard
@app.route('/download_image_dashboard', methods=['GET'])
def download_image_dashboard():
    image_name = request.args.get('image_name')
    if not image_name:
        return jsonify({'error': 'Image name is required.'}), 400

    bucket_name = 'icon_dashboard'

    try:
        bucket = storage_client.get_bucket(bucket_name)
        blob = bucket.blob(image_name)
        image_data = blob.download_as_bytes()

        image_data_base64 = base64.b64encode(image_data).decode('utf-8')
        return jsonify({'image_data': image_data_base64}), 200
    except Exception as e:
        return jsonify({'error': 'Failed to download image', 'details': str(e)}), 500

#Generate responses for the audio with vertexAI
def generate_responses_internal(weather_details, questions):
    try:
        # Formater les données météorologiques en un prompt de base
        base_prompt = (
            f"La météo actuelle pour {weather_details['city_name']} est la suivante : "
            f"température de {weather_details['temperature']}°C, "
            f"température maximale de {weather_details['max_temp']}°C, "
            f"température minimale de {weather_details['min_temp']}°C, "
            f"condition météorologique : {weather_details['description']}, "
            f"humidité : {weather_details['humidity']}%, "
            f"vitesse du vent : {weather_details['wind_speed']} km/h. "
        )

        PROJECT_ID = "cloud-advanced-analytics-1"
        REGION = "us-central1"
        vertexai.init(project=PROJECT_ID, location=REGION)

        model = TextGenerationModel.from_pretrained("text-bison@002")

        responses = {}

        for question in questions:
            prompt = base_prompt + question
            response = model.predict(prompt)
            responses[question] = response.text.strip()

        return responses
    except Exception as e:
        print(f"Error in generating responses: {e}")
        return {}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
