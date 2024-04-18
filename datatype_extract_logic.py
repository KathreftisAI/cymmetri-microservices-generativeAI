from datetime import datetime
from dateutil.parser import parse
import json
 
def get_distinct_keys_and_datatypes(json_data):
    distinct_keys_datatypes = {}
 
    def explore_json(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key not in distinct_keys_datatypes:
                    distinct_keys_datatypes[key] = get_data_type(value)
                elif distinct_keys_datatypes[key] != get_data_type(value):
                    distinct_keys_datatypes[key] = 'Mixed'
                explore_json(value)
        elif isinstance(obj, list):
            for item in obj:
                explore_json(item)
 
    def get_data_type(value):
      if isinstance(value, str):
          try:
              # Try parsing the value as a date
              parse_result = parse(value)
              if parse_result.hour == 0 and parse_result.minute == 0 and parse_result.second == 0:
                  return 'date'  # Date if no time components
              else:
                  return 'datetime'  # Datetime if time components present
          except (ValueError, OverflowError):
              return 'string'  # Fallback to string if parsing as date/datetime fails
      else:
          return type(value).__name__
 
    explore_json(json_data)
    return distinct_keys_datatypes


# Test JSON data
json_data = {
  "users": [
    {
      "id": 2,
      "name": "Jane Smith",
      "age": 25,
      "email": "jane@example.com",
      "is_active": True,
      "profile_picture": "https://example.com/profile.jpg",
      "registration_date": "2022-01-15",
      "last_login": "2024-03-04T15:30:00",
      "address": {
        "street": "456 Elm St",
        "city": "Othertown",
        "state": "NY",
        "zipcode": "54321"
      },
      "interests": ["swimming", "cooking"],
      "ldap_datetime_custom": "20240305110000Z",
      "ldap_byte_array": "0x0A0B0C",
      "password": "securepassword",
      "successfactor_date": "2024-03-04T12:45:00+00:00",
      "custom": "Another custom data"
    },
    {
      "PersonId": 300000003107430,
      "PersonNumber": "0010188",
      "CorrespondenceLanguage": "null",
      "BloodType": "B+",
      "DateOfBirth": "1990-11-01",
      "DateOfDeath": "null",
      "CountryOfBirth": "null",
      "RegionOfBirth": "null",
      "TownOfBirth": "null",
      "ApplicantNumber": "null",
      "CreatedBy": "FUSION_APPS_HCM_ESS_LOADER_APPID",
      "CreationDate": "2020-01-10T11:02:11+00:00",
      "LastUpdatedBy": "Ali.Mehaboob",
      "LastUpdateDate": "2021-11-10T17:18:46.144+00:00",
    },
    {
      "businessPhones": [],
      "displayName": "cyrus",
      "givenName": "cyrus",
      "jobTitle": "Unemployed",
      "mail": "null",
      "mobilePhone": "7977280292",
      "officeLocation": "null",
      "preferredLanguage": "null",
      "surname": "gracias",
      "userPrincipalName": "cyrus@cymmetri.com",
      "id": "353db878-b8b6-4235-adfa-f8979d7eeeb2"
    },
  ]
}


parsed_json = json.loads(json.dumps(json_data))
distinct_keys_datatypes = get_distinct_keys_and_datatypes(parsed_json)
l1 = list(distinct_keys_datatypes.keys())
print("all the keys",l1)
for key, datatype in distinct_keys_datatypes.items():
    print(f"Key: {key}, Data Type: {datatype}")