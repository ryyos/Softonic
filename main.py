import os
from src import Softonic

if __name__ == '__main__':
    if not os.path.exists('data'): os.mkdir('data')
    sof = Softonic()
    sof.main()

    