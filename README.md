# Forecast Postprocessing Script

## Overview

This Python script automates the postprocessing of weather forecast data for Belgium, allowing you to download the latest GRIB files and generate summary plots for temperature, humidity, and wind at specific city locations. The script also applies a Bayesian method to improve the accuracy of the forecasts by combining recent simulation outputs with historical data, producing refined and probabilistically informed predictions.

---

## Features

✅ **Command-line interface with two straightforward options:**

- `download`: downloads the latest weather forecast data
- `get_forecast`: processes and visualizes the most recent forecast for a specific city in Belgium


✅ Generates a **2×2 multi-panel plot** for any supported Belgian city, showing:  

- Temperature (°C)  
- Relative humidity (%)  
- Wind speed (m/s)  
- Wind direction (°)  

✅ Improved forecast by Bayesian method   

---

## Usage

Run the script using:

```bash
python blend_forecast.py -o download_forecast

python blend_forecast.py -o get_forecast -c <city>

```
Example:
```bash
python blend_forecast.py -o get_forecast -c antwerp
python blend_forecast.py -o get_forecast -c main_cities
