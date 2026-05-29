Three-Day Surf Forecast Pipeline

A Python-based data application that fetches real-time, multi-model marine and weather data from the Stormglass.io API. Users can input a specific surf spot (City and State/Country) and timezone to generate structured surf reports.

Version 1.2 now automatically processes, flattens, and exports the multi-model forecast data into individual, clean CSV files for easy analysis.
Features

    Geocoding Capabilities: Dynamically converts user-inputted locations into exact Latitude/Longitude coordinates.

    Multi-Model Data Fetching: Pulls detailed wave, wind, and weather metrics from global meteorological models via the Stormglass API.

    Data Transformation: Flattens complex, nested JSON API payloads into structured data formats.

    Automated CSV Export: Generates standalone CSV files for each forecast model for seamless tracking.

Repository Structure

    surf.py: The production-ready Python script, optimized for standalone execution, scheduling, or pipeline integration.

    surf.ipynb: The interactive Jupyter Notebook scratchpad showcasing live execution history, data exploration, and step-by-step outputs.

    Sample Files: Pre-generated CSV outputs included to demonstrate the final structured data schema without requiring an API key.

Prerequisites and Setup

    Get an API Key: Sign up for a free account and retrieve an API key from Stormglass.io.

    Environment Configuration: Ensure you have Python installed along with the required libraries (such as requests and pandas).

User Inputs Required:

    Full City Name (e.g., Playa Hermosa)

    Full State or Country (e.g., Costa Rica or California)

    Timezone Preference (Eastern or Pacific time)
