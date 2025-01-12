import streamlit as st
import pandas as pd
import requests

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

# Заголовок приложения
st.markdown("<h1 style='text-align: center;'>Прогноз погоды и анализ исторических данных</h1>", unsafe_allow_html=True)

# Центрирование всех элементов
col1, col2, col3 = st.columns([1, 3, 1])  # Центрируем контент в середине (col2)

with col2:
    # Загрузка файла с данными
    st.header("Загрузите файл с данными")
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
        
        # Ввод API ключа
        st.header("Введите API ключ OpenWeatherMap")
        api_key = st.text_input("API ключ", type="password")
        
        # Получение текущей температуры (если введен правильный ключ)
        if api_key:
            temperature, error = get_current_temperature(selected_city, api_key)
            if error:
                st.error(error)
            else:
                st.write(f"Текущая температура в {selected_city}: {temperature} °C")
