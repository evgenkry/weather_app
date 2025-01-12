import streamlit as st
import pandas as pd
import requests
import numpy as np
import matplotlib.pyplot as plt
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

# Функция для вычисления сезонной статистики (среднего и стандартного отклонения)
def calculate_seasonal_stats(df):
    seasonal_stats = df.groupby(['city', 'season'])['temperature'].agg(['mean', 'std']).reset_index()
    seasonal_stats = seasonal_stats.rename(columns={'mean': 'mean_temperature', 'std': 'std_temperature'})
    return seasonal_stats

# Функция для вычисления скользящего среднего
def calculate_rolling_mean(df, window=30):
    rolling_means = {}
    for city in df['city'].unique():
        city_data = df[df['city'] == city].sort_index()
        rolling_mean = city_data['temperature'].rolling(window=window, center=False).mean()
        rolling_means[city] = rolling_mean
    return rolling_means

# Заголовок приложения
st.title("Прогноз погоды и анализ исторических данных")

# Центрируем элементы с помощью CSS
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

# Контейнер для центрации
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
        
        # Добавляем столбцы для сезонной статистики
        seasonal_stats = calculate_seasonal_stats(data)
        data = pd.merge(data, seasonal_stats, on=['city', 'season'], how='left')

        # Вычисляем верхнюю и нижнюю границу для аномалий
        data['upper_bound'] = data['mean_temperature'] + 2 * data['std_temperature']
        data['lower_bound'] = data['mean_temperature'] - 2 * data['std_temperature']

        # Добавляем столбец для аномалий
        data['is_anomaly'] = (data['temperature'] < data['lower_bound']) | (data['temperature'] > data['upper_bound'])

        # Отображаем аномалии
        anomalies = city_data[city_data['is_anomaly'] == True]
        st.write("Аномалии для города:", anomalies)
        
        # Вычисление и отображение скользящего среднего
        rolling_means = calculate_rolling_mean(data)
        data['rolling_mean_30'] = np.nan
        for city, rm in rolling_means.items():
            data.loc[data['city'] == city, 'rolling_mean_30'] = rm

        # Вывод графика скользящего среднего
        plt.figure(figsize=(15, 8))
        for city in data['city'].unique():
            city_data = data[data['city'] == city].sort_values('timestamp')
            plt.plot(city_data['timestamp'], city_data['rolling_mean_30'], label=city, alpha=0.9)
            anomalies_data = city_data[city_data['is_anomaly'] == True]
            plt.scatter(anomalies_data['timestamp'], anomalies_data['temperature'], color='red', label=f'Аномалии в {city}')

        plt.xlabel('Дата', fontsize=12)
        plt.ylabel('Температура (°C)', fontsize=12)
        plt.title('Cкользящее среднее температуры по городам', fontsize=14)
        plt.legend(loc='upper right', fontsize=10)
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(plt)
        
        # Ввод API ключа
        st.sidebar.header("Введите API ключ OpenWeatherMap")
        api_key = st.sidebar.text_input("API ключ", type="password")
        
        # Получение текущей температуры и проверка на аномальность
        if api_key:
            temperature, error = get_current_temperature(selected_city, api_key)
            if error:
                st.error(error)
            else:
                st.write(f"Текущая температура в {selected_city}: {temperature} °C")
                
                # Определяем сезон и сравниваем с границами
                current_season = city_data['season'].iloc[0]  # Примерно для первого дня
                season_data = city_data[city_data['season'] == current_season]
                lower_bound = season_data['lower_bound'].iloc[0]
                upper_bound = season_data['upper_bound'].iloc[0]

                if lower_bound <= temperature <= upper_bound:
                    st.write(f"Температура нормальная для сезона {current_season}.")
                else:
                    st.write(f"Температура аномальная для сезона {current_season}.")
