CEPS Extractor
=============

ČEPS, a.s. is a company providing operation of the electricity transmission system in the Czech Republic

This component enables you to extract publicly available data from the CEPS API.

**Table of contents:**

[TOC]

Configuration
=============

## CEPS data source Configuration

 - Date from (date_from) - [REQ] Date from which to start fetching data e.g. 3 days ago or exact date 2021-01-01
 - Date to (date_to) - [REQ] Date to which data fetching should be performed e.g. 3 days ago or exact date 2021-01-01
 - Endpoints (endpoints) - [REQ] Select list of endpoints and their granularity (MI, QH, HR, DY, WE, MO, YR, None)

## Endpoints

| Endpoint | Granularity | Primary key |
|---|---|---|
| AktivaceSVRvCR | MI, QH, HR, DY | date |
| AktualniCenaRE | None (1-minute data) | date |
| AktualniSystemovaOdchylkaCR | MI, QH, HR | date |
| CrossborderPowerFlows | MI, QH, HR, DY, WE, MO, YR | date |
| EmergencyExchange | QH, HR, DY | date, border_and_direction, type_of_exchange |
| Emise | QH | date |
| ExportImportSVR | MI, QH, HR, DY | date |
| Frekvence | None (1-minute data) | date |
| Generation | QH, HR, DY, WE, MO, YR | date |
| GenerationPlan | QH, HR, DY, WE, MO, YR | date |
| GenerationRES | MI, QH, HR, DY, WE, MO, YR | date |
| Load | MI, QH, HR, DY, WE, MO, YR | date |
| NepredvidatelneOdmitnuteNabidky | None | hour, date, unit |
| OdhadovanaCenaOdchylky | None | interval, date |
| OfferPrices | None | hour, date, unit |

Not every endpoint supports every granularity. The run checks the selected combinations against the table above before
downloading anything: with `continue_on_fail` off it fails, otherwise it logs a warning and skips the unsupported
endpoints. Endpoints listed with None ignore the granularity, so any value is accepted for them.

Each endpoint is written to one table named after the endpoint (e.g. `Load`), incrementally. The primary key does not
contain the granularity, so select each endpoint with one granularity per configuration. If you need several
granularities of one endpoint, use one configuration for each granularity. Otherwise rows with the same timestamp
overwrite each other.

Notes on the ČEPS API:
 - WE, MO and YR are fetched in a single request for the whole date range, so periods are not cut into partial aggregates.
   Endpoints that ignore the granularity are always fetched in 30-day chunks.
 - At WE, MO and YR, EmergencyExchange returns one row per event day dated at the start of the period, so the rows are
   not unique. Use DY and aggregate it yourself.
 - Emise always returns quarter-hour data, whatever granularity is selected.
 - At WE granularity the API returns the week of the March daylight-saving change several times with different values.

Upgrading from 0.1.x:
 - GenerationRES had no primary key, so an existing GenerationRES table may contain duplicate rows. Storage cannot
   create a primary key on a table with duplicates. The run still succeeds, but the job log shows "The new primary key
   cannot be created; duplicate values in primary key columns exist" and new rows keep being appended as duplicates.
   Delete the GenerationRES table (or remove the duplicates) once, then run the configuration again.
 - Versions 0.1.5 and 0.1.6 loaded the CSV header as a data row. Remove those rows with `granularity = 'granularity'`.




Sample Configuration
=============
```json
{
    "parameters": {
        "date_from": "2021-01-01",
        "date_to": "2021-05-01",
        "endpoints": [
            {
                "endpoint_name": "CrossborderPowerFlows",
                "granularity": "MI"
            },
            {
                "endpoint_name": "Generation",
                "granularity": "HR"
            },
            {
                "endpoint_name": "GenerationPlan",
                "granularity": "HR"
            },
            {
                "endpoint_name": "GenerationRES",
                "granularity": "MI"
            },
            {
                "endpoint_name": "Load",
                "granularity": "MI"
            },
            {
                "endpoint_name": "OdhadovanaCenaOdchylky",
                "granularity": "None"
            },
            {
                "endpoint_name": "OfferPrices",
                "granularity": "None"
            },
            {
                "endpoint_name": "AktualniSystemovaOdchylkaCR",
                "granularity": "MI"
            }
        ]
    },
    "action": "run"
}
```

Output
======

Each data is output as a single csv File as incremental.

Development
-----------

If required, change local data folder (the `CUSTOM_FOLDER` placeholder) path to your custom path in
the `docker-compose.yml` file:

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    volumes:
      - ./:/code
      - ./CUSTOM_FOLDER:/data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Clone this repository, init the workspace and run the component with following command:

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
docker-compose build
docker-compose run --rm dev
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Run the test suite and lint check using this command:

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
docker-compose run --rm test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Integration
===========

For information about deployment and integration with KBC, please refer to the
[deployment section of developers documentation](https://developers.keboola.com/extend/component/deployment/)
