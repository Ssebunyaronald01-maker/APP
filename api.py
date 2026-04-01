import requests
from datetime import datetime, timedelta
import json
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

class WeatherSystem:
    def __init__(self, api_key: str):
        """
        Initialize the weather system with your API key
        Sign up for a free API key at: https://openweathermap.org/api
        """
        self.api_key = api_key
        self.base_url = "http://api.openweathermap.org/data/2.5"
        
    def get_coordinates(self, location: str) -> Optional[tuple]:
        """Convert location name to coordinates"""
        geocoding_url = f"http://api.openweathermap.org/geo/1.0/direct"
        params = {
            'q': location,
            'limit': 1,
            'appid': self.api_key
        }
        
        try:
            response = requests.get(geocoding_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data:
                lat = data[0]['lat']
                lon = data[0]['lon']
                return (lat, lon)
            else:
                print(f"Location '{location}' not found")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Error getting coordinates: {e}")
            return None
    
    def get_current_weather(self, location: str) -> Optional[Dict[str, Any]]:
        """Get current weather for a location"""
        coords = self.get_coordinates(location)
        if not coords:
            return None
            
        weather_url = f"{self.base_url}/weather"
        params = {
            'lat': coords[0],
            'lon': coords[1],
            'appid': self.api_key,
            'units': 'metric'  # Use 'imperial' for Fahrenheit
        }
        
        try:
            response = requests.get(weather_url, params=params)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error getting weather: {e}")
            return None
    
    def get_forecast(self, location: str, days: int = 5) -> Optional[Dict[str, Any]]:
        """Get weather forecast for a location"""
        coords = self.get_coordinates(location)
        if not coords:
            return None
            
        forecast_url = f"{self.base_url}/forecast"
        params = {
            'lat': coords[0],
            'lon': coords[1],
            'appid': self.api_key,
            'units': 'metric',
            'cnt': days * 8  # 8 forecasts per day (every 3 hours)
        }
        
        try:
            response = requests.get(forecast_url, params=params)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error getting forecast: {e}")
            return None
    
    def get_weather_for_datetime(self, location: str, target_date: str, target_time: str) -> Optional[Dict[str, Any]]:
        """
        Get weather for a specific date and time
        
        Args:
            location: City name or location
            target_date: Date in format 'YYYY-MM-DD'
            target_time: Time in format 'HH:MM' (24-hour format)
        """
        try:
            # Parse the target datetime
            target_datetime = datetime.strptime(f"{target_date} {target_time}", "%Y-%m-%d %H:%M")
            current_time = datetime.now()
            
            # Check if the target is in the past or future
            if target_datetime.date() == current_time.date():
                # Today - get current weather
                weather_data = self.get_current_weather(location)
                if weather_data:
                    return self._format_current_weather(weather_data)
                    
            elif target_datetime > current_time:
                # Future - get forecast
                days_ahead = (target_datetime - current_time).days + 1
                forecast_data = self.get_forecast(location, min(days_ahead, 5))
                
                if forecast_data:
                    return self._find_closest_forecast(forecast_data, target_datetime)
            else:
                # Past - note: free APIs don't provide historical data
                return {
                    'error': 'Historical weather data requires premium API access',
                    'message': 'Please use a weather API with historical data support'
                }
            
            return None
            
        except ValueError as e:
            print(f"Invalid date/time format: {e}")
            return None
    
    def _find_closest_forecast(self, forecast_data: Dict, target_datetime: datetime) -> Dict[str, Any]:
        """Find the closest forecast to the target datetime"""
        closest_forecast = None
        min_time_diff = float('inf')
        
        for forecast in forecast_data['list']:
            forecast_time = datetime.fromtimestamp(forecast['dt'])
            time_diff = abs((forecast_time - target_datetime).total_seconds())
            
            if time_diff < min_time_diff:
                min_time_diff = time_diff
                closest_forecast = forecast
        
        if closest_forecast:
            return self._format_forecast(closest_forecast, forecast_data['city']['name'])
        
        return None
    
    def _format_current_weather(self, data: Dict) -> Dict[str, Any]:
        """Format current weather data"""
        return {
            'location': data['name'],
            'date': datetime.fromtimestamp(data['dt']).strftime('%Y-%m-%d'),
            'time': datetime.fromtimestamp(data['dt']).strftime('%H:%M'),
            'temperature': f"{data['main']['temp']}°C",
            'feels_like': f"{data['main']['feels_like']}°C",
            'humidity': f"{data['main']['humidity']}%",
            'description': data['weather'][0]['description'].capitalize(),
            'wind_speed': f"{data['wind']['speed']} m/s",
            'pressure': f"{data['main']['pressure']} hPa"
        }
    
    def _format_forecast(self, forecast: Dict, city_name: str) -> Dict[str, Any]:
        """Format forecast data"""
        forecast_time = datetime.fromtimestamp(forecast['dt'])
        return {
            'location': city_name,
            'date': forecast_time.strftime('%Y-%m-%d'),
            'time': forecast_time.strftime('%H:%M'),
            'temperature': f"{forecast['main']['temp']}°C",
            'feels_like': f"{forecast['main']['feels_like']}°C",
            'humidity': f"{forecast['main']['humidity']}%",
            'description': forecast['weather'][0]['description'].capitalize(),
            'wind_speed': f"{forecast['wind']['speed']} m/s",
            'pressure': f"{forecast['main']['pressure']} hPa",
            'rain_probability': f"{forecast.get('pop', 0) * 100}%" if 'pop' in forecast else "N/A"
        }

class WeatherCLI:
    """Command-line interface for the weather system"""
    
    def __init__(self, api_key: str):
        self.weather_system = WeatherSystem(api_key)
    
    def run(self):
        """Main CLI loop"""
        print("=" * 50)
        print("🌤️  Weather Query System")
        print("=" * 50)
        
        while True:
            print("\nEnter weather query details:")
            print("-" * 30)
            
            # Get location
            location = input("Location (e.g., 'London,UK'): ").strip()
            if not location:
                print("Location cannot be empty!")
                continue
            
            # Get date
            print("\nDate format: YYYY-MM-DD")
            print("Examples: 2024-12-25, 2024-01-15")
            date = input("Date: ").strip()
            
            # Get time
            print("\nTime format: HH:MM (24-hour)")
            print("Examples: 14:30, 09:00, 23:45")
            time = input("Time: ").strip()
            
            print("\n" + "=" * 50)
            print(f"Querying weather for {location} on {date} at {time}")
            print("=" * 50 + "\n")
            
            # Get weather data
            weather_info = self.weather_system.get_weather_for_datetime(location, date, time)
            
            if weather_info:
                if 'error' in weather_info:
                    print(f"⚠️  {weather_info['error']}")
                    print(f"ℹ️  {weather_info['message']}")
                else:
                    self._display_weather(weather_info)
            else:
                print("❌ Unable to retrieve weather information.")
                print("   Please check:")
                print("   - Location name is correct")
                print("   - Date is within forecast range (max 5 days)")
                print("   - Your internet connection")
            
            # Ask if user wants to continue
            print("\n" + "-" * 30)
            again = input("Another query? (y/n): ").strip().lower()
            if again != 'y':
                print("\nThank you for using Weather Query System! 👋")
                break
    
    def _display_weather(self, weather_info: Dict):
        """Display weather information in a nice format"""
        print(f"📍 Location: {weather_info['location']}")
        print(f"📅 Date: {weather_info['date']}")
        print(f"⏰ Time: {weather_info['time']}")
        print("-" * 30)
        print(f"🌡️  Temperature: {weather_info['temperature']}")
        print(f"🤔 Feels like: {weather_info['feels_like']}")
        print(f"☁️  Conditions: {weather_info['description']}")
        print(f"💧 Humidity: {weather_info['humidity']}")
        print(f"💨 Wind Speed: {weather_info['wind_speed']}")
        print(f"📊 Pressure: {weather_info['pressure']}")
        
        if 'rain_probability' in weather_info:
            print(f"🌧️  Rain Probability: {weather_info['rain_probability']}")

# Example usage
if __name__ == "__main__":
    # You need to sign up for a free API key at https://openweathermap.org/api
    API_KEY = "eaae7b70d17ad77c4da4367c196027d6"  # Replace with your actual API key
    
    if API_KEY == "eaae7b70d17ad77c4da4367c196027d6":
        print("⚠️  Please set your OpenWeatherMap API key first!")
        print("Get a free key at: https://openweathermap.org/api")
    else:
        cli = WeatherCLI(API_KEY)
        cli.run()