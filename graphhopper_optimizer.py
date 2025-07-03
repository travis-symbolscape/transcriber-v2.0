import csv
import json
import time
import requests
import os
from typing import List, Dict, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class GraphHopperRouteOptimizer:
    """Use GraphHopper's Route Optimization API for sales route optimization"""
    
    def __init__(self):
        self.api_key = os.getenv('GRAPHHOPPER_API_KEY')
        if not self.api_key:
            raise ValueError("GRAPHHOPPER_API_KEY not found in environment variables")
        
        self.base_url = "https://graphhopper.com/api/1"
        self.optimization_url = f"{self.base_url}/vrp"
    
    def load_csv_addresses(self, csv_file: str) -> List[Dict]:
        """Load addresses from CSV and prepare for optimization"""
        locations = []
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            
            for i, row in enumerate(reader):
                if len(row) >= 3 and row[2].strip():  # Has address
                    location = {
                        "id": f"stop_{i}",
                        "type": row[0] if row[0] else "Business",
                        "name": row[1] if row[1] else f"Stop {i}",
                        "address": row[2],
                        "phone": row[4] if len(row) > 4 else "",
                        "website": row[5] if len(row) > 5 else ""
                    }
                    locations.append(location)
        
        print(f"Loaded {len(locations)} locations from CSV")
        return locations
    
    def create_optimization_request(self, locations: List[Dict], start_address: str = None) -> Dict:
        """Create GraphHopper Route Optimization API request"""
        
        # Build locations array for the API
        api_locations = []
        
        # Add start location if provided
        if start_address:
            api_locations.append({
                "id": "start",
                "lon": 0,  # Will be geocoded by GraphHopper
                "lat": 0,
                "address": {"location_name": start_address}
            })
        
        # Add all business locations
        for location in locations:
            api_locations.append({
                "id": location["id"],
                "lon": 0,  # Will be geocoded by GraphHopper
                "lat": 0,
                "address": {"location_name": location["address"]}
            })
        
        # Create vehicles (sales person)
        vehicles = [{
            "vehicle_id": "sales_vehicle",
            "type_id": "car",
            "start_address": {
                "location_id": "start" if start_address else locations[0]["id"]
            },
            "end_address": {
                "location_id": "start" if start_address else locations[0]["id"]
            }
        }]
        
        # Create services (business visits)
        services = []
        for location in locations:
            services.append({
                "id": location["id"],
                "type": "service",
                "address": {
                    "location_id": location["id"]
                },
                "duration": 900,  # 15 minutes per visit
                "name": location["name"]
            })
        
        # Create vehicle types
        vehicle_types = [{
            "type_id": "car",
            "profile": "car"
        }]
        
        # Build the optimization request
        optimization_request = {
            "vehicles": vehicles,
            "vehicle_types": vehicle_types,
            "services": services,
            "locations": api_locations,
            "objectives": [{
                "type": "min",
                "value": "completion_time"
            }]
        }
        
        return optimization_request
    
    def submit_optimization(self, request_data: Dict) -> str:
        """Submit route optimization job to GraphHopper"""
        
        headers = {
            "Content-Type": "application/json"
        }
        
        params = {
            "key": self.api_key
        }
        
        print("Submitting route optimization request...")
        print(f"Optimizing {len(request_data['services'])} stops...")
        
        response = requests.post(
            self.optimization_url,
            json=request_data,
            headers=headers,
            params=params
        )
        
        if response.status_code == 202:
            result = response.json()
            job_id = result.get("job_id")
            print(f"✅ Optimization job submitted successfully!")
            print(f"Job ID: {job_id}")
            return job_id
        else:
            print(f"❌ Error submitting optimization: {response.status_code}")
            print(f"Response: {response.text}")
            raise Exception(f"Optimization submission failed: {response.text}")
    
    def check_optimization_status(self, job_id: str) -> Dict:
        """Check the status of an optimization job"""
        
        url = f"{self.optimization_url}/solution/{job_id}"
        params = {"key": self.api_key}
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to check job status: {response.text}")
    
    def wait_for_optimization(self, job_id: str, max_wait_minutes: int = 10) -> Dict:
        """Wait for optimization to complete and return results"""
        
        max_wait_seconds = max_wait_minutes * 60
        check_interval = 5  # Check every 5 seconds
        elapsed = 0
        
        print(f"Waiting for optimization to complete...")
        
        while elapsed < max_wait_seconds:
            try:
                result = self.check_optimization_status(job_id)
                status = result.get("status")
                
                if status == "finished":
                    print("✅ Optimization completed successfully!")
                    return result
                elif status == "failed":
                    print("❌ Optimization failed!")
                    print(f"Error: {result}")
                    raise Exception("Optimization failed")
                else:
                    print(f"⏳ Status: {status} - waiting...")
                    time.sleep(check_interval)
                    elapsed += check_interval
                    
            except Exception as e:
                print(f"Error checking status: {e}")
                time.sleep(check_interval)
                elapsed += check_interval
        
        raise Exception(f"Optimization timed out after {max_wait_minutes} minutes")
    
    def parse_optimization_result(self, result: Dict, original_locations: List[Dict]) -> List[Dict]:
        """Parse GraphHopper optimization result into readable format"""
        
        # Create lookup for original location data
        location_lookup = {loc["id"]: loc for loc in original_locations}
        
        optimized_route = []
        
        if "solution" in result and "routes" in result["solution"]:
            route = result["solution"]["routes"][0]  # First (and only) vehicle route
            
            for activity in route.get("activities", []):
                location_id = activity.get("location_id")
                
                if location_id in location_lookup:
                    location_data = location_lookup[location_id].copy()
                    location_data["arrival_time"] = activity.get("arr_time", 0)
                    location_data["end_time"] = activity.get("end_time", 0)
                    optimized_route.append(location_data)
        
        return optimized_route
    
    def export_google_maps_url(self, optimized_route: List[Dict]) -> str:
        """Create Google Maps URL from optimized route"""
        
        if len(optimized_route) < 2:
            return "Not enough points for route"
        
        # Use addresses instead of coordinates for better Google Maps compatibility
        addresses = [location["address"] for location in optimized_route]
        
        # Google Maps has a URL length limit, so use coordinates if too many addresses
        if len(addresses) <= 10:
            # Use addresses for better accuracy
            encoded_addresses = [address.replace(" ", "+").replace(",", "%2C") for address in addresses]
            waypoints = "/".join(encoded_addresses)
            url = f"https://www.google.com/maps/dir/{waypoints}"
        else:
            # Fall back to first few addresses
            start_address = addresses[0].replace(" ", "+").replace(",", "%2C")
            end_address = addresses[-1].replace(" ", "+").replace(",", "%2C")
            middle_addresses = addresses[1:-1][:8]  # Max 8 waypoints
            
            if middle_addresses:
                waypoint_str = "/".join([addr.replace(" ", "+").replace(",", "%2C") for addr in middle_addresses])
                url = f"https://www.google.com/maps/dir/{start_address}/{waypoint_str}/{end_address}"
            else:
                url = f"https://www.google.com/maps/dir/{start_address}/{end_address}"
        
        return url
    
    def export_csv(self, optimized_route: List[Dict], filename: str):
        """Export optimized route to CSV"""
        
        fieldnames = ['order', 'arrival_time', 'type', 'name', 'address', 'phone', 'website']
        
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            
            for i, location in enumerate(optimized_route):
                # Convert arrival time from seconds to readable format
                arrival_seconds = location.get("arrival_time", 0)
                hours = arrival_seconds // 3600
                minutes = (arrival_seconds % 3600) // 60
                arrival_time = f"{hours:02d}:{minutes:02d}"
                
                writer.writerow({
                    'order': i + 1,
                    'arrival_time': arrival_time,
                    'type': location.get('type', ''),
                    'name': location.get('name', ''),
                    'address': location.get('address', ''),
                    'phone': location.get('phone', ''),
                    'website': location.get('website', '')
                })
        
        print(f"📁 Exported optimized route to {filename}")

def main():
    """Main function to run the GraphHopper route optimization"""
    
    try:
        # Initialize optimizer
        optimizer = GraphHopperRouteOptimizer()
        
        # Load your CSV data
        csv_file = '/Users/workspace/Downloads/NST- Chico - Sheet3.csv'
        locations = optimizer.load_csv_addresses(csv_file)
        
        if not locations:
            print("❌ No valid locations found in CSV!")
            return
        
        # Get starting address
        start_address = input("Enter your starting address (optional, press Enter to skip): ").strip()
        if not start_address:
            start_address = None
        
        # Create optimization request
        request_data = optimizer.create_optimization_request(locations, start_address)
        
        # Submit optimization job
        job_id = optimizer.submit_optimization(request_data)
        
        # Wait for results
        result = optimizer.wait_for_optimization(job_id)
        
        # Parse results
        optimized_route = optimizer.parse_optimization_result(result, locations)
        
        if not optimized_route:
            print("❌ No route found in optimization result!")
            return
        
        # Display results
        print(f"\n🗺️  OPTIMIZED SALES ROUTE ({len(optimized_route)} stops):")
        print("=" * 60)
        
        total_time = 0
        for i, location in enumerate(optimized_route):
            arrival_seconds = location.get("arrival_time", 0)
            hours = arrival_seconds // 3600
            minutes = (arrival_seconds % 3600) // 60
            arrival_time = f"{hours:02d}:{minutes:02d}"
            
            print(f"{i+1:2d}. [{arrival_time}] {location['type']}: {location['name']}")
            print(f"    📍 {location['address']}")
            if location.get('phone'):
                print(f"    📞 {location['phone']}")
            
            total_time = max(total_time, arrival_seconds)
        
        print(f"\n⏱️  Total route time: {total_time//3600:.0f}h {(total_time%3600)//60:.0f}m")
        
        # Export results
        optimizer.export_csv(optimized_route, 'graphhopper_optimized_route.csv')
        
        # Generate Google Maps URL
        google_url = optimizer.export_google_maps_url(optimized_route)
        
        print(f"\n🔗 GOOGLE MAPS URL:")
        print("=" * 60)
        print(google_url)
        
        # Save URL to file
        with open('graphhopper_google_route.txt', 'w') as f:
            f.write(google_url)
        
        print(f"\n📱 MOBILE INSTRUCTIONS:")
        print("=" * 60)
        print("1. Copy the Google Maps URL above")
        print("2. Open it on your phone") 
        print("3. Tap 'Directions' in Google Maps")
        print("4. Start your optimized sales route!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
