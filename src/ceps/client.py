import logging.config
from typing import List

from zeep.wsdl.utils import etree_to_string
import xmltodict

import zeep
from requests import Session
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from zeep.transports import Transport

from keboola.utils.header_normalizer import DefaultHeaderNormalizer

WSDL_URL = 'https://www.ceps.cz/_layouts/CepsData.asmx?wsdl'

MAX_RETRIES = 10

# Custom column name mappings to override header normalizer output
# The header normalizer drops diacritics incorrectly (e.g., 'í' -> '' instead of 'i')
COLUMN_NAME_OVERRIDES = {
    "aktuln_odchylka_mw": "aktualni_odchylka_mw"
}


class CepsClientException(Exception):
    pass


class CepsClient:

    def __init__(self, debug=False, max_retries=MAX_RETRIES, backoff_factor=0.3):
        self._set_logger(debug)
        session = Session()
        retry = Retry(
            total=max_retries,
            read=max_retries,
            connect=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=(500, 501, 502, 503, 504),
            method_whitelist=('GET', 'POST', 'PATCH', 'UPDATE')
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        transport = Transport(session=session)
        self.client = zeep.Client(WSDL_URL, transport=transport)

    def _set_logger(self, debug):
        if debug:
            log_level = "DEBUG"
        else:
            log_level = "INFO"

        logging.config.dictConfig({
            'version': 1,
            'formatters': {
                'verbose': {
                    'format': '%(name)s: %(message)s'
                }
            },
            'handlers': {
                'console': {
                    'level': log_level,
                    'class': 'logging.StreamHandler',
                    'formatter': 'verbose',
                },
            },
            'loggers': {
                'zeep.transports': {
                    'level': log_level,
                    'propagate': True,
                    'handlers': ['console'],
                },
            }
        })

    def get_data(self, endpoint, date_start, date_end, granularity="HR", function="AVG", version="RT"):
        if endpoint == "DataVersion":
            return self.get_data_version(endpoint)
        elif endpoint in ["RegulationEnergy", "RegulationEnergyB"]:
            return self.get_timeseries_data(endpoint, date_start, date_end, granularity=granularity, function=function,
                                            version=version, add_para1=False)
        elif endpoint in ["NepredvidatelneOdmitnuteNabidky", "OdhadovanaCenaOdchylky", "OfferPrices"]:
            return self.get_timeseries_data(endpoint, date_start, date_end, add_para1=False)

        elif endpoint in ["AktualniSystemovaOdchylkaCR"]:
            return self.get_timeseries_data(endpoint, date_start, date_end, granularity=granularity, function=function,
                                            add_para1=False)

        elif endpoint in ["CrossborderPowerFlows", "GenerationPlan", "Load"]:
            return self.get_timeseries_data(endpoint, date_start, date_end, granularity=granularity, function=function,
                                            version=version, add_para1=False)
        else:
            return self.get_timeseries_data(endpoint, date_start, date_end, granularity=granularity, function=function,
                                            version=version)

    def get_timeseries_data(self, endpoint, date_start, date_end, granularity=None, function=None, version=None,
                            add_para1=True):
        request_data = {
            "dateFrom": date_start,
            "dateTo": date_end
        }
        if add_para1:
            request_data["para1"] = "all"
        if version:
            request_data["version"] = version
        if function:
            request_data["function"] = function
        if granularity:
            request_data["agregation"] = granularity

        method_to_call = getattr(self.client.service, endpoint)
        try:
            response = method_to_call(**request_data)
        except TypeError as type_error:
            raise CepsClientException(
                f"Invalid request for {endpoint} with request {request_data}. {type_error}") from type_error
        xml = etree_to_string(response).decode()
        response_data = xmltodict.parse(xml)
        try:
            data = response_data.get("root").get("data").get("item")
            field_names = response_data.get("root").get("series").get("serie")
            add_date = True
            if endpoint == "OfferPrices":
                add_date = False
            data = self.replace_fieldnames(data, field_names, add_date)
            data = self.add_granularity(granularity, data)
            if endpoint == "OdhadovanaCenaOdchylky":
                data = self.add_index(data)
        except AttributeError as att_exc:
            raise CepsClientException(
                f"No data returned for {endpoint} with request {request_data}. "
                f"Try a different aggregation period") from att_exc

        return data

    def get_data_version(self, endpoint):
        method_to_call = getattr(self.client.service, endpoint)
        response = method_to_call()
        xml = etree_to_string(response).decode()
        response_data = xmltodict.parse(xml)
        return response_data

    def replace_fieldnames(self, data, field_names, add_date):
        field_names_dict = self.process_fieldnames(field_names, add_date)
        for i, datum in enumerate(data):
            for field_name in field_names_dict:
                if field_name in data[i]:
                    data[i][field_names_dict[field_name]] = data[i].pop(field_name)
        return data

    @staticmethod
    def process_fieldnames(field_names, add_date):
        field_names_dict = {}
        header_normalizer = DefaultHeaderNormalizer()
        if not isinstance(field_names, List):
            field_names = [field_names]
        if add_date:
            field_names_dict["@date"] = "date"
        for field_name in field_names:
            normalized_name = header_normalizer._normalize_column_name(field_name["@name"]).lower()
            # Apply custom column name overrides if defined
            normalized_name = COLUMN_NAME_OVERRIDES.get(normalized_name, normalized_name)
            field_names_dict["@" + field_name["@id"]] = normalized_name
        return field_names_dict

    @staticmethod
    def add_granularity(granularity, data):
        for i, d in enumerate(data):
            data[i]["granularity"] = granularity
        return data

    def add_index(self, data):
        for i, d in enumerate(data):
            data[i]["ordered_index"] = i
        return data
