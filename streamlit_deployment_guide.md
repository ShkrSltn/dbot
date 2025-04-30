# Deployment Guide for Streamlit Cloud

## Prerequisites

Before you deploy your application to Streamlit Cloud, make sure you have:

1. A GitHub account
2. Your project code pushed to a GitHub repository
3. A Streamlit account (sign up at https://streamlit.io/cloud)

## Deployment Steps

### 1. Push Your Code to GitHub

If you haven't already, push your code to a GitHub repository:

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/your-username/your-repo-name.git
git push -u origin main
```

### 2. Set Up Secrets in Streamlit Cloud

When deploying to Streamlit Cloud, you'll need to configure your secrets:

1. Log in to Streamlit Cloud
2. Click "New app"
3. Connect to your GitHub repository
4. Under "Advanced Settings", navigate to the "Secrets" section
5. Add all the secrets from your `.streamlit/secrets.toml` file:
   - DATABASE_URL
   - OPENAI_API_KEY
   - Any other environment variables your app needs

### 3. Configure the App Settings

1. Set the "Main file path" to `main.py`
2. Choose the Python version that matches your local development environment
3. If you need specific packages not in your requirements.txt, you can add them

### 4. Deploy the App

Click "Deploy" and wait for Streamlit Cloud to build and deploy your application.

### 5. Database Considerations

For the PostgreSQL database:

1. Make sure your database is accessible from Streamlit Cloud (consider using a cloud database service)
2. Update the DATABASE_URL in your Streamlit Cloud secrets to point to your production database
3. Make sure the database user has the necessary permissions

## Troubleshooting

If your app fails to deploy:

1. Check the deployment logs in Streamlit Cloud
2. Verify that all dependencies are correctly listed in requirements.txt
3. Make sure all environment variables are properly set in the Streamlit Cloud secrets
4. Check that your database is accessible from Streamlit Cloud

## Maintaining Your App

After deployment:

1. Monitor the app's performance and logs
2. For updates, simply push changes to your GitHub repository - Streamlit Cloud will automatically redeploy
3. If you change requirements, make sure to update requirements.txt
