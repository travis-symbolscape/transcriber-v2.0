import os
from dotenv import load_dotenv
from graphhopper_client import GraphHopperClient

# Load environment variables from .env file
load_dotenv()

def get_graphhopper_client():
    """Get a GraphHopper client using API key from environment variable"""
    api_key = os.getenv('GRAPHHOPPER_API_KEY')
    if not api_key:
        raise ValueError("GRAPHHOPPER_API_KEY environment variable not set")
    return GraphHopperClient(api_key)

# Example usage
if __name__ == "__main__":
    try:
        client = get_graphhopper_client()
        print("GraphHopper client initialized successfully!")
        
        # Test geocoding
        result = client.geocode("San Francisco")
        if result.get("hits"):
            location = result["hits"][0]
            print(f"Found: {location['name']}")
            print(f"Coordinates: {location['point']['lat']}, {location['point']['lng']}")
            
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure to create a .env file with your GRAPHHOPPER_API_KEY")
