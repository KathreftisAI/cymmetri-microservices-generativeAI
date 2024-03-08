import json

def extract_user_data(response):
    user_data = {}

    def is_user_data(obj):
        # Check if object contains common user data keys
        user_keys = {'displayName', 'givenName', 'mail', 'id'}
        return all(key in obj for key in user_keys)

    def traverse(obj):
        # Recursively traverse the JSON object
        nonlocal user_data
        if isinstance(obj, dict):
            if is_user_data(obj):
                user_data = obj
            else:
                for value in obj.values():
                    traverse(value)
        elif isinstance(obj, list):
            for item in obj:
                traverse(item)

    traverse(response)

    return user_data


# Example response data
response = {
    "@odata.context": "https://graph.microsoft.com/v1.0/$metadata#users",
    "value": [
        {
            "businessPhones": [],
            "displayName": "Aakanksha Raina",
            "givenName": "Aakanksha",
            "jobTitle": "Null",
            "mail": "aakanksha.raina@cymmetri.com",
            "mobilePhone": "null",
            "officeLocation": "null",
            "preferredLanguage": "null",
            "surname": "Raina",
            "userPrincipalName": "aakanksha.raina@cymmetri.com",
            "id": "c835ea75-707b-4e63-b4dc-b24b4b522a09"
        },
        {
            "businessPhones": [],
            "displayName": "Abhishek Ghante",
            "givenName": "Abhishek",
            "jobTitle": "null",
            "mail": "abhishek.ghante@cymmetri.com",
            "mobilePhone": "null",
            "officeLocation": "null",
            "preferredLanguage": "null",
            "surname": "Ghante",
            "userPrincipalName": "abhishek.ghante@cymmetri.com",
            "id": "c39d5cf7-2d6c-4281-b58b-451125761c3d"
        }
    ]
}

#json_data = response.json()

# Parse the user data from the response
user_data = extract_user_data(response)

# Print the extracted user data
print(type(user_data))
print(user_data)
