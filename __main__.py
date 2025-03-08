from optibook import *
from main.bot import Bot
from time import sleep
from main.algorithms import algos


if __name__ == '__main__':
    bot = Bot()
    for algo in algos:
        bot.algorithms.append(algo(bot))
    
    while True:
        sleep(5)
        bot.run_bot()