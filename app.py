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
        
        # Ввод API ключа
        api_key = st.text_input("Введите API ключ OpenWeatherMap", type="password")
        
        # Получение текущей температуры (если введен правильный ключ)
        if api_key:
            temperature, error = get_current_temperature(selected_city, api_key)
            if error:
                st.error(error)
            else:
                st.write(f"Текущая температура в {selected_city}: {temperature} °C")
