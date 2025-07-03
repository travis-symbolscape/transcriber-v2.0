import requests
import json
from typing import Dict, List, Tuple, Optional

class GraphHopperClient:
    """A simple client for GraphHopper API services"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://graphhopper.com/api/1"
        
    def route(self, points: List[Tuple[float, float]], vehicle: str = "car", 
              locale: str = "en", instructions: bool = True) -> Dict:
        """
        Calculate a route between multiple points
        
        Args:
            points: List of (latitude, longitude) tuples
            vehicle: Transportation mode (car, bike, foot, motorcycle, etc.)
            locale: Language for instructions
            instructions: Whether to include turn-by-turn instructions
            
        Returns:
            Dictionary with route information
        """
        url = f"{self.base_url}/route"
        
        # Add points to parameters - each point needs its own parameter
        point_params = []
        for lat, lon in points:
            point_params.append(f"{lat},{lon}")
        
        # Create URL with multiple point parameters
        point_query = '&'.join([f"point={point}" for point in point_params])
        full_url = f"{url}?key={self.api_key}&vehicle={vehicle}&locale={locale}&instructions={instructions}&calc_points=True&debug=False&{point_query}"
        
        response = requests.get(full_url)
        response.raise_for_status()
        
        return response.json()
    
    def geocode(self, query: str, limit: int = 10) -> Dict:
        """
        Geocode an address or place name
        
        Args:
            query: Address or place name to geocode
            limit: Maximum number of results to return
            
        Returns:
            Dictionary with geocoding results
        """
        url = f"{self.base_url}/geocode"
        
        params = {
            "key": self.api_key,
            "q": query,
            "limit": limit
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        return response.json()
    
    def reverse_geocode(self, lat: float, lon: float) -> Dict:
        """
        Reverse geocode coordinates to get address
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Dictionary with reverse geocoding results
        """
        url = f"{self.base_url}/geocode"
        
        params = {
            "key": self.api_key,
            "reverse": "true",
            "point": f"{lat},{lon}"
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        return response.json()
    
    def matrix(self, points: List[Tuple[float, float]], vehicle: str = "car") -> Dict:
        """
        Calculate distance/time matrix between multiple points
        
        Args:
            points: List of (latitude, longitude) tuples
            vehicle: Transportation mode
            
        Returns:
            Dictionary with matrix results
        """
        url = f"{self.base_url}/matrix"
        
        data = {
            "points": [[lon, lat] for lat, lon in points],
            "vehicle": vehicle,
            "out_arrays": ["times", "distances"]
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        params = {"key": self.api_key}
        
        response = requests.post(url, json=data, headers=headers, params=params)
        response.raise_for_status()
        
        return response.json()

# Example usage
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Initialize client with API key from environment
    api_key = os.getenv('GRAPHHOPPER_API_KEY')
    if not api_key:
        print("Error: GRAPHHOPPER_API_KEY not found in environment variables")
        print("Please create a .env file with your API key")
        exit(1)
    
    client = GraphHopperClient(api_key)
    
    # Example 1: Geocoding
    print("=== Geocoding Example ===")
    try:
        result = client.geocode("New York City")
        if result.get("hits"):
            location = result["hits"][0]
            print(f"Found: {location['name']}")
            print(f"Coordinates: {location['point']['lat']}, {location['point']['lng']}")
    except Exception as e:
        print(f"Geocoding error: {e}")
    
    # Example 2: Simple route
    print("\n=== Routing Example ===")
    try:
        # Route from NYC to Philadelphia (approximate coordinates)
        points = [
            (40.7128, -74.0060),  # New York City
            (39.9526, -75.1652)   # Philadelphia
        ]
        
        route_result = client.route(points, vehicle="car")
        
        if route_result.get("paths"):
            path = route_result["paths"][0]
            distance_km = path["distance"] / 1000
            time_minutes = path["time"] / 60000
            
            print(f"Distance: {distance_km:.2f} km")
            print(f"Time: {time_minutes:.0f} minutes")
            
            if path.get("instructions"):
                print("\nTurn-by-turn instructions:")
                for i, instruction in enumerate(path["instructions"][:5]):  # First 5 instructions
                    print(f"{i+1}. {instruction['text']}")
                if len(path["instructions"]) > 5:
                    print(f"... and {len(path['instructions']) - 5} more instructions")
    except Exception as e:
        print(f"Routing error: {e}")
