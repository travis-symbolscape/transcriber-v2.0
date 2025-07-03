import csv
import json
import time
import requests
from typing import List, Dict, Tuple
import itertools
import math

class LocalGraphHopperClient:
    """Client for self-hosted GraphHopper server with route optimization"""
    
    def __init__(self, base_url: str = "http://localhost:8989"):
        self.base_url = base_url
        self.geocoding_url = f"{base_url}/geocode"
        self.routing_url = f"{base_url}/route"
        
    def wait_for_server(self, max_wait_minutes: int = 10):
        """Wait for GraphHopper server to be ready"""
        max_wait_seconds = max_wait_minutes * 60
        check_interval = 10
        elapsed = 0
        
        print("Waiting for GraphHopper server to be ready...")
        
        while elapsed < max_wait_seconds:
            try:
                response = requests.get(f"{self.base_url}/health", timeout=5)
                if response.status_code == 200:
                    print("✅ GraphHopper server is ready!")
                    return True
            except:
                pass
            
            print(f"⏳ Still starting up... ({elapsed//60:.0f}m {elapsed%60:.0f}s)")
            time.sleep(check_interval)
            elapsed += check_interval
        
        raise Exception(f"GraphHopper server not ready after {max_wait_minutes} minutes")
    
    def geocode(self, address: str) -> Dict:
        """Geocode an address using local GraphHopper"""
        params = {
            "q": address,
            "limit": 1
        }
        
        response = requests.get(self.geocoding_url, params=params)
        response.raise_for_status()
        return response.json()
    
    def route(self, points: List[Tuple[float, float]], vehicle: str = "car") -> Dict:
        """Calculate route between points"""
        params = {
            "vehicle": vehicle,
            "calc_points": "true",
            "instructions": "true"
        }
        
        # Add points
        for lat, lon in points:
            params[f"point"] = f"{lat},{lon}"
        
        response = requests.get(self.routing_url, params=params)
        response.raise_for_status()
        return response.json()
    
    def load_csv_addresses(self, csv_file: str) -> List[Dict]:
        """Load addresses from CSV"""
        locations = []
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            
            for i, row in enumerate(reader):
                if len(row) >= 3 and row[2].strip():  # Has address
                    location = {
                        "id": i,
                        "type": row[0] if row[0] else "Business",
                        "name": row[1] if row[1] else f"Stop {i}",
                        "address": row[2],
                        "phone": row[4] if len(row) > 4 else "",
                        "website": row[5] if len(row) > 5 else ""
                    }
                    locations.append(location)
        
        print(f"Loaded {len(locations)} locations from CSV")
        return locations
    
    def geocode_locations(self, locations: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """Geocode all locations"""
        geocoded = []
        failed = []
        
        for i, location in enumerate(locations):
            print(f"Geocoding {i+1}/{len(locations)}: {location['name']}")
            
            try:
                result = self.geocode(location['address'])
                if result.get('hits') and len(result['hits']) > 0:
                    hit = result['hits'][0]
                    location['latitude'] = hit['point']['lat']
                    location['longitude'] = hit['point']['lng']
                    location['geocoded_address'] = hit.get('name', location['address'])
                    geocoded.append(location)
                    print(f"  ✅ {location['latitude']:.4f}, {location['longitude']:.4f}")
                else:
                    failed.append(location)
                    print(f"  ❌ No results found")
            except Exception as e:
                failed.append(location)
                print(f"  ❌ Error: {e}")
        
        print(f"\n✅ Successfully geocoded: {len(geocoded)}")
        print(f"❌ Failed to geocode: {len(failed)}")
        
        return geocoded, failed
    
    def calculate_distance_matrix(self, locations: List[Dict]) -> List[List[float]]:
        """Calculate distance matrix between all locations"""
        n = len(locations)
        matrix = [[0.0 for _ in range(n)] for _ in range(n)]
        
        print(f"Calculating distance matrix for {n} locations...")
        
        for i in range(n):
            for j in range(i + 1, n):
                try:
                    point1 = (locations[i]['latitude'], locations[i]['longitude'])
                    point2 = (locations[j]['latitude'], locations[j]['longitude'])
                    
                    route_result = self.route([point1, point2])
                    
                    if route_result.get('paths'):
                        distance = route_result['paths'][0]['distance']  # meters
                        matrix[i][j] = distance
                        matrix[j][i] = distance
                    else:
                        # Fallback to straight-line distance
                        distance = self.haversine_distance(point1, point2)
                        matrix[i][j] = distance
                        matrix[j][i] = distance
                        
                except Exception as e:
                    # Fallback to straight-line distance
                    point1 = (locations[i]['latitude'], locations[i]['longitude'])
                    point2 = (locations[j]['latitude'], locations[j]['longitude'])
                    distance = self.haversine_distance(point1, point2)
                    matrix[i][j] = distance
                    matrix[j][i] = distance
                
                if (i * n + j) % 10 == 0:
                    progress = ((i * n + j) / (n * n)) * 100
                    print(f"  Progress: {progress:.1f}%")
        
        return matrix
    
    def haversine_distance(self, point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """Calculate straight-line distance between two points in meters"""
        lat1, lon1 = point1
        lat2, lon2 = point2
        
        R = 6371000  # Earth's radius in meters
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def nearest_neighbor_tsp(self, distance_matrix: List[List[float]], start_index: int = 0) -> List[int]:
        """Solve TSP using nearest neighbor algorithm"""
        n = len(distance_matrix)
        unvisited = set(range(n))
        unvisited.remove(start_index)
        
        route = [start_index]
        current = start_index
        
        while unvisited:
            nearest = min(unvisited, key=lambda x: distance_matrix[current][x])
            route.append(nearest)
            unvisited.remove(nearest)
            current = nearest
        
        # Return to start
        route.append(start_index)
        return route
    
    def optimize_route(self, locations: List[Dict], start_address: str = None) -> List[Dict]:
        """Optimize route using TSP algorithm"""
        
        # Add start location if provided
        all_locations = locations.copy()
        start_index = 0
        
        if start_address:
            try:
                start_result = self.geocode(start_address)
                if start_result.get('hits'):
                    start_location = {
                        'id': 'start',
                        'name': 'START',
                        'type': 'Starting Point',
                        'address': start_address,
                        'latitude': start_result['hits'][0]['point']['lat'],
                        'longitude': start_result['hits'][0]['point']['lng'],
                        'phone': '',
                        'website': ''
                    }
                    all_locations.insert(0, start_location)
                    print(f"✅ Added start location: {start_address}")
            except Exception as e:
                print(f"⚠️  Could not geocode start address: {e}")
        
        if len(all_locations) < 2:
            return all_locations
        
        # Calculate distance matrix
        distance_matrix = self.calculate_distance_matrix(all_locations)
        
        # Solve TSP
        print("Solving TSP optimization...")
        optimal_route_indices = self.nearest_neighbor_tsp(distance_matrix, start_index)
        
        # Build optimized route
        optimized_route = [all_locations[i] for i in optimal_route_indices[:-1]]  # Remove duplicate start
        
        # Calculate total distance
        total_distance = sum(distance_matrix[optimal_route_indices[i]][optimal_route_indices[i+1]] 
                           for i in range(len(optimal_route_indices)-1))
        
        print(f"✅ Route optimized! Total distance: {total_distance/1000:.1f} km")
        
        return optimized_route
    
    def export_google_maps_url(self, optimized_route: List[Dict]) -> str:
        """Create Google Maps URL from optimized route"""
        
        if len(optimized_route) < 2:
            return "Not enough points for route"
        
        # Use addresses for better Google Maps compatibility
        addresses = [location["address"] for location in optimized_route[:10]]  # Google Maps limit
        
        encoded_addresses = [address.replace(" ", "+").replace(",", "%2C") for address in addresses]
        waypoints = "/".join(encoded_addresses)
        url = f"https://www.google.com/maps/dir/{waypoints}"
        
        return url
    
    def export_csv(self, optimized_route: List[Dict], filename: str):
        """Export optimized route to CSV"""
        
        fieldnames = ['order', 'type', 'name', 'address', 'phone', 'website', 'latitude', 'longitude']
        
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            
            for i, location in enumerate(optimized_route):
                writer.writerow({
                    'order': i + 1,
                    'type': location.get('type', ''),
                    'name': location.get('name', ''),
                    'address': location.get('address', ''),
                    'phone': location.get('phone', ''),
                    'website': location.get('website', ''),
                    'latitude': location.get('latitude', ''),
                    'longitude': location.get('longitude', '')
                })
        
        print(f"📁 Exported optimized route to {filename}")

def main():
    """Main function to run local GraphHopper route optimization"""
    
    try:
        # Initialize client
        client = LocalGraphHopperClient()
        
        # Wait for server to be ready
        client.wait_for_server()
        
        # Load CSV data
        csv_file = '/Users/workspace/Downloads/NST- Chico - Sheet3.csv'
        locations = client.load_csv_addresses(csv_file)
        
        if not locations:
            print("❌ No valid locations found in CSV!")
            return
        
        # Geocode all locations
        geocoded_locations, failed = client.geocode_locations(locations)
        
        if not geocoded_locations:
            print("❌ No locations were successfully geocoded!")
            return
        
        # Get starting address
        start_address = input("\nEnter your starting address (optional, press Enter to skip): ").strip()
        if not start_address:
            start_address = None
        
        # Optimize route
        optimized_route = client.optimize_route(geocoded_locations, start_address)
        
        # Display results
        print(f"\n🗺️  OPTIMIZED SALES ROUTE ({len(optimized_route)} stops):")
        print("=" * 60)
        
        for i, location in enumerate(optimized_route):
            if location.get('name') == 'START':
                print(f"{i+1:2d}. 🏠 START: {location['address']}")
            else:
                print(f"{i+1:2d}. {location['type']}: {location['name']}")
                print(f"    📍 {location['address']}")
                if location.get('phone'):
                    print(f"    📞 {location['phone']}")
        
        # Export results
        client.export_csv(optimized_route, 'local_graphhopper_optimized_route.csv')
        
        # Generate Google Maps URL
        google_url = client.export_google_maps_url(optimized_route)
        
        print(f"\n🔗 GOOGLE MAPS URL:")
        print("=" * 60)
        print(google_url)
        
        # Save URL to file
        with open('local_graphhopper_google_route.txt', 'w') as f:
            f.write(google_url)
        
        print(f"\n📱 MOBILE INSTRUCTIONS:")
        print("=" * 60)
        print("1. Copy the Google Maps URL above")
        print("2. Open it on your phone")
        print("3. Tap 'Directions' in Google Maps")
        print("4. Start your optimized sales route!")
        
        if failed:
            print(f"\n⚠️  ADDRESSES THAT COULDN'T BE GEOCODED:")
            for location in failed:
                print(f"   • {location['name']}: {location['address']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
