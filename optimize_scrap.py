import os
import requests
import re
from bs4 import BeautifulSoup
import time
import streamlit as st
import pandas as pd

# Leer la API Key desde las variables de entorno
API_KEY = os.getenv("API_KEY")

# Función para realizar la búsqueda con SerpAPI
def search_google(query, api_key=API_KEY, num_results=100):
    search_url = "https://serpapi.com/search"
    params = {
        'q': query,
        'engine': 'google',
        'api_key': api_key,
        'num': num_results,
    }
    
    response = requests.get(search_url, params=params)
    
    if response.status_code != 200:
        print(f"Error en la búsqueda: {response.status_code}")
        return []
    
    results = response.json().get("organic_results", [])
    urls = [result["link"] for result in results]
    return urls

# Función para extraer correos electrónicos de una página web
def extract_emails_from_html(html):
    email_regex = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(email_regex, html)
    # Filtrar correos electrónicos que no sean válidos (por ejemplo, los que usan "@" para nombrar fotos)
    valid_emails = {email for email in emails if not email.endswith(('.jpg', '.jpeg', '.png', '.gif'))}
    return valid_emails

# Función para extraer el nombre del sitio web desde el título o el encabezado principal
def extract_site_name(html):
    soup = BeautifulSoup(html, "html.parser")
    title = soup.find('title')
    h1 = soup.find('h1')
    if title:
        return title.get_text().strip()
    elif h1:
        return h1.get_text().strip()
    return 'Desconocido'

# Función para obtener los emails y nombres de una lista de URLs
def get_emails_and_names_from_urls(urls):
    emails_found = []
    names_found = []
    
    for url in urls:
        try:
            print(f"Accediendo a {url}...")
            response = requests.get(url, timeout=10)
            time.sleep(0.5)  # Reducir el tiempo de espera
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                page_html = str(soup)
                emails = extract_emails_from_html(page_html)
                if emails:
                    emails_found.extend(emails)
                    # Añadir el nombre del sitio web a la lista de nombres
                    site_name = extract_site_name(page_html)
                    names_found.extend([site_name] * len(emails))
            else:
                print(f"No se pudo acceder a {url}. Status code: {response.status_code}")
        
        except Exception as e:
            print(f"Error al acceder a {url}: {e}")
        
    return names_found, emails_found

# Interfaz de Usuario con Streamlit
st.title("Web Scraping de Correos Electrónicos")
query = st.text_input("Consulta de Búsqueda")
num_results = st.number_input("Número de Resultados", min_value=1, max_value=100, value=10)

if st.button("Buscar"):
    if query:
        urls = search_google(query, API_KEY, num_results)
        names, emails = get_emails_and_names_from_urls(urls)
        if emails:
            df = pd.DataFrame({'Nombre': names, 'Email': emails})
            st.write(df)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Descargar correos electrónicos como CSV",
                data=csv,
                file_name='emails.csv',
                mime='text/csv',
            )
            st.success("Correos electrónicos listos para descargar.")
        else:
            st.warning("No se encontraron correos electrónicos.")
    else:
        st.warning("Por favor, ingresa una consulta de búsqueda.")
