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

        self.MAIN_DOMAIN = 'en.softonic.com'
        self.MAIN_URL = 'https://en.softonic.com/windows/action'

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

                        if response.status_code == 200: break
                        if response.status_code == 500: break
                        if response.status_code == 403: break

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

    def __fetch_categories(self, url: str) -> List[str]:
        response: Response = self.__retry(url=url, action='get')

        ...

    def main(self):
        self.__fetch_categories(url=self.MAIN_URL)

        ...