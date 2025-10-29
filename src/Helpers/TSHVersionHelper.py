from qtpy.QtGui import *
from qtpy.QtWidgets import *
from qtpy.QtCore import *
from .TSHDirHelper import TSHResolve
import json
from loguru import logger

def get_beta_status(feature):
    try:
        versions = json.load(
            open(TSHResolve('./assets/versions.json'), encoding='utf-8'))
    except Exception as e:
        logger.error("Local version file not found")
        versions = {}

    return(feature in versions.get("beta_features", []))

def add_beta_label(text, feature):
    if get_beta_status(feature):
        beta_label = "[" + str(QApplication.translate("app", "beta")).upper() + "] "
        return(beta_label + text)
    else:
        return(text)
    
def get_supported_providers():
    try:
        versions = json.load(
            open(TSHResolve('./assets/versions.json'), encoding='utf-8'))
    except Exception as e:
        logger.error("Local version file not found")
        versions = {}
    
    return(versions.get("supported_providers", []))