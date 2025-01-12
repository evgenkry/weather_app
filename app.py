import streamlit as st
import pandas as pd
import numpy as np
import requests
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import matplotlib.dates as mdates

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
    if response.status_code != 200:
        return None, f"Error fetching weather data: Status code {response.status_code}"
    try:
        data = response.json()
        temperature = data['main']['temp'] if 'main' in data else None
        return temperature, None
    except (KeyError, ValueError):
        return None, "Error parsing weather data. Check city name or API response."


# Функция для вычисления сезонной статистики
def calculate_seasonal_stats(df, city):
    seasonal_stats = df[df['city'] == city].groupby(['season'])['temperature'].agg(['mean', 'std', 'min', 'max']).reset_index()
    seasonal_stats = seasonal_stats.rename(columns={'mean': 'mean_temperature', 'std': 'std_temperature',
                                                    'min': 'min_temperature', 'max': 'max_temperature'})
    seasonal_stats['upper_bound'] = seasonal_stats['mean_temperature'] + 2 * seasonal_stats['std_temperature']
    seasonal_stats['lower_bound'] = seasonal_stats['mean_temperature'] - 2 * seasonal_stats['std_temperature']
    return seasonal_stats

# Функция для вычисления годовой статистики
def calculate_yearly_stats(df):
    df['year'] = pd.to_datetime(df['timestamp']).dt.year
    yearly_stats = df.groupby(['city', 'year'])['temperature'].agg(['mean', 'std', 'min', 'max']).reset_index()
    yearly_stats = yearly_stats.rename(columns={'mean': 'mean_temperature', 'std': 'std_temperature',
                                                    'min': 'min_temperature', 'max': 'max_temperature'})
    return yearly_stats

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
        try:
            data = load_data(uploaded_file)
        except pd.errors.ParserError:
            st.error("Ошибка при чтении CSV файла. Убедитесь, что файл имеет правильный формат.")
            st.stop()
        except Exception as e:
            st.error(f"Произошла ошибка при загрузке файла: {e}")
            st.stop()


        # Получение списка уникальных городов
        cities = data['city'].unique()

        # Выбор города
        selected_city = st.selectbox("Выберите город", cities)

        # Отображение данных за выбранный город
        st.subheader(f"Данные для города {selected_city}")
        city_data = data[data['city'] == selected_city].copy()
        st.write(city_data)

        # Вычисляем сезонную статистику *ПОСЛЕ* фильтрации по городу
        seasonal_stats = calculate_seasonal_stats(data, selected_city)

        # Вычисление аномалий
        city_data = pd.merge(city_data, seasonal_stats, on=['season'], how='left')
        city_data['is_anomaly'] = (city_data['temperature'] < city_data['lower_bound']) | (city_data['temperature'] > city_data['upper_bound'])


        # Описательная статистика по сезонам
        st.subheader("Описательная статистика по сезонам")
        st.dataframe(seasonal_stats)

        # Описательная статистика по годам
        st.subheader("Описательная статистика по годам")
        yearly_stats = calculate_yearly_stats(data)
        yearly_data = yearly_stats[yearly_stats['city'] == selected_city]
        st.dataframe(yearly_data)

        # Построение временного ряда температур с выделением аномалий
        st.subheader(f"Временной ряд температур для города {selected_city}")

        fig, ax = plt.subplots(figsize=(10, 6))
        sns.lineplot(x='timestamp', y='temperature', data=city_data, ax=ax, label="Температура")
        anomalies = city_data[city_data['is_anomaly'] == True]
        ax.scatter(anomalies['timestamp'], anomalies['temperature'], color='red', label="Аномалии", zorder=5)

        plt.title(f"Температура для {selected_city}")

        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

        plt.xticks(rotation=45)
        plt.xlabel("Дата")
        plt.ylabel("Температура (°C)")
        plt.legend()
        plt.tight_layout()
        st.pyplot(fig)

        # Получение текущей температуры и проверка на аномальность
        api_key = st.text_input("Введите API ключ OpenWeatherMap", type="password")

        if st.button("Узнать текущую температуру"):  # Добавлена кнопка
            if api_key:
                with st.spinner("Запрос данных..."):  # Добавлен прелоадер
                    temperature, error = get_current_temperature(selected_city, api_key)

                    if error:
                        st.error(error)
                    elif temperature is not None:
                        st.write(f"Текущая температура в {selected_city}: {temperature} °C")

                        if not seasonal_stats.empty:
                            current_season_data = seasonal_stats[seasonal_stats['season'] == city_data['season'].iloc[0]]
                            if not current_season_data.empty:
                                lower_bound = current_season_data['lower_bound'].iloc[0]
                                upper_bound = current_season_data['upper_bound'].iloc[0]

                                if lower_bound <= temperature <= upper_bound:
                                    st.write(f"Текущая температура нормальна для сезона {city_data['season'].iloc[0]}.")
                                else:
                                    st.write(f"Текущая температура аномальна для сезона {city_data['season'].iloc[0]}.")
                            else:
                                st.write(f"Нет данных о сезонной статистике для {selected_city} в сезоне {city_data['season'].iloc[0]}. Проверка на аномальность невозможна.")
                        else:
                            st.write(f"Нет данных о сезонной статистике для {selected_city}. Проверка на аномальность невозможна.")
                    else:
                        st.write("Не удалось получить текущую температуру.")
