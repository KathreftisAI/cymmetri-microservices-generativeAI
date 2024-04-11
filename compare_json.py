import json

def compare_json_structure(json1, json2):
  if type(json1) != type(json2):
    return False  # Different data types (dict vs list)

  if isinstance(json1, dict) and isinstance(json2, dict):
    return len(json1) == len(json2)  # Compare number of keys

  if isinstance(json1, list) and isinstance(json2, list):
    if len(json1) != len(json2):
      return False
    # Recursively compare elements in the list
    for item1, item2 in zip(json1, json2):
      if not compare_json_structure(item1, item2):
        return False
    return True

  return False  # Not dictionaries or lists

# Example usage
# json1 = {
#   "input": [
#     {
#       "_profiles_id": "",
#       "emails": "",
#       "firstname": "",
#       "name": "",
#       "password": "",
#       "password2": "",
#       "realname": ""
#     }
#   ]
# }

# json2 = {
#   "_profiles_id": "",
#   "emails": "${emails}",
#   "firstname": "${firstname}",
#   "name": "",
#   "password": "${password}",
#   "password2": "",
#   "realname": ""
# }

json1 = {
    "@odata.context": "https: //graph.microsoft.com/v1.0/$metadata#users/$entity",
    "businessPhones": [],
    "displayName": "${displayName}",
    "givenName": "${givenName}",
    "jobTitle": "Product Head",
    "mailNickname": "manojgulahe",
    "mobilePhone": "${mobilePhone}",
    "officeLocation": "${officeLocation}",
    "preferredLanguage": None,
    "surname": "${surname}",
    "userPrincipalName": "${userPrincipalName}",
    "passwordProfile": {
        "forceChangePasswordNextSignIn": False,
        "password": "${password}"
    },
    "accountEnabled": True
}

json2 = {
        "@odata.context":"https: //graph.microsoft.com/v1.0/$metadata#users/$entity",
        "businessPhones":[],
        "displayName":"ManojGulahe",
        "givenName":"Manoj",
        "jobTitle":"Product Head",
        "mailNickname":"manojgulahe",
        "mobilePhone":"9324418557",
        "officeLocation":"IDAM Project",
        "preferredLanguage":None,
        "surname":"Gulahe",
        "userPrincipalName":"manojgulahe@cymmetri.com",
        "passwordProfile":{
            "forceChangePasswordNextSignIn":False,
            "password":"xWwvJ]6NMw+bWH-d"},
        "accountEnabled":True}

# if compare_json_structure(json1, json2):
#   return True
#   print("JSON objects are same structure.")
# else:
#   return False
#   print("JSON objects are different structures.")

result = compare_json_structure(json1, json2)

print("result: ", result)
