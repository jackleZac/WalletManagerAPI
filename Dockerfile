# Use an official Python runtime as parent image
FROM python:3.9

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements into the container
COPY requirements.txt .

# Install all the required packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application into the container
COPY . .

# Specify the command to run the Flask app
CMD ["python3", "app.py"]


