import requests
import json
import csv

API_KEY = '' #geocoding API key
# Search parameters
search_query = "American Hospital Nad Al Sheba Clinic" #"clinic OR hospital OR doctor OR GP OR general physician"
location = "25.20302751881149, 55.27371932212987" #"25.20302751881149, 55.27371932212987"  # Dubai's latitude, longitude
radius = 20000  # 10 km radius
places_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
details_url = "https://maps.googleapis.com/maps/api/place/details/json"

# Step 1: Get places (clinics, hospitals, doctors)
params = {
    "query": search_query,
    "location": location,
    "radius": radius,
    "key": API_KEY
}

response = requests.get(places_url, params=params).json()
response.keys()


if response.get("status") == "OK":
    places = response.get("results", [])

    # Step 2: Prepare a list to collect all place details
    all_place_details = []

    # Step 3: Get place details
    for place in places:
        name = place.get("name", "N/A")
        formatted_address = place.get("formatted_address", "N/A")
        place_id = place.get("place_id", "N/A")
        types = place.get("types", [])
        geometry = place.get("geometry", {})
        lat = geometry.get("location", {}).get("lat", "N/A")
        lng = geometry.get("location", {}).get("lng", "N/A")
        # Step 2: Call Place Details API to get more data
        details_params = {
            "place_id": place_id,
            "key": API_KEY
        }
        details_response = requests.get(details_url, params=details_params).json()
        if details_response.get("status") == "OK":
            place_details = details_response.get("result")
            print(place_details)
            # Extract more information
            formatted_phone_number = place_details.get("formatted_phone_number", "N/A")
            international_phone_number = place_details.get("international_phone_number", "N/A")
            website = place_details.get("website", "N/A")
            area = place_details.get("area", "N/A")

            adr_address = "N/A"
            if "adr_address" in place_details:
                # Extract building name from adr_address if available
                adr_address = place_details.get("adr_address", "N/A")
                adr_parts = adr_address.split(" - ")
                building_name = adr_parts[0]
            
            # Extract address components to find the locality and area
            address_components = place_details.get("address_components", [])

            landmark = "N/A"
            street_number = "N/A"
            street_name = "N/A"
            area = "N/A"
            area2 = "N/A"
            administrative_area_level_1 = "N/A"
            city = "N/A"

            for component in address_components:
                types = component.get("types", [])
                
                 # Extract street number and street name
                if "landmark" in types:
                    landmark = component.get("long_name", "N/A")
                if "street_number" in types:
                    street_number = component.get("long_name", "N/A")
                elif "route" in types:
                    street_name = component.get("long_name", "N/A")
                # Extract area neighborhood
                elif "neighborhood" in types:  # Look for neighborhood type here
                    area2 = component.get("long_name", "N/A")
                # Extract sublocality
                elif "sublocality" in types:
                    area = component.get("long_name", "N/A")
                # Extract administrative_area_level_1
                elif "administrative_area_level_1" in types:
                    administrative_area_level_1 = component.get("long_name", "N/A")
                # Extract city/locality
                elif "locality" in types:
                    city = component.get("long_name", "N/A")

        # Print extracted information with proper encoding
        place_data = {
            "name": name,
            "formatted_address": formatted_address,
            "place_id": place_id,
            "building": building_name,
            "lat": lat,
            "lng": lng,
            "formatted_phone_number": formatted_phone_number,
            "international_phone_number": international_phone_number,
            "website": website,
            "street_number": street_number,
            "street_name": street_name,
            "area": area,
            "administrative_area_level_1": administrative_area_level_1,
            "city": city,
        }
        print(json.dumps(place_data, indent=4, ensure_ascii=False))
        print("=" * 80)

        # Store the data
        all_place_details.append(place_data)

    # Define the headers for the CSV
    headers = list(all_place_details[0].keys())

    # Define the CSV file name
    csv_filename = f"{search_query}_place_details.csv"

    # Write collected data to CSV
    if all_place_details:  # Ensure there is data to write
        with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=headers)
            
            # Write the header
            writer.writeheader()
            
            # Write all rows
            writer.writerows(all_place_details)
        
        # Confirmation message
        print(f"Data has been saved to {csv_filename}")
    else:
        print("No place details found to save.")

else:
    print("No places found.")
