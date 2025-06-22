#!/bin/bash

# Set the application name as a variable for frontend
APP_NAME="dbot"

# Export the tag with the current date and time
export TAG=251225_$(date +%s)

# Function to handle failure and exit
handle_failure() {
    echo "Error occurred during $1. Exiting script."
    exit 1
}

# Ask user for build method
echo "Choose build method:"
echo "1) Local Docker build"
echo "2) Google Cloud Build"
read -p "Enter your choice (1 or 2): " BUILD_METHOD

if [ "$BUILD_METHOD" = "1" ]; then
    # Local Docker build with buildx
    echo "Building Docker image locally for $APP_NAME..."
    docker buildx build --no-cache --platform linux/amd64 -t $APP_NAME:$TAG --load . || handle_failure "Local Docker build"
    
    echo "Tagging Docker image..."
    docker tag $APP_NAME:$TAG gcr.io/digibot-streamlit-458413/$APP_NAME:$TAG || handle_failure "Docker tagging"
    
    echo "Pushing Docker image to Google Container Registry..."
    docker push gcr.io/digibot-streamlit-458413/$APP_NAME:$TAG || handle_failure "Docker push"
    
elif [ "$BUILD_METHOD" = "2" ]; then
    # Google Cloud Build
    echo "Building Docker image for $APP_NAME using Google Cloud Build..."
    gcloud builds submit --tag gcr.io/digibot-streamlit-458413/$APP_NAME:$TAG . || handle_failure "Google Cloud Build"
    
else
    echo "Invalid choice. Exiting."
    exit 1
fi

# Deploy to Google Cloud Run
echo "Deploying $APP_NAME to Google Cloud Run..."
gcloud run deploy $APP_NAME --image gcr.io/digibot-streamlit-458413/$APP_NAME:$TAG --platform managed --region europe-west6 --allow-unauthenticated --revision-suffix=$(date +%s) || handle_failure "Google Cloud Run deployment"

echo "$APP_NAME deployment completed successfully."