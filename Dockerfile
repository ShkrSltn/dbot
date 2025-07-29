# Using official Python image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy dependencies file
COPY requirements.txt .

# Upgrade pip and install dependencies with trusted host flags
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt

# Copy all project files
COPY . .

# Open port for Google Cloud Run (uses PORT environment variable, default to 8080)
EXPOSE 8080

# Environment variables for Streamlit
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ENABLE_CORS=false

# Command to run the application
# Use PORT environment variable from Cloud Run (defaults to 8080)
CMD streamlit run src/main.py --server.port=${PORT:-8080} --server.address=0.0.0.0