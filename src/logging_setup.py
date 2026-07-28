import logging


def configure_logging():
    log_formatter_file = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    log_formatter_console = logging.Formatter('[%(levelname)s] %(message)s')

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    if not any(isinstance(handler, logging.FileHandler) for handler in root_logger.handlers):
        file_handler = logging.FileHandler("audit.log")
        file_handler.setFormatter(log_formatter_file)
        root_logger.addHandler(file_handler)

    if not any(isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler) for handler in root_logger.handlers):
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_formatter_console)
        root_logger.addHandler(console_handler)
