import logging

def setupLogger(debug = False):
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format='%(levelname)s: %(message)s'
    )
