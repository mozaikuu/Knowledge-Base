import requests
import json

def fetch_einstein_data():
    # Einstein's Wikidata ID
    einstein_id = "Q937"
    
    # Wikidata API endpoint
    api_url = f"https://www.wikidata.org/w/api.php"
    
    # Get basic entity data
    params = {
        "action": "wbgetentities",
        "ids": einstein_id,
        "format": "json",
        "languages": "en",
        "props": "labels|descriptions|claims"
    }
    
    response = requests.get(api_url, params=params)
    data = response.json()
    
    # Extract entity data
    entity = data["entities"][einstein_id]
    
    # Dictionary to store Einstein's information
    einstein_data = {
        "name": entity["labels"]["en"]["value"],
        "description": entity["descriptions"]["en"]["value"],
        "claims": {}
    }
    
    # Process claims
    for prop_id, claims in entity["claims"].items():
        # Get property label
        prop_params = {
            "action": "wbgetentities",
            "ids": prop_id,
            "format": "json",
            "languages": "en",
            "props": "labels"
        }
        
        prop_response = requests.get(api_url, params=prop_params)
        prop_data = prop_response.json()
        
        if "entities" in prop_data and prop_id in prop_data["entities"]:
            # Get property label, fallback to ID if no English label
            if "labels" in prop_data["entities"][prop_id] and "en" in prop_data["entities"][prop_id]["labels"]:
                property_label = prop_data["entities"][prop_id]["labels"]["en"]["value"]
            else:
                property_label = prop_id
                
            values = []
            
            for claim in claims:
                if "mainsnak" in claim and "datavalue" in claim["mainsnak"]:
                    value_data = claim["mainsnak"]["datavalue"]
                    
                    if value_data["type"] == "wikibase-entityid":
                        # If the value is another entity, get its label
                        entity_id = value_data["value"]["id"]
                        entity_params = {
                            "action": "wbgetentities",
                            "ids": entity_id,
                            "format": "json",
                            "languages": "en",
                            "props": "labels"
                        }
                        
                        entity_response = requests.get(api_url, params=entity_params)
                        entity_data = entity_response.json()
                        
                        if "entities" in entity_data and entity_id in entity_data["entities"]:
                            # Get entity label, fallback to ID if no English label
                            if "labels" in entity_data["entities"][entity_id] and "en" in entity_data["entities"][entity_id]["labels"]:
                                value = entity_data["entities"][entity_id]["labels"]["en"]["value"]
                            else:
                                value = entity_id
                        else:
                            value = entity_id
                    else:
                        # For other types of values
                        value = str(value_data["value"])
                    
                    values.append(value)
            
            if values:
                einstein_data["claims"][property_label] = values
    
    # Save to JSON file
    with open("einstein_knowledge_base.json", "w", encoding="utf-8") as f:
        json.dump(einstein_data, f, ensure_ascii=False, indent=2)
    
    return einstein_data

if __name__ == "__main__":
    print("Fetching Albert Einstein's data from Wikidata...")
    data = fetch_einstein_data()
    print(f"Successfully fetched data about {data['name']}")
    print(f"Description: {data['description']}")
    print(f"Number of properties: {len(data['claims'])}") 