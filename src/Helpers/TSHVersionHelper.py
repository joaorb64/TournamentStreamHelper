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

    return(feature in versions.get("beta_features"))