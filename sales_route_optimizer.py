import csv
import os
import json
from typing import List, Dict, Tuple
from dotenv import load_dotenv
from graphhopper_client import GraphHopperClient

# Load environment variables
load_dotenv()

class SalesRouteOptimizer:
    """Optimize sales routes and export to Google Maps"""
    
    def __init__(self):
        api_key = os.getenv('GRAPHHOPPER_API_KEY')
        if not api_key:
            raise ValueError("GRAPHHOPPER_API_KEY not found in environment variables")
        self.client = GraphHopperClient(api_key)
    
    def load_csv(self, csv_file: str) -> List[Dict]:
        """Load business data from CSV file"""
        businesses = []
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            
            for row in reader:
                if len(row) >= 3 and row[2].strip():  # Has address
                    business = {
                        'type': row[0],
                        'name': row[1], 
                        'address': row[2],
                        'zip': row[3] if len(row) > 3 else '',
                        'phone': row[4] if len(row) > 4 else '',
                        'website': row[5] if len(row) > 5 else ''
                    }
                    businesses.append(business)
        
        print(f"Loaded {len(businesses)} businesses from CSV")
        return businesses
    
    def geocode_businesses(self, businesses: List[Dict]) -> List[Dict]:
        """Geocode all business addresses"""
        geocoded = []
        failed = []
        
        for i, business in enumerate(businesses):
            print(f"Geocoding {i+1}/{len(businesses)}: {business['name']}")
            
            try:
                result = self.client.geocode(business['address'])
                if result.get('hits'):
                    location = result['hits'][0]
                    business['latitude'] = location['point']['lat']
                    business['longitude'] = location['point']['lng']
                    business['geocoded_address'] = location.get('name', business['address'])
                    geocoded.append(business)
                else:
                    failed.append(business)
                    print(f"  ❌ Could not geocode: {business['address']}")
            except Exception as e:
                failed.append(business)
                print(f"  ❌ Error: {e}")
        
        print(f"\n✅ Successfully geocoded: {len(geocoded)}")
        print(f"❌ Failed to geocode: {len(failed)}")
        
        return geocoded, failed
    
    def optimize_route(self, businesses: List[Dict], start_address: str = None) -> List[Dict]:
        """Optimize the route order using GraphHopper's matrix API"""
        
        # Add starting point if provided
        points = []
        if start_address:
            try:
                start_result = self.client.geocode(start_address)
                if start_result.get('hits'):
                    start_location = start_result['hits'][0]
                    start_point = {
                        'name': 'START',
                        'address': start_address,
                        'latitude': start_location['point']['lat'],
                        'longitude': start_location['point']['lng'],
                        'type': 'Starting Point'
                    }
                    points.append(start_point)
            except Exception as e:
                print(f"Could not geocode starting address: {e}")
        
        # Add all businesses
        points.extend(businesses)
        
        if len(points) < 2:
            return points
        
        # Extract coordinates for matrix calculation
        coordinates = [(point['latitude'], point['longitude']) for point in points]
        
        try:
            print("Calculating optimal route...")
            matrix_result = self.client.matrix(coordinates)
            
            if 'times' in matrix_result:
                # Simple nearest neighbor optimization
                optimized_order = self.nearest_neighbor_optimize(matrix_result['times'])
                optimized_route = [points[i] for i in optimized_order]
                
                # Calculate total time and distance
                total_time = sum(matrix_result['times'][optimized_order[i]][optimized_order[i+1]] 
                               for i in range(len(optimized_order)-1))
                
                print(f"✅ Route optimized! Total travel time: {total_time/60000:.1f} minutes")
                return optimized_route
            else:
                print("⚠️  Matrix optimization failed, using original order")
                return points
                
        except Exception as e:
            print(f"⚠️  Optimization failed: {e}")
            print("Using original order")
            return points
    
    def nearest_neighbor_optimize(self, time_matrix: List[List[int]]) -> List[int]:
        """Simple nearest neighbor algorithm for route optimization"""
        n = len(time_matrix)
        unvisited = set(range(1, n))  # Start from point 0
        route = [0]
        current = 0
        
        while unvisited:
            nearest = min(unvisited, key=lambda x: time_matrix[current][x])
            route.append(nearest)
            unvisited.remove(nearest)
            current = nearest
        
        return route
    
    def export_google_maps_url(self, optimized_route: List[Dict]) -> str:
        """Create Google Maps URL with all waypoints"""
        
        if len(optimized_route) < 2:
            return "Not enough points for route"
        
        # Start point
        start = optimized_route[0]
        start_coords = f"{start['latitude']},{start['longitude']}"
        
        # End point (last business)
        end = optimized_route[-1]
        end_coords = f"{end['latitude']},{end['longitude']}"
        
        # Waypoints (middle points)
        waypoints = []
        for business in optimized_route[1:-1]:  # Skip first and last
            waypoints.append(f"{business['latitude']},{business['longitude']}")
        
        # Build Google Maps URL
        base_url = "https://www.google.com/maps/dir/"
        
        if waypoints:
            waypoint_str = "/".join(waypoints)
            url = f"{base_url}{start_coords}/{waypoint_str}/{end_coords}"
        else:
            url = f"{base_url}{start_coords}/{end_coords}"
        
        return url
    
    def export_csv(self, optimized_route: List[Dict], filename: str):
        """Export optimized route to CSV"""
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            fieldnames = ['order', 'type', 'name', 'address', 'phone', 'latitude', 'longitude', 'website']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            
            for i, business in enumerate(optimized_route):
                writer.writerow({
                    'order': i + 1,
                    'type': business.get('type', ''),
                    'name': business.get('name', ''),
                    'address': business.get('address', ''),
                    'phone': business.get('phone', ''),
                    'latitude': business.get('latitude', ''),
                    'longitude': business.get('longitude', ''),
                    'website': business.get('website', '')
                })
        
        print(f"📁 Exported route to {filename}")

def main():
    """Main function to run the sales route optimizer"""
    
    # Initialize optimizer
    optimizer = SalesRouteOptimizer()
    
    # Load your CSV
    csv_file = '/Users/workspace/Downloads/NST- Chico - Sheet3.csv'
    businesses = optimizer.load_csv(csv_file)
    
    # Geocode all addresses
    geocoded_businesses, failed = optimizer.geocode_businesses(businesses)
    
    if not geocoded_businesses:
        print("❌ No businesses were successfully geocoded!")
        return
    
    # Get starting point
    start_address = input("\nEnter your starting address (or press Enter to skip): ").strip()
    if not start_address:
        start_address = None
    
    # Optimize route
    optimized_route = optimizer.optimize_route(geocoded_businesses, start_address)
    
    # Show route summary
    print(f"\n🗺️  OPTIMIZED SALES ROUTE:")
    print("=" * 50)
    for i, business in enumerate(optimized_route):
        if business.get('name') == 'START':
            print(f"{i+1:2d}. 🏠 START: {business['address']}")
        else:
            print(f"{i+1:2d}. {business['type']}: {business['name']}")
            print(f"    📍 {business['address']}")
            if business.get('phone'):
                print(f"    📞 {business['phone']}")
    
    # Export results
    optimizer.export_csv(optimized_route, 'optimized_sales_route.csv')
    
    # Generate Google Maps URL
    google_url = optimizer.export_google_maps_url(optimized_route)
    
    print(f"\n🔗 GOOGLE MAPS URL:")
    print("=" * 50)
    print(google_url)
    
    # Save URL to file
    with open('google_maps_route.txt', 'w') as f:
        f.write(google_url)
    
    print(f"\n📱 MOBILE INSTRUCTIONS:")
    print("=" * 50)
    print("1. Copy the Google Maps URL above")
    print("2. Open it on your phone")
    print("3. Tap 'Directions' in Google Maps")
    print("4. Start navigation!")
    
    if failed:
        print(f"\n⚠️  ADDRESSES THAT COULDN'T BE GEOCODED:")
        for business in failed:
            print(f"   • {business['name']}: {business['address']}")

if __name__ == "__main__":
    main()
