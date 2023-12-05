import openai
import json

openai.api_key = "ebe64320148849aead404cc3aec9cc49"

def get_similar_elements(l1, l2):
    # Use OpenAI's fuzzy logic to find similar elements
    similarity_results = {} 
    for item1 in l1:
        for item2 in l2:
            similarity_score = openai.Completion.create(
                engine="text-davinci-003",
                prompt=f"Find similarity between '{item1}' and '{item2}'",
                max_tokens=50
            )
            similarity_results[f"{item1} - {item2}"] = similarity_score.choices[0].text.strip()

    return similarity_results

# Get input for two lists
l1 = input("Enter elements of list 1 separated by comma: ").split(',')
l2 = input("Enter elements of list 2 separated by comma: ").split(',')

# Find similar elements
similar_elements = get_similar_elements(l1, l2)

# Output the results in JSON format
output_json = json.dumps(similar_elements, indent=4)
print(output_json)