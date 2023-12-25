FROM python:3.10-slim

# Set the working directory to /app
WORKDIR /app

# Copy the contents of the local directory into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install Flask
RUN pip install flask

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV NAME World

# Run your FastAPI application
CMD ["uvicorn", "fetch_labels:app", "--host", "0.0.0.0", "--port", "5000"]
