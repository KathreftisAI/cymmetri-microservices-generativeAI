from fastapi import FastAPI, HTTPException
from typing import Dict, Any, List
from fuzzywuzzy import process
import uvicorn

app = FastAPI()

def map_field_to_policy(field: str, policy_mapping: List[Dict[str, Any]]) -> str:
    matched = False
    # Perform case-insensitive exact match
    for map_entry in policy_mapping:
        external_field = map_entry["external"]
        internal_field = map_entry["internal"]
        if external_field.lower() == field.lower():
            matched = True
            print(f"Exact match found: '{field}' -> '{external_field}'")
            return external_field, f"${{{external_field}}}"  # Use placeholder syntax
    
    # Perform fuzzy matching if no direct match is found
    # best_match, score = process.extractOne(field.lower(), [map_entry["internal"].lower() for map_entry in policy_mapping])
    # if score >= 70:  # Adjust the threshold as needed
    #     for map_entry in policy_mapping:
    #         if map_entry["internal"].lower() == best_match:
    #             matched = True
    #             print(f"Fuzzy match found: '{field}' -> '{map_entry['external']}' (Best match: '{best_match}')")
    #             return map_entry['external'], f"${{{map_entry['external']}}}"  # Use placeholder syntax
    
    if not matched:
        print(f"No match found for '{field}'")
    return field, None  # Return original field if no match is found


def map_nested_fields_to_policy(nested_field: Dict[str, Any], policy_mapping: List[Dict[str, Any]]) -> Dict[str, Any]:
    mapped_nested_data = {}
    for field, value in nested_field.items():
        if isinstance(value, dict):
            # Recursively map nested fields
            mapped_nested_data[field] = map_nested_fields_to_policy(value, policy_mapping)
        else:
            # Map non-nested fields
            mapped_field, placeholder = map_field_to_policy(field, policy_mapping)
            if placeholder is not None:
                mapped_nested_data[field] = placeholder
            else:
                mapped_nested_data[field] = value
    return mapped_nested_data


@app.post("/generativeaisrvc/map_fields_to_policy/")
async def map_fields_to_policy(payload: Dict[str, Any]):
    body = payload.get("body")
    policy_mapping = payload.get("policyMapping")

    if not body or not policy_mapping:
        raise HTTPException(status_code=400, detail="Body and policyMapping are required in the payload")

    mapped_data = {}

    for field, value in body.items():
        if isinstance(value, dict):
            # If the value is a dictionary (nested object), map its nested fields
            mapped_data[field] = map_nested_fields_to_policy(value, policy_mapping)
        else:
            # Map non-nested fields
            mapped_field, placeholder = map_field_to_policy(field, policy_mapping)
            if placeholder is not None:
                mapped_data[field] = placeholder
            else:
                mapped_data[field] = value

    return mapped_data

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
