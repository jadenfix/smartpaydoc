#!/bin/bash

# Exit on error
set -e

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Google Cloud SDK is not installed. Please install it first:"
    echo "https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if user is logged in
echo "Checking Google Cloud login status..."
if ! gcloud auth list --filter=status:ACTIVE --format='value(account)' | grep -q '@'; then
    echo "Please log in to Google Cloud..."
    gcloud auth login
fi

# Set project
read -p "Enter your GCP Project ID: " PROJECT_ID
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "Enabling required Google Cloud APIs..."
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com

# Set the region
REGION="us-central1"

# Build and deploy
echo "Building and deploying to Cloud Run..."
gcloud builds submit \
    --config=cloudbuild.yaml \
    --substitutions=_ANTHROPIC_API_KEY=$(gcloud secrets versions access latest --secret=ANTHROPIC_API_KEY --project=$PROJECT_ID || echo "Please set up your ANTHROPIC_API_KEY as a secret first") \
    --project=$PROJECT_ID

echo "Deployment complete! Your application should be available shortly."
