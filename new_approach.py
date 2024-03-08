@app.post('/generativeaisrvc/get_policy_mapped')
async def get_mapped(data: dict):
    logging.debug(f"API call for auto policy mapping with the application")
    try:
        tenant = "generativeAI"
        input_collection = stored_input(tenant)
        output_collection = stored_response(tenant)

        # Store the received response directly into the input collection
        input_collection.insert_one(data)
        
        logging.debug("Input response saved successfully")
 
        # Extract necessary information directly from the received response
        json_data_ = extract_user_data(data)
        response_data = get_distinct_keys_and_datatypes(json_data_)

        l1 = [item['label'] for item in response_data]
 
        # Predefined list l2 remains unchanged
        
        threshold = 60
        result = compare_lists_with_fuzzy(l1, l2, threshold)

        final_response = generate_final_response(result['similar_elements'], response_data)
        final_response_dict = {"final_response": final_response}

        # Assuming 'appId' is present in the received response
        appId = data.get("appId")
        final_response_dict['appId'] = appId

        # Store the final response into the output collection
        output_collection.update_one(
            {"appId": appId},
            {"$set": final_response_dict},
            upsert=True
        )

        logging.debug("Final response saved successfully")

        return JSONResponse(content=final_response)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
