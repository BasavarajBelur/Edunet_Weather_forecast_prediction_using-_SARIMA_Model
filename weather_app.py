import requests
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.stattools import adfuller
import numpy as np
import streamlit as st

def speak(message):
    st.text(message)

def log_text(message):
    with open('weather_logg.txt', 'a') as f:
        f.write(message + '\n')

def get_current_weather(city):
    api_key = '13d6f372052b76fdc44bd6057ffb9dfc'
    base_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    response = requests.get(base_url)
    data = response.json()
    if data["cod"] != "404":
        weather_desc = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        wind_speed = data["wind"]["speed"]
        pressure = data["main"]["pressure"]
        speak(f"The current temperature in {city} is {temp} degrees Celsius with {weather_desc}, \n humidity {humidity}%,\n wind speed {wind_speed} m/s,\n and wind pressure is {pressure} hPa.")
        log_text(f"Current weather in {city}: {temp}°C, {weather_desc}, {humidity}%, {wind_speed} m/s, {pressure} hPa")
    else:
        speak("City not found.")
        log_text("City not found.")

def fetch_weather_forecast(city):
    api_key = '13d6f372052b76fdc44bd6057ffb9dfc'
    base_url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric"
    response = requests.get(base_url)
    data = response.json()
    if data["cod"] != "404":
        return data
    else:
        return None

def prepare_forecast_data(data):
    forecast_data = []
    for entry in data['list']:
        forecast_data.append({
            'ds': entry['dt_txt'],
            'temp': entry['main']['temp'],
            'humidity': entry['main']['humidity'],
            'wind_speed': entry['wind']['speed'],
            'pressure': entry['main']['pressure'],
        })
    df = pd.DataFrame(forecast_data)
    df['ds'] = pd.to_datetime(df['ds'])
    df.set_index('ds', inplace=True)
    return df

def adf_test(series):
    """Perform ADF test to check for stationarity"""
    result = adfuller(series, autolag='AIC')
    speak(f'ADF Statistic: {result[0]}')
    speak(f'p-value: {result[1]}')
    for key, value in result[4].items():
        speak(f'Critical Values: {key}: {value}')

def difference_series(series):
    return series.diff().dropna()

def fit_arima_model(series, order=(1,1,1)):
    model = SARIMAX(series, order=order)
    model_fit = model.fit(disp=False)
    return model_fit

def predict_future_weather(model, steps=16):
    forecast = model.get_forecast(steps=steps)
    return forecast.predicted_mean, forecast.conf_int()

def plot_forecast(df, forecast_temp, conf_int_temp, forecast_humidity, conf_int_humidity, forecast_wind, conf_int_wind, forecast_pressure, conf_int_pressure, city):
    fig, axs = plt.subplots(4, figsize=(12,22))
    axs[0].plot(df.index, df['temp'], label='Observed Temperature')
    axs[0].plot(forecast_temp.index, forecast_temp, color='red', label='Forecasted Temperature')
    axs[0].fill_between(forecast_temp.index, conf_int_temp.iloc[:, 0], conf_int_temp.iloc[:, 1], color='pink', alpha=0.3)
    axs[0].set_xlabel('Date')
    axs[0].set_ylabel('Temperature (°C)')
    axs[0].set_title(f'Temperature Forecast for {city}')
    axs[0].legend()

    axs[1].plot(df.index, df['humidity'], label='Observed Humidity')
    axs[1].plot(forecast_humidity.index, forecast_humidity, color='blue', label='Forecasted Humidity')
    axs[1].fill_between(forecast_humidity.index, conf_int_humidity.iloc[:, 0], conf_int_humidity.iloc[:, 1], color='green', alpha=0.3)
    axs[1].set_xlabel('Date')
    axs[1].set_ylabel('Humidity (%)')
    axs[1].set_title(f'Humidity Forecast for {city}')
    axs[1].legend()

    axs[2].plot(df.index, df['wind_speed'], label='Observed Wind Speed')
    axs[2].plot(forecast_wind.index, forecast_wind, color='orange', label='Forecasted Wind Speed')
    axs[2].fill_between(forecast_wind.index, conf_int_wind.iloc[:, 0], conf_int_wind.iloc[:, 1], color='yellow', alpha=0.3)
    axs[2].set_ylabel('Wind Speed (m/s)')
    axs[2].set_title(f'Wind Speed Forecast for {city}')
    axs[2].legend()

    axs[3].plot(df.index, df['pressure'], label='Observed Pressure')
    axs[3].plot(forecast_pressure.index, forecast_pressure, color='purple', label='Forecasted Pressure')
    axs[3].fill_between(forecast_pressure.index, conf_int_pressure.iloc[:, 0], conf_int_pressure.iloc[:, 1], color='brown', alpha=0.3)
    axs[3].set_xlabel('Date')
    axs[3].set_ylabel('Pressure (hPa)')
    axs[3].set_title(f'Pressure Forecast for {city}')
    axs[3].legend()

    return fig

def get_weather_forecast(city, steps=5):
    data = fetch_weather_forecast(city)
    if data:
        df = prepare_forecast_data(data)
        speak(f"Weather forecast for {city}:")
        adf_test(df['temp'])
        df_diff = difference_series(df['temp'])
        adf_test(df_diff)
        model_temp = fit_arima_model(df['temp'])
        forecast_temp, conf_int_temp = predict_future_weather(model_temp, steps=steps)
        model_humidity = fit_arima_model(df['humidity'])
        forecast_humidity, conf_int_humidity = predict_future_weather(model_humidity, steps=steps)
        model_wind = fit_arima_model(df['wind_speed'])
        forecast_wind, conf_int_wind = predict_future_weather(model_wind, steps=steps)
        model_pressure = fit_arima_model(df['pressure'])
        forecast_pressure, conf_int_pressure = predict_future_weather(model_pressure, steps=steps)
        
        fig = plot_forecast(df, forecast_temp, conf_int_temp, forecast_humidity, conf_int_humidity, forecast_wind, conf_int_wind, forecast_pressure, conf_int_pressure, city)
        
        st.pyplot(fig)

        for date, temp in forecast_temp.items():
            speak(f"{date.date()}: {temp:.2f} °C")
        for date, humidity in forecast_humidity.items():
            speak(f"{date.date()}: {humidity:.2f} %")
        for date, wind in forecast_wind.items():
            speak(f"{date.date()}: {wind:.2f} m/s")
    else:
        speak("City not found.")
        log_text("City not found.")

# Streamlit UI
st.title("Weather Forecast App")

city = st.text_input("Enter city name:")

if st.button("Get Current Weather"):
    get_current_weather(city)

if st.button("Get Weather Forecast"):
    get_weather_forecast(city, steps=5)
