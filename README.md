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
 - Endpoints (endpoints) - [REQ] Select list of endpoints and their granularity (MI, HR, QH, DY)




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
                "endpoint_name": "RegulationEnergy",
                "granularity": "MI"
            },
            {
                "endpoint_name": "RegulationEnergyB",
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