import logging


logger = logging.getLogger()
l_handler = logging.StreamHandler()
l_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s]: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
l_handler.setLevel(logging.DEBUG)
logger.addHandler(l_handler)
logger.setLevel(logging.INFO)
