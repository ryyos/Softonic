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
from concurrent.futures import ThreadPoolExecutor, wait
from zlib import crc32

from src.utils.fileIO import File
from src.utils.logger import logger
from src.utils.Logs import Logs
from src.utils.parser import Parser
from src.utils.corrector import vname

class Softonic:
    def __init__(self) -> None:

        self.__file = File()
        self.__parser = Parser()
        self.__executor = ThreadPoolExecutor(max_workers=10)

        self.__datas: List[dict] = []
        self.__monitorings: List[dict] = []
        self.logs: List[dict] = []

        self.PIC = 'Rio Dwi Saputra'
        self.MAIN_PATH = 'data'
        self.platform = ''

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

        self.PLATFORMS = [
            "windows",
            "android",
            "mac",
            "iphone"
        ]

        self.RESPONSE_CODE = [200, 400, 404, 500]

        self.detail_reviews = []
        ...


    def __create_dir(self, raw_data: dict) -> str:
        try: os.makedirs(f'{self.MAIN_PATH}/data_raw/data_review_app/{raw_data["platform"]}/{raw_data["type"]}/{raw_data["categories"]}/{vname(raw_data["reviews_name"].lower())}/json/detail')
        except Exception: ...
        finally: return f'{self.MAIN_PATH}/data_raw/data_review_app/{raw_data["platform"]}/{raw_data["type"]}/{raw_data["categories"]}/{vname(raw_data["reviews_name"].lower())}/json'
        ...


    def __logging(self,
                total: int, 
                failed: int, 
                success: int,
                id_product: int,
                sub_source: str,
                id_review: int,
                status_runtime: str,
                status_conditions: str,
                type_error: str,
                message: str):

        uid_found = False
        MONITORING_DATA = 'logs/monitoring_gofood.json'
        MONITORING_LOG = 'logs/monitoring_logs.json'

        content = {
            "Crawlling_time": strftime('%Y-%m-%d %H:%M:%S'),
            "id_project": None,
            "project": "Data Intelligence",
            "sub_project": "data review",
            "source_name": "gofood.co.id",
            "sub_source_name": sub_source,
            "id_sub_source": id_product,
            "total_data": total,
            "total_success": success,
            "total_failed": failed,
            "status": status_conditions,
            "assign": "Rio"
        }

        monitoring = {
            "Crawlling_time": strftime('%Y-%m-%d %H:%M:%S'),
            "id_project": None,
            "project": "Data Intelligence",
            "sub_project": "data review",
            "source_name": "en.softonic.com",
            "sub_source_name": sub_source,
            "id_sub_source": id_product,
            "id_data": id_review,
            "process_name": "Crawling",
            "status": status_runtime,
            "type_error": type_error,
            "message": message,
            "assign": "Rio"
        }

        for index, data in enumerate(self.__datas):
            if id_product in data["id_sub_source"]:
                self.__datas[index]["total_data"] = total
                self.__datas[index]["total_success"] = success
                self.__datas[index]["total_failed"] = failed
                self.__datas[index]["status"] = status_conditions
                uid_found = True
                break

        if not uid_found:
            self.__datas.append(content)

        self.__monitorings.append(monitoring)
        Logs.write(MONITORING_DATA, self.__datas)
        Logs.write(MONITORING_LOG, self.__monitorings)


    def __retry(self, url: str, 
                retry_interval: int = 10) -> Response:

        while True:
            try:
                response = requests.get(url)

                logger.info(f'request to: {url}')
                logger.info(f'reponse: {response.status_code}')
                print()

                if response.status_code in self.RESPONSE_CODE: return response

                logger.warning(f'request to: {url}')
                logger.warning(f'reponse: {response.status_code}')
                print()
                
                sleep(retry_interval)
                retry_interval+=5
            
            except Exception as err: 
                logger.error(f'request to: {url}')
                logger.error(f'reponse: {err}')
                print()
                
                sleep(retry_interval)
                retry_interval+=5
                ...
        ...


    def __convert_path(self, path: str) -> str:
        
        path = path.split('/')
        path[1] = 'data_clean'
        return '/'.join(path)
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
        response = self.__retry(url=url_game)
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
            "version": PyQuery(headers.find('li[data-meta="version"]')[-1]).text().replace('V ', '') if headers.find('li[data-meta="version"]') else None,
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

        ... # Write only detail


        raw_game["reviews_name"] = detail_game["title"]
        ic(raw_game["reviews_name"])

        path_detail = f'{self.__create_dir(raw_game)}/detail/{vname(detail_game["title"])}.json'

        raw_game.update({
            "detail_applications": detail_game,
            "path_data_raw": path_detail,
            "path_data_clean": self.__convert_path(path_detail)
        })

        self.__file.write_json(path_detail, raw_game)
        ...

        ... # request to comments param

        response = self.__retry(url=f'{url_game}/comments')
        html = PyQuery(response.text)

        game_title = html.find('head > title:first-child')
        ...

        ... # extract disqus review

        response = self.__retry(url=self.__build_param_disqus(name_apk=game_title, url_apk=url_game))

        disqus_page = PyQuery(response.text)
        reviews_temp = json.loads(disqus_page.find('#disqus-threadData').text())

        all_reviews = []
        total_error = 0

        ic(len(reviews_temp["response"]["posts"]))

        for review in reviews_temp["response"]["posts"]:
            
            all_reviews.append(review)

        try:
            cursor = reviews_temp["cursor"]["next"]
            thread = reviews_temp["response"]["posts"][0]["thread"]

            while True:

                reviews = self.__retry(url=self.__param_second_cursor(
                    thread=thread,
                    cursor=cursor)).json()

                if not reviews["cursor"]["hasNext"]: break
                
                if response.status_code != 200:
                    total_error+=1
                    break

                cursor = reviews["cursor"]["next"]
                logger.info(f'cursor: {cursor}')


                for review in reviews["response"]:
                    all_reviews.append(review)

        except Exception as err:
            ...

        ic(len(all_reviews))

        temporarys = []
        for index, review in enumerate(all_reviews):
            
            ... # Logging
            self.__logging(id_product=crc32(vname(detail_game["title"]).encode('utf-8')),
                           id_review=review["id"],
                           status_conditions='on progress',
                           status_runtime='success',
                           total=len(all_reviews),
                           success=index,
                           failed=0,
                           sub_source=detail_game["title"],
                           message=None,
                           type_error=None)

            ...

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
                        "total_rating": PyQuery(html.find('div.rating-info')[0]).text(),
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
                    "content_reviews": PyQuery(review["raw_message"]).text(),
                    "reply_content_reviews": [],
                    "date_of_experience": review["createdAt"].replace('T', ' '),
                    "date_of_experience_epoch": self.__convert_time(review["createdAt"])
                }

                path = f'{self.__create_dir(raw_data=raw_game)}/{detail_review["id"]}.json'


                raw_game.update({
                    "detail_reviews": detail_review,
                    "detail_applications": detail_game,
                    "reviews_name": detail_game["title"],
                    "path_data_raw": path,
                    "path_data_clean": self.__convert_path(path),
                })

                self.__file.write_json(path=path, content=raw_game)

                


        if total_error:    
            message="failed request to api review"
            type_error="request failed"
            runtime = 'error'
        else:
            message = None
            runtime = 'success'
            type_error = None

        self.__logging(id_product=crc32(vname(detail_game["title"]).encode('utf-8')),
                        id_review=review["id"],
                        status_conditions=runtime,
                        status_runtime='error',
                        total=len(all_reviews),
                        success=len(all_reviews),
                        failed=total_error,
                        sub_source=detail_game["title"],
                        message=message,
                        type_error=type_error)
    

        for detail in temporarys:

            raw_game.update({
                "detail_reviews": detail,
                "detail_applications": detail_game,
                "reviews_name": detail_game["title"],
            })

            path = f'{self.__create_dir(raw_data=raw_game)}/{detail["id"]}.json'

            raw_game.update({
                "path_data_raw": path,
                "path_data_clean": self.__convert_path(path),
            })

            self.__file.write_json(path=path, content=raw_game)

        ic({
            "len all review": len(all_reviews),
            "len temp": len(temporarys),
            "find review": len(reviews_temp["response"]["posts"])
        })

        logger.info(f'application: {raw_game["url_game"]}')
        logger.info(f'category: {raw_game["categories"]}')
        logger.info(f'type: {raw_game["type"]}')
        logger.info(f'total review: {len(all_reviews)}')

        ...


    def __fetch_game(self, url: str):
        response = self.__retry(url=url)
        
        games = []
        page = 1
        while True:
            html = PyQuery(response.text)

            for game in html.find('a[data-meta="app"]'): games.append(PyQuery(game).attr('href'))

            response: Response = self.__retry(url=f'{url}/{page}')

            if page > 1 and response.history: break

            logger.info(f'page: {page}')
            logger.info(f'total application: {len(games)}')
            print()

            page+=1

            if response.status_code != 200: break
            if not html.find('a[data-meta="app"]'): break

            ...
        return games
        ...


    def __fetch_categories(self, url: str) -> List[str]:
        response: Response = self.__retry(url=url)
        html = PyQuery(response.text)

        ic(url)
    
        categories_urls = [PyQuery(categories).attr('href') for categories in html.find('#sidenav-menu a[class="menu-categories__link"]')]
        
        return categories_urls
        
    def __extract_game(self, url_game: str) -> None:
        ic(url_game)
        response = self.__retry(url=url_game["url"].replace('/comments', ''))

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
            "url_game": url_game["url"],
            "type": PyQuery(response.text).find('meta[property="rv-recat"]').attr('content').split(',')[0],
            "categories": PyQuery(response.text).find('meta[property="rv-recat"]').attr('content').split(',')[-1],
            "platform": url_game["platform"]
        }

        self.__extract_review(raw_game=results_header)

        ...

    def main(self):

        for platform in self.PLATFORMS:
            categories_urls = self.__fetch_categories(url=self.MAIN_URL+platform)

            for categories in categories_urls:

                for type in self.TYPES:
                    games = self.__fetch_game(url=f'{categories}:{type}')

                    task_executor = []
                    for index, game in enumerate(games):

                        ic(f'game: {game}')
                        ic(f'game to: {index}')

                        igredation = {
                            "platform": platform,
                            "url": game
                        }

                        ic(igredation)
                        
                        # self.__extract_game(game)
                        task_executor.append(self.__executor.submit(self.__extract_game, igredation))
                        ...
                    wait(task_executor)
                    ...
                ...
            ...
        ...
        self.__executor.shutdown(wait=True)
