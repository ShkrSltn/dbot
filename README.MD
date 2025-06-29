# DigiBot Demo - Getting Started Guide

## Requirements

Before running the application, it is recommended to create a virtual environment:

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate
```

After activating the virtual environment, install all required dependencies:

```bash
pip install -r requirements.txt
```

## Running the Application on macOS

To run the Streamlit application via main.py, follow these steps:

```bash
# Navigate to the project directory
cd path/to/digibot-demo

# Run the application
streamlit run main.py
```

After launching, the application will be available in your browser at: http://localhost:8501

## Troubleshooting

If you encounter any issues:

- Make sure all dependencies are installed correctly
- Check console output for any error messages
- Verify that you're running the command from the project's root directory
- Ensure you have the correct Python environment activated

## Additional Information

The application uses Streamlit for the frontend and LangChain for NLP capabilities. The main entry point is main.py which initializes the Streamlit configuration and calls the run_app() function from app.py.

If you experience any problems with launching the application, check the console for error messages and ensure that all dependencies are installed correctly.

## Database Setup

This application uses PostgreSQL for data storage. Follow these steps to set up the database:

1. Install PostgreSQL on your system if not already installed.

2. Create a new PostgreSQL database:
   ```bash
   createdb digibot
   ```

3. Set up the database connection in your `.env` file:
   ```
   DATABASE_URL=postgresql://username:password@localhost:5432/digibot
   ```
   Replace `username` and `password` with your PostgreSQL credentials.

4. Initialize the database tables:
   ```bash
   python init_db.py
   ```

5. If you encounter any issues with database connections, check that:
   - PostgreSQL service is running
   - Your credentials are correct
   - The database exists
   - Your user has appropriate permissions
