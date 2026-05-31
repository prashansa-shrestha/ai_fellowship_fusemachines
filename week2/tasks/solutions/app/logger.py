import logging
import sys

def get_logger(name:str)->logging.Logger:
    """
    Creates and returns a configured logger.
    'name' should be the module name (__name__) that shows where logs arae coming from
    """
    logger=logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        
        # logs in terminal
        console_handler=logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        # logs in file
        file_handler=logging.FileHandler("app.log")
        file_handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
    return logger
