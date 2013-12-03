# vim: ai ts=4 sts=4 et sw=4
# encoding=utf-8
import logging

logger = logging.getLogger(__name__)

def info(message, echo=False):
    if echo: print message
    logger.info(message)

def error(message):
	logger.error(message)

def exception(message=''):
	logger.exception(message)

def warn(message, echo=False):
    if echo: print message
    logger.warn(message)