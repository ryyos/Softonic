import os
import requests
import json
import datetime as date

from time import time, strftime, sleep
from pyquery import PyQuery
from requests import Response
from typing import List
from icecream import ic
from requests_html import HTMLSession
from datetime import datetime, timezone

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
        self.API_REVIEW = 'https://disqus.com/api/3.0/threads/listPostsThreaded'
        self.API_KEY = 'E8Uh5l5fHZ6gD8U3KycjAIAk46f68Zw7C6eW8WSjZvCLXebZ7p0r1yrYDrLilk2F'
        self.DISQUS_API_COMMENT = 'https://disqus.com/embed/comments'

        self.TYPES = [
            "new-apps",
            "trending",
            "date",
            "last-news",
            "new-versions"
        ]

        self.detail_reviews = []
        ...

    def __retry(self, url: str, 
                action: str,
                retry_interval: int = 10) -> Response:
        
        match action:
            case 'get':

                while True:
                    try:
                        response = requests.get(url)
                        ic(url)
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

            case 'review':

                while True:
                    try:
                        response = requests.get(url)

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


    def __convert_time(self, times: str) -> int:
        dt = date.datetime.fromisoformat(times)
        dt = dt.replace(tzinfo=timezone.utc) 

        return int(dt.timestamp())
        ...


    def __param_second_cursor(self, cursor: str, thread: str) -> str:

        return f'https://disqus.com/api/3.0/threads/listPostsThreaded?limit=50&thread={thread}&forum=en-softonic-com&order=popular&cursor={cursor}&api_key={self.API_KEY}'
        ...


    def __build_param_disqus(self, url_apk: str, name_apk: str) -> str:
        return f'{self.DISQUS_API_COMMENT}/?base=default&f=en-softonic-com&t_u={url_apk}/comments&t_d={name_apk}&s_o=default#version=cb3f36bfade5c758ef967a494d077f95'
        ...


    def __extract_review(self, raw_game: str) -> None: # halaman game
        url_game = raw_game["url_game"]

        ... # mengambil Header baku
        response = self.__retry(url=url_game, action='get')
        headers = PyQuery(response.text)

        descriptions = headers.find('article.editor-review')

        descs = []
        for desc in descriptions.children():
            text = desc.text_content()

            if desc.tag == 'h2':

                content = {
                    "sub_title": text,
                    "sub_description": []
                }

                descs.append(content)
                
            elif desc.tag == 'p':
                descs[-1]["sub_description"].append(text)

        detail_game = {
            "title": headers.find('head > title').text().split(' - ')[0],
            "version": PyQuery(headers.find('li[data-meta="version"]')[0]).text().replace('V ', ''),
            "language": PyQuery(headers.find('ul[class="app-header__features"] > li[class="app-header__item"]')[1]).text(),
            "status": PyQuery(headers.find('ul[class="app-header__features"] > li[class="app-header__item"]')[0]).text(),
            "descriptions": descs,
            "related_topics": [PyQuery(relevant).text() for relevant in headers.find('ul.related-topics__list > li')],
        }

        for spec in headers.find('ul.app-specs__list > li'):
            detail_game.update(
                {
                    PyQuery(spec).find('h3').text(): PyQuery(spec).find('p').text()
                }
            )

        ... 

        ... # request to comments param

        response = self.__retry(url=f'{url_game}/comments', action='get')
        html = PyQuery(response.text)

        game_title = html.find('head > title:first-child')
        ...

        ... # extract disqus review

        response = self.__retry(url=self.__build_param_disqus(name_apk=game_title, url_apk=url_game), 
                                action='get')

        disqus_page = PyQuery(response.text)
        reviews = json.loads(disqus_page.find('#disqus-threadData').text())
        all_reviews = []
        while True:

            for review in reviews["response"]["posts"]:
                all_reviews.append(review)

            if not reviews["cursor"]["hasNext"]: break
            ic(reviews["cursor"]["hasNext"])
            reviews = self.__retry(url=self.__param_second_cursor(
                thread=reviews["response"]["posts"][0]["thread"],
                cursor=reviews["cursor"]["next"]))
            break

        ic(len(all_reviews))
        
        temporarys = []
        for review in all_reviews:
            ic(len(temporarys))

            if review["parent"]:
                for parent in temporarys:
                    if parent["id"] == review["parent"]:
                        parent["reply_content_reviews"].append({
                            "username_reply_reviews":  review["author"]["name"],
                            "content_reviews": review["raw_message"]
                        })
                        parent["total_reply_reviews"] +=1
            
            else:
                detail_review = {
                    "id": int(review["id"]),
                    "username_reviews": review["author"]["name"],
                    "image_reviews": 'https:'+review["author"]["avatar"]["permalink"],
                    "created_time": review["createdAt"].replace('T', ' '),
                    "created_time_epoch": self.__convert_time(review["createdAt"]),
                    "email_reviews": None,
                    "company_name": None,
                    "location_reviews": None,
                    "title_detail_reviews": None,

                    "total_reviews": len(all_reviews),
                    "reviews_rating": {
                        "total_rating": html.find('body > main > div:nth-child(2) > div > div > div > div:nth-child(2) > div.header-columns__main > div > div.s-media__body.app-header__body > ul:nth-child(3) > li.app-header__item.app-header__item--double > div > p').text(),
                        "detail_total_rating": None
                    },
                    "detail_reviews_rating": [
                        {
                        "score_rating": None,
                        "category_rating": None
                        }
                    ],
                    "total_likes_reviews": review["likes"],
                    "total_dislikes_reviews": review["dislikes"],
                    "total_reply_reviews": 0,
                    "content_reviews": review["raw_message"],
                    "reply_content_reviews": [],
                    "date_of_experience": review["createdAt"].replace('T', ' '),
                    "date_of_experience_epoch": self.__convert_time(review["createdAt"])
                }
                
                ic(detail_review["username_reviews"])

                temporarys.append(detail_review)

        for detail in temporarys:

            raw_game.update({
                "detail_reviews": detail,
                "detail_applications": detail_game,
                "reviews_name": detail_game["title"]
            })

            ic(detail["username_reviews"])
            self.__file.write_json(path=f'data/{detail["username_reviews"]}.json', content=raw_game)

        ...

# json.loads(disqus_page.find('#disqus-threadData').text())

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
        return games
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
                games = self.__fetch_game(url=f'{categories}:{type}')

                for game in games:

                    results_header = {
                        "link": self.MAIN_URL,
                        "domain": self.MAIN_DOMAIN,
                        "tags": [self.MAIN_DOMAIN],
                        "crawling_time": strftime('%Y-%m-%d %H:%M:%S'),
                        "crawling_time_epoch": int(time()),
                        "path_data_raw": "",
                        "path_data_clean": "",
                        "reviews_name": "name_game",
                        "location_reviews": None,
                        "category_reviews": "application",
                        "url_game": "https://minecraft.en.softonic.com",
                    }
                    self.__extract_review(raw_game=results_header)

                    break
                    ...

                break
                ...
            break
            ...

        ...


# data/data_raw/softonic_review/action/trending/name_app/file.json