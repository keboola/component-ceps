import logging
import warnings
from ceps import CepsClient, CepsClientException
from keboola.component.base import ComponentBase
from keboola.component.exceptions import UserException
import keboola.utils.date as dutils
from csv_tools import CachedOrthogonalDictWriter
import tempfile

KEY_DATE_FROM = 'date_from'
KEY_DATE_TO = 'date_to'

KEY_ENDPOINTS = "endpoints"
KEY_ENDPOINT_NAME = "endpoint_name"
KEY_ENDPOINT_GRANULARITY = "granularity"
KEY_CONTINUE_ON_FAIL = "continue_on_fail"

# not implemented in UI, for case of further implementation
KEY_ENDPOINT_FUNCTION = "function"

REQUIRED_PARAMETERS = [KEY_DATE_FROM, KEY_DATE_TO]
REQUIRED_IMAGE_PARS = []

warnings.filterwarnings(
    "ignore",
    message="The localize method is no longer necessary, as this time zone supports the fold attribute",
)


class Component(ComponentBase):
    def __init__(self):
        super().__init__()
        self._writer_cache = dict()
        self.tables = []

    def run(self):
        self.validate_configuration_parameters(REQUIRED_PARAMETERS)
        self.validate_image_parameters(REQUIRED_IMAGE_PARS)
        params = self.configuration.parameters

        continue_on_fail = params.get(KEY_CONTINUE_ON_FAIL, True)

        intervals = self.get_date_intervals(params)

        endpoints_to_fetch = params.get(KEY_ENDPOINTS)

        client = CepsClient()

        for endpoint in endpoints_to_fetch:
            self.process_endpoint(endpoint, intervals, client, continue_on_fail)

        self._close_writers()
        self.write_manifests(self.tables)

    def process_endpoint(self, endpoint, intervals, client, continue_on_fail):
        endpoint_name = endpoint.get(KEY_ENDPOINT_NAME)
        logging.info(f"Fetching {endpoint_name} data")

        out_table = self.create_out_table_definition(f'{endpoint_name}.csv', incremental=True, enclosure="")
        out_table.primary_key = self.get_endpoint_p_keys(endpoint_name)

        self.tables.append(out_table)

        writer = self._get_writer_from_cache(out_table)
        for interval in intervals:
            self.process_interval(endpoint_name, interval, endpoint, client, writer, continue_on_fail)

    @staticmethod
    def get_endpoint_p_keys(endpoint_name):
        if endpoint_name in ["CrossborderPowerFlows", "Generation", "GenerationPlan", "GenerationPlan", "Load",
                             "RegulationEnergy", "RegulationEnergyB"]:
            return ["date"]
        elif endpoint_name in ["OdhadovanaCenaOdchylky", "OfferPrices"]:
            return ["hour", "date"]

    @staticmethod
    def process_interval(endpoint_name, interval, endpoint, client, writer, continue_on_fail):
        logging.info(
            f"Fetching {endpoint_name} data for interval {interval['start_date']} to {interval['end_date']}")
        try:
            result = client.get_data(endpoint.get(KEY_ENDPOINT_NAME),
                                     interval["start_date"],
                                     interval["end_date"],
                                     granularity=endpoint.get(KEY_ENDPOINT_GRANULARITY),
                                     function=endpoint.get(KEY_ENDPOINT_FUNCTION, "AVG"),
                                     version="RT")
            writer.writerows(result)
        except CepsClientException as ceps_exc:
            if continue_on_fail:
                logging.warning(ceps_exc)
            else:
                raise UserException(ceps_exc) from ceps_exc

    def _get_writer_from_cache(self, out_table):
        if not self._writer_cache.get(out_table.name):
            # init writer if not in cache
            self._writer_cache[out_table.name] = CachedOrthogonalDictWriter(out_table.full_path,
                                                                            out_table.primary_key.copy(),
                                                                            temp_directory=tempfile.mkdtemp())
            self._writer_cache[out_table.name].writeheader()

        return self._writer_cache[out_table.name]

    def _close_writers(self):
        for wr in self._writer_cache.values():
            wr.close()

    @staticmethod
    def get_date_intervals(params):
        try:
            start_date, end_date = dutils.parse_datetime_interval(params.get(KEY_DATE_FROM), params.get(KEY_DATE_TO))
        except TypeError:
            raise UserException("Failed to parse date to and from. Make sure the input is valid")
        intervals = dutils.split_dates_to_chunks(start_date, end_date, intv=30, strformat='%Y-%m-%d')
        return intervals


if __name__ == "__main__":
    try:
        comp = Component()
        # this triggers the run method by default and is controlled by the configuration.action parameter
        comp.execute_action()
    except UserException as exc:
        logging.exception(exc)
        exit(1)
    except Exception as exc:
        logging.exception(exc)
        exit(2)
