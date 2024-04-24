FROM python:3.10-slim

# Set the working directory to /app
WORKDIR /app

COPY requirements.txt /app/requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install Flask
#RUN pip install flask

COPY config.yaml /config/config.yaml

# Make port 5000 available to the world outside this container
EXPOSE 8000

# Define environment variable
#ENV CONFIG_FILE_PATH=/app/config.yaml

# Copy the contents of the local directory into the container at /app
COPY . /app 

# Run your FastAPI application
CMD ["uvicorn", "policy_mapping:app", "--host", "0.0.0.0", "--port", "5000"]