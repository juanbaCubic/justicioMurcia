#!/usr/bin/env python

import copy
import logging as lg
from abc import ABC, abstractmethod
from datetime import date, timedelta, datetime
import typing as tp
from requests.exceptions import HTTPError
import requests
import sys
import os
import json
import typer
from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
import argparse

from bs4 import BeautifulSoup  # Importa BeautifulSoup

load_dotenv()

sys.path.append(os.getenv('BASE_PATH'))
sys.path.append(os.getenv('SLEEP_TIME'))


# Initialize logging
def initialize_logging():
    lg.basicConfig(level=lg.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


initialize_logging()


class BaseScrapper(ABC):
    def download_days(self, date_start: date, date_end: date) -> list:
        """Download all the documents between two dates (from date_start to date_end)"""
        logger = lg.getLogger(self.download_days.__name__)
        logger.info("Downloading content from day %s to %s", date_start, date_end)
        delta = timedelta(days=1)
        date_start_aux = copy.copy(date_start)
        while date_start_aux <= date_end:
            self.download_day(date_start_aux)
            date_start_aux += delta
        logger.info("Downloaded content from day %s to %s", date_start, date_end)

    @abstractmethod
    def download_day(self, day: date) -> list:
        """Download all the documents for a specific date."""
        pass

    @abstractmethod
    def download_document(self, url: str, day: date) -> str:
        """Download XML from url document."""
        pass


class BoletinScrapper(BaseScrapper):
    def __init__(self):
        # Setup Chrome options
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')  # Run headless if you do not need a GUI
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        # Initialize the WebDriver
        self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
        #self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

    def download_days(self, date_start: date, date_end: date) -> list:
        """Download all the documents between two dates"""
        logger = lg.getLogger(self.download_days.__name__)
        logger.info("Downloading content from day %s to %s", date_start, date_end)
        delta = timedelta(days=1)
        date_start_aux = copy.copy(date_start)
        file_routes = []
        while date_start_aux <= date_end:
            file_routes += self.download_day(date_start_aux)
            date_start_aux += delta
        logger.info("Downloaded from %s to %s", date_start, date_end)
        return file_routes

    def download_day(self, day: date) -> list:
        """Download all the documents for a specific date."""
        logger = lg.getLogger(self.download_day.__name__)
        logger.info("Downloading Boletin content for day %s", day)
        day_str = day.strftime("%d-%m-%Y")
        boletin_url = f"https://www.borm.es/#/home/sumario/{day_str}"

        try:
            self.driver.get(boletin_url)
            time.sleep(int(os.getenv('SLEEP_TIME')))  # Esperar 5 segundos
            logger.info("Waiting %s seconds before continuing...", os.getenv('SLEEP_TIME'))

            soup = BeautifulSoup(self.driver.page_source, 'html.parser')

            main_page_data = self.get_from_main_page(soup, boletin_url)

            documents = []
            type_index = 0
            for div in soup.find_all('div', class_='row ng-scope'):
                for a_tag in div.find_all('a', title='Ver anuncio'):
                    doc_url = 'https://www.borm.es/' + a_tag['href']
                    documents.append(self.download_document(doc_url, day, main_page_data, type_index))
                    type_index += 1
            return documents

        except HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
        #except IndentationException as err:
        #    logger.error(f"Other error occurred: {err}")
        return []

    def download_document(self, url: str, day: date, main_page_data: dict, type_index: int):
        """Download document for a specific date."""
        logger = lg.getLogger(self.download_document.__name__)
        logger.info("Scraping announcement: %s", url)

        try:
            self.driver.get(url)
            time.sleep(int(os.getenv('SLEEP_TIME')))

            soup = BeautifulSoup(self.driver.page_source, 'html.parser')

            # Extract metadata
            header_table_data = self.get_header_table_data(soup)

            doc_info = {
                "number": main_page_data['number'],
                "date": main_page_data['date'],
                "type": main_page_data['type'][type_index],
                "cve": header_table_data['Nº de Publicación:'] if 'Nº de Publicación:' in header_table_data else "",
                "section": header_table_data['Sección:'] if 'Sección:' in header_table_data else "",
                "authority": header_table_data['Anunciante:'] if 'Anunciante:' in header_table_data else "",
                "extract": self.get_extract(soup),
                "url": url
            }


            content = soup.find('div', {'class': 'cuerpoAnuncioHTML'})

            # Save JSON metadata
            date_path = day.strftime("%Y/%m/%d")
            doc_id = f"{main_page_data['number']}-{day.strftime('%d%m%Y')}-{header_table_data['Nº de Publicación:']}"
            file_path = os.path.join(os.getenv('DOCUMENT_PATH'), date_path, doc_id)
            os.makedirs(file_path, exist_ok=True)

            json_path = os.path.join(file_path, f"{doc_id}.json")
            with open(json_path, 'w', encoding='utf-8') as json_file:
                json.dump(doc_info, json_file, ensure_ascii=False, indent=4)

            # Save XML content
            xml_path = os.path.join(file_path, f"{doc_id}.xml")
            with open(xml_path, 'w', encoding='utf-8') as xml_file:
                xml_file.write(f"<texto>{content}</texto>")

            logger.info("Documents %s and %s downloaded and saved to %s", f"{doc_id}.json", f"{doc_id}.xml", file_path)
            return file_path

        except HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
        except Exception as err:
            logger.error(f"Other error occurred: {err}")
        return None

    def get_extract(self, soup):
        # Extract announcement text
        announcement_text = ""
        try:
            container_div = soup.find('div', class_='container-fluid cabecera02 ng-scope')
            if container_div:
                h1_tag = container_div.find('h1', class_='ng-binding')
                if h1_tag:
                    announcement_text = h1_tag.get_text(strip=True)
        except:
            pass
        return announcement_text

    def get_from_main_page(self, soup, url):

        # Extract type of document
        dict_info = {}
        array_info = []
        for anuDer_div in soup.find_all('div', class_='anuDer'):
            for p in anuDer_div.find_all('p'):
                i_tag = p.find('i', class_='ng-binding')
                if i_tag:
                    array_info.append(i_tag.get_text(strip=True))
        dict_info['type'] = array_info

        # Extract number of document
        dict_info['number'] = ""
        titular_div = soup.find('div', class_='titular')
        if titular_div:
            h1_tag = titular_div.find('h1', class_='ng-binding')
            if h1_tag:
                h1_text = h1_tag.get_text(strip=True)
                match = re.search(r'Nº\s(\d+),', h1_text)
                if match:
                    dict_info['number'] = match.group(1)

        # Extract date of document
        dict_info['date'] = ""
        date_pattern = r'(\d{2}-\d{2}-\d{4})'

        # Buscar la fecha en la URL
        match = re.search(date_pattern, url)
        if match:
            dict_info['date'] = match.group(1)
        else:
            dict_info['date'] = ''

        return dict_info

    def get_header_table_data(self, soup):

        # Extract all <p> text with class 'dato2 ng-binding' and corresponding <h3> text with class 'dato1'
        info_dict = {}
        for div in soup.find_all('div', class_='col-md-5 col-sm-6 col-xs-12'):
            h3_tags = div.find_all('h3', class_='dato1')
            p_tags = div.find_all('p', class_='dato2 ng-binding')
            for h3_tag, p_tag in zip(h3_tags, p_tags):
                key = h3_tag.get_text(strip=True)
                value = p_tag.get_text(strip=True)
                info_dict[key] = value

        return info_dict


def main():
    parser = argparse.ArgumentParser(description="Scraper del Boletín Oficial de la Región de Murcia")
    parser.add_argument('date_start', type=str, help="Fecha de inicio en formato YYYY-MM-DD")
    parser.add_argument('date_end', type=str, nargs='?', help="Fecha de fin en formato YYYY-MM-DD (opcional)")

    args = parser.parse_args()

    boletin_scrapper = BoletinScrapper()

    if args.date_end:
        boletin_scrapper.download_days(
            date_start=datetime.strptime(args.date_start, "%Y-%m-%d").date(),
            date_end=datetime.strptime(args.date_end, "%Y-%m-%d").date(),
        )
    else:
        boletin_scrapper.download_day(
            date=datetime.strptime(args.date_start, "%Y-%m-%d").date()
        )


if __name__ == "__main__":
    main()