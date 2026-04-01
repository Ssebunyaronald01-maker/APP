from flask import Flask, render_template, request, jsonify
import requests
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Get API key from environment variable
API_KEY = os.getenv('OPENWEATHER_API_KEY', 'YOUR_API_KEY_HERE')

class WeatherSystem:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "http://api.openweathermap.org/data/2.5"
        
    def get_coordinates(self, location):
        """Convert location name to coordinates"""
        geocoding_url = "http://api.openweathermap.org/geo/1.0/direct"
        params = {
            'q': location,
            'limit': 1,
            'appid': self.api_key
        }
        
        try:
            response = requests.get(geocoding_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data:
                return (data[0]['lat'], data[0]['lon'])
            return None
        except Exception as e:
            print(f"Geocoding error: {e}")
            return None
    
    def get_weather_for_datetime(self, location, target_date, target_time):
        """Get weather for specific date and time"""
        try:
            # Get coordinates
            coords = self.get_coordinates(location)
            if not coords:
                return {'error': f"Location '{location}' not found"}
            
            # Parse target datetime
            target_datetime = datetime.strptime(f"{target_date} {target_time}", "%Y-%m-%d %H:%M")
            current_time = datetime.now()
            
            # Check if date is within range (today + 5 days)
            if target_datetime > current_time + timedelta(days=5):
                return {'error': 'Cannot forecast beyond 5 days'}
            
            # Get forecast data
            forecast_url = f"{self.base_url}/forecast"
            params = {
                'lat': coords[0],
                'lon': coords[1],
                'appid': self.api_key,
                'units': 'metric',
                'cnt': 40  # 5 days * 8 forecasts
            }
            
            response = requests.get(forecast_url, params=params, timeout=10)
            response.raise_for_status()
            forecast_data = response.json()
            
            # Find closest forecast to target time
            closest_forecast = None
            min_time_diff = float('inf')
            
            for forecast in forecast_data['list']:
                forecast_time = datetime.fromtimestamp(forecast['dt'])
                time_diff = abs((forecast_time - target_datetime).total_seconds())
                
                if time_diff < min_time_diff:
                    min_time_diff = time_diff
                    closest_forecast = forecast
            
            if closest_forecast and min_time_diff < 10800:  # Within 3 hours
                return self._format_forecast(closest_forecast, forecast_data['city']['name'])
            else:
                return {'error': f'No forecast available for {target_date} {target_time}'}
                
        except requests.exceptions.RequestException as e:
            return {'error': f'API connection error: {str(e)}'}
        except ValueError as e:
            return {'error': f'Invalid date/time format: {str(e)}'}
        except Exception as e:
            return {'error': f'Unexpected error: {str(e)}'}
    
    def _format_forecast(self, forecast, city_name):
        """Format forecast data"""
        forecast_time = datetime.fromtimestamp(forecast['dt'])
        return {
            'location': city_name,
            'date': forecast_time.strftime('%Y-%m-%d'),
            'time': forecast_time.strftime('%H:%M'),
            'temperature': f"{forecast['main']['temp']:.1f}°C",
            'feels_like': f"{forecast['main']['feels_like']:.1f}°C",
            'humidity': f"{forecast['main']['humidity']}%",
            'description': forecast['weather'][0]['description'].capitalize(),
            'wind_speed': f"{forecast['wind']['speed']:.1f} m/s",
            'pressure': f"{forecast['main']['pressure']} hPa",
            'rain_probability': f"{forecast.get('pop', 0) * 100:.0f}%" if 'pop' in forecast else "0%"
        }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/weather', methods=['POST'])
def get_weather():
    try:
        data = request.get_json()
        location = data.get('location')
        date = data.get('date')
        time = data.get('time')
        
        if not all([location, date, time]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        weather_system = WeatherSystem(API_KEY)
        result = weather_system.get_weather_for_datetime(location, date, time)
        
        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 404
        else:
            return jsonify({'success': True, 'data': result})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    # Check if API key is set
    if API_KEY == 'YOUR_API_KEY_HERE':
        print("\n" + "="*50)
        print("⚠️  WARNING: Please set your OpenWeatherMap API key!")
        print("="*50)
        print("\nOptions:")
        print("1. Create a .env file with: OPENWEATHER_API_KEY=your_key_here")
        print("2. Or edit app.py and replace 'YOUR_API_KEY_HERE' with your key")
        print("\nGet a free API key at: https://openweathermap.org/api")
        print("="*50 + "\n")
    
    print("\n🚀 Starting Weather Server...")
    print("📱 Access the app at: http://127.0.0.1:5000")
    print("🛑 Press CTRL+C to stop the server\n")
    app.run(debug=True, host='127.0.0.1', port=5000)