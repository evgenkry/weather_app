import streamlit as st
import pandas as pd
import numpy as np
import requests
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Функция для загрузки и анализа CSV файла
def load_data(file):
    data = pd.read_csv(file)
    return data

# Функция для получения текущей температуры с помощью API OpenWeatherMap
def get_current_temperature(city, api_key):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&appid={api_key}"
    response = requests.get(url)
    if response.status_code == 401:
        return None, "Invalid API key. Please see https://openweathermap.org/faq#error401 for more info."
    data = response.json()
    temperature = data['main']['temp'] if 'main' in data else None
    return temperature, None

# Функция для вычисления сезонной статистики
def calculate_seasonal_stats(df):
    seasonal_stats = df.groupby(['city', 'season'])['temperature'].agg(['mean', 'std', 'min', 'max']).reset_index()
    seasonal_stats = seasonal_stats.rename(columns={'mean': 'mean_temperature', 'std': 'std_temperature', 
                                                     'min': 'min_temperature', 'max': 'max_temperature'})
    return seasonal_stats

# Функция для вычисления годовой статистики
def calculate_yearly_stats(df):
    df['year'] = pd.to_datetime(df['timestamp']).dt.year
    yearly_stats = df.groupby(['city', 'year'])['temperature'].agg(['mean', 'std', 'min', 'max']).reset_index()
    yearly_stats = yearly_stats.rename(columns={'mean': 'mean_temperature', 'std': 'std_temperature', 
                                                 'min': 'min_temperature', 'max': 'max_temperature'})
    return yearly_stats

# Функция для вычисления скользящего среднего
def calculate_rolling_mean(df, window=30):
    rolling_means = {}
    for city in df['city'].unique():
        city_data = df[df['city'] == city].sort_index()
        rolling_mean = city_data['temperature'].rolling(window=window, center=False).mean()
        rolling_means[city] = rolling_mean
    return rolling_means

# Добавляем немного CSS для выравнивания всех элементов по центру
st.markdown("""
    <style>
        .centered-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
        }
    </style>
""", unsafe_allow_html=True)

# Контейнер для центровки
with st.container():
    st.markdown("<h1 style='text-align: center;'>Прогноз погоды и анализ исторических данных</h1>", unsafe_allow_html=True)
    
    # Загрузка файла с данными
    uploaded_file = st.file_uploader("Выберите файл", type=["csv"])
    
    if uploaded_file:
        # Загрузка данных из CSV файла
        data = load_data(uploaded_file)
        
        # Получение списка уникальных городов
        cities = data['city'].unique()
        
        # Выбор города
        selected_city = st.selectbox("Выберите город", cities)
        
        # Отображение данных за выбранный город
        st.subheader(f"Данные для города {selected_city}")
        city_data = data[data['city'] == selected_city]
        st.write(city_data)
        
        # Описательная статистика по сезонам
        st.subheader("Описательная статистика по сезонам")
        seasonal_stats = calculate_seasonal_stats(data)
        seasonal_data = seasonal_stats[seasonal_stats['city'] == selected_city]
        st.dataframe(seasonal_data)

        # Описательная статистика по годам
        st.subheader("Описательная статистика по годам")
        yearly_stats = calculate_yearly_stats(data)
        yearly_data = yearly_stats[yearly_stats['city'] == selected_city]
        st.dataframe(yearly_data)

        # Вычисляем сезонную статистику
        seasonal_stats = calculate_seasonal_stats(data)
        data = pd.merge(data, seasonal_stats, on=['city', 'season'], how='left')

        # Вычисляем верхние и нижние границы для аномалий
        data['upper_bound'] = data['mean_temperature'] + 2 * data['std_temperature']
        data['lower_bound'] = data['mean_temperature'] - 2 * data['std_temperature']

        # Определяем аномалии
        data['is_anomaly'] = (data['temperature'] < data['lower_bound']) | (data['temperature'] > data['upper_bound'])

        # Построение временного ряда температур с выделением аномалий
        st.subheader(f"Временной ряд температур для города {selected_city}")
        
        # График
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.lineplot(x='timestamp', y='temperature', data=city_data, ax=ax, label="Температура")
        anomalies = city_data[city_data['is_anomaly'] == True]
        ax.scatter(anomalies['timestamp'], anomalies['temperature'], color='red', label="Аномалии", zorder=5)
        
        plt.title(f"Температура для {selected_city}")
        plt.xticks(rotation=45)
        plt.xlabel("Дата")
        plt.ylabel("Температура (°C)")
        plt.legend()
        st.pyplot(fig)

        # Получение текущей температуры (если введен правильный ключ)
        api_key = st.text_input("Введите API ключ OpenWeatherMap", type="password")
        
        # Получение текущей температуры (если введен правильный ключ)
        if api_key:
            temperature, error = get_current_temperature(selected_city, api_key)
            if error:
                st.error(error)
            else:
                st.write(f"Текущая температура в {selected_city}: {temperature} °C")
                
                # Проверка нормальности температуры
                current_season = city_data['season'].iloc[0]  # Предполагаем, что сезон одинаковый для всего города
                season_stats = seasonal_stats[(seasonal_stats['city'] == selected_city) & 
                                              (seasonal_stats['season'] == current_season)]
                lower_bound = season_stats['lower_bound'].iloc[0]
                upper_bound = season_stats['upper_bound'].iloc[0]
                
                if lower_bound <= temperature <= upper_bound:
                    st.write(f"Текущая температура нормальна для сезона {current_season}.")
                else:
                    st.write(f"Текущая температура аномальна для сезона {current_season}.")
