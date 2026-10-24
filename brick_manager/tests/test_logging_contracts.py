"""Regression contracts for CLI-safe application logging."""

import logging
from logging.handlers import RotatingFileHandler

from app import configure_logging
from flask import Flask
from flask.logging import default_handler


def test_logging_configuration_does_not_modify_root_stream_handlers(tmp_path):
    application = Flask("logging-contract")
    application.config["LOG_FOLDER"] = str(tmp_path)
    root_handlers = tuple(logging.getLogger().handlers)

    configure_logging(application)

    assert tuple(logging.getLogger().handlers) == root_handlers
    assert application.logger.propagate is False
    assert default_handler in application.logger.handlers
    file_handlers = [
        handler
        for handler in application.logger.handlers
        if isinstance(handler, RotatingFileHandler)
    ]
    assert len(file_handlers) == 1
    assert file_handlers[0].baseFilename == str(tmp_path / "brick_manager.log")
    for handler in file_handlers:
        handler.close()


def test_logging_configuration_is_idempotent(tmp_path):
    application = Flask("logging-idempotency")
    application.config["LOG_FOLDER"] = str(tmp_path)

    configure_logging(application)
    configure_logging(application)

    file_handlers = [
        handler
        for handler in application.logger.handlers
        if isinstance(handler, RotatingFileHandler)
    ]
    assert len(file_handlers) == 1
    application.logger.debug("logging remains usable")
    for handler in file_handlers:
        handler.close()
