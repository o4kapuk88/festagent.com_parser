import time

import requests
from bs4 import BeautifulSoup
import fake_useragent
import re
import pandas as pd
import logging

ua = fake_useragent.UserAgent().random
header = {'User-Agent': ua}
base_url = "https://festagent.com"
data = []

# Настройка логирования
logging.basicConfig(filename='scraping_log.txt', level=logging.INFO)


def send_request(url):
    try:
        with requests.Session() as session:
            response = session.get(url, headers=header, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return response
    except requests.RequestException as e:
        logging.error(f"Ошибка при запросе {url}: {e}")
        return None


def extract_festival_data(url):
    response = send_request(url)
    if response is None:
        return []

    soup = BeautifulSoup(response.text, 'lxml')
    title = soup.title.text if soup.title else "Заголовок не найден"
    country_element = soup.find('span', class_='country-icon')
    country = country_element.get('class')[1] if country_element else "Страна не найдена"

    email = "Email не найден"

    contacts_section = soup.find('div', class_='contacts')
    if contacts_section:
        email_match = re.search(r'[\w.-]+@[\w.-]+', contacts_section.get_text())
        if email_match:
            email = email_match.group()

    if email == "Email не найден":
        email_alt_section = soup.find('p', class_='festival-contact-emails')
        if email_alt_section:
            email_alt_match = re.search(r'[\w.-]+@[\w.-]+', email_alt_section.get_text())
            if email_alt_match:
                email = email_alt_match.group()

    official_website_element = soup.find('a', class_='website')
    official_website = official_website_element['href'] if official_website_element else "Официальный сайт не найден"

    return [title, country, email, official_website]


for page_number in range(1, 58):
    url = f'https://festagent.com/ru/festivals?page={page_number}'
    response = send_request(url)
    if response is None:
        continue

    soup = BeautifulSoup(response.text, 'lxml')
    links = soup.find_all('div', class_='title-link')

    for link in links:
        anchor = link.find('a')
        if anchor:
            url = anchor['href']
            full_url = base_url + url

            try:
                festival_data = extract_festival_data(full_url)
                if festival_data:
                    data.append(festival_data)
                    logging.info(f"Данные для {festival_data[0]} получены успешно")
            except Exception as e:
                logging.error(f"Ошибка при извлечении данных для {full_url}: {e}")
    time.sleep(10)

df = pd.DataFrame(data, columns=["Название", "Страна", "Email", "Официальный сайт"])

output_excel_file = "festivals_data.xlsx"
df.to_excel(output_excel_file, index=False, engine='openpyxl')

print("Данные записаны в Excel-таблицу:", output_excel_file)
