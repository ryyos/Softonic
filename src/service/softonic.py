import os
import requests

from time import time, strftime, sleep
from pyquery import PyQuery
from requests import Response
from typing import List
from icecream import ic

from src.utils.fileIO import File
from src.utils.logs import logger
from src.utils.parser import Parser
from src.utils.corrector import vname

class Softonic:
    def __init__(self) -> None:

        self.__file = File()
        self.__parser = Parser()

        self.MAIN_DOMAIN = 'en.softonic.com'
        self.MAIN_URL = 'https://en.softonic.com/'

        self.TYPES = [
            "new-apps",
            "trending",
            "date",
            "last-news",
            "new-versions"
        ]

        ...

    def __retry(self, url: str, 
                action: str,
                retry_interval: int = 10) -> Response:
        
        match action:
            case 'get':

                while True:
                    try:
                        response = requests.get(url)
                        ic(response)

                        if response.status_code == 200: return response
                        if response.status_code == 500: return response
                        if response.status_code == 403: return response
                        if response.status_code == 404: return response

                        sleep(retry_interval)
                        retry_interval+=5
                    
                    except Exception as err: 
                        ic(err)
                        sleep(retry_interval)
                        retry_interval+=5
                        ...
                    ...
                
                ...

            case 'post':

                while True:
                    try:
                        response = requests.get(url)

                        if response.status_code == 200: break
                        if response.status_code == 500: break
                        if response.status_code == 403: break
                        if response.status_code == 404: break

                        sleep(retry_interval)
                        retry_interval+=5
                    
                    except Exception as err: 
                        ic(err)
                        sleep(retry_interval)
                        retry_interval+=5
                        ...
                    ...
                ...
        ...


    def __fetch_game(self, url: str):
        response = self.__retry(url=url, action='get')
        
        games = []
        page = 1
        while True:
            html = PyQuery(response.text)

            for game in html.find('a[data-meta="app"]'): games.append(PyQuery(game).attr('href'))

            response: Response = self.__retry(url=f'{url}/{page}', action='get')
            page+=1

            if response.status_code != 200: break
            if not html.find('a[data-meta="app"]'): break

            break

            ...
        ic(games)
        ...

    def __fetch_categories(self, url: str) -> List[str]:
        response: Response = self.__retry(url=url, action='get')
        html = PyQuery(response.text)
    
        categories_urls = [PyQuery(categories).attr('href') for categories in html.find('#sidenav-menu a[class="WNTOdu tEDxqA js-menu-categories-item"]')]
        
        return categories_urls
        

    def main(self):
        categories_urls = self.__fetch_categories(url=self.MAIN_URL)

        for categories in categories_urls:
            for type in self.TYPES:

                ic(categories)
                ic(type)
                self.__fetch_game(url=f'{categories}:{type}')

                break
                ...
            break
            ...

        ...


# data/data_raw/softonic_review/action/trending/name_app/file.json