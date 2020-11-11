import logging
import sys

LEVEL = 20

for arg in sys.argv:
    if arg == '--debug':
        LEVEL = 10

# create logger
log = logging.getLogger('chimera')
log.setLevel(LEVEL)

# handler
handler = logging.FileHandler('chimera.log', encoding='UTF-8')
handler.setLevel(LEVEL)

# create formater
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', '%Y-%m-%d %H:%M:%S')

# add formater to handler
handler.setFormatter(formatter)

# add handler to logger
log.addHandler(handler)

# test messages
# log.debug('debug message')
# log.info('info message')
# log.warning('warn message')
# log.error('error message')
# log.critical('critical message')