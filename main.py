import os

from time import perf_counter
from src import Softonic
from src import logger

if __name__ == '__main__':
    if not os.path.exists('data'): os.mkdir('data')
    start = perf_counter()

    logger.info(f'scraping start..')

    sof = Softonic()
    sof.main()

    logger.info(f'scraping complete')
    logger.info(f'time to scraping: {perf_counter() - start}')


    