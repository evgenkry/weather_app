import streamlit as st
import pandas as pd
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
    seasonal_stats = df.groupby(['city', 'season'])['temperature'].agg(['mean', 'std']).reset_index()
    seasonal_stats = seasonal_stats.rename(columns={'mean': 'mean_temperature', 'std': 'std_temperature'})
    return seasonal_stats

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
        
        # Описательная статистика для исторических данных города
        st.subheader("Описательная статистика по температуре")
        st.write(city_data['temperature'].describe())

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

        # Ввод API ключа
        api_key = st.text_input("Введите API ключ OpenWeatherMap", type="password")
        
        # Получение текущей температуры (если введен правильный ключ)
        if api_key:
            temperature, error = get_current_temperature(selected_city, api_key)
            if error:
                st.error(error)
            else:
                st.write(f"Текущая температура в {selected_city}: {temperature} °C")

