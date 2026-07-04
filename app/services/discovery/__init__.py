"""Job discovery connectors."""

from app.services.discovery.adzuna import AdzunaConnector
from app.services.discovery.greenhouse import GreenhouseConnector
from app.services.discovery.indeed import IndeedConnector
from app.services.discovery.lever import LeverConnector
from app.services.discovery.linkedin import LinkedInConnector
from app.services.discovery.remotive import RemotiveConnector
from app.services.discovery.rss_connector import RssConnector

CONNECTOR_MAP = {
    'greenhouse': GreenhouseConnector,
    'lever': LeverConnector,
    'adzuna': AdzunaConnector,
    'remotive': RemotiveConnector,
    'rss': RssConnector,
    'linkedin': LinkedInConnector,
    'indeed': IndeedConnector,
}


def get_connectors(source_names):
    connectors = []
    for name in source_names or []:
        cls = CONNECTOR_MAP.get(name)
        if cls:
            connectors.append(cls())
    return connectors
