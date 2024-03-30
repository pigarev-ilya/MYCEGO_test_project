import logging

logging.basicConfig(filename='logger/log.log', level=logging.INFO, format='%(asctime)s-%(name)s-%(levelname)s-%(message)s')
logger = logging.getLogger(__name__)
stream = logging.StreamHandler()

logger.addHandler(stream)