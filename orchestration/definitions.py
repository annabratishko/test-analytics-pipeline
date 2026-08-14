from dagster import asset, Definitions

from extract.extract_product_db import run as extract_product_db_run
from load.load_product_db import run as load_product_db_run

from extract.extract_stripe import run as extract_stripe_run
from load.load_stripe import run as load_stripe_run

from extract.extract_amplitude import run as extract_amplitude_run
from load.load_amplitude import run as load_amplitude_run

import subprocess

from dagster import ScheduleDefinition, define_asset_job



@asset
def product_db_raw_files():
    """Raw CSV files extracted from the product database."""
    extract_product_db_run()


@asset(deps=[product_db_raw_files])
def product_db_loaded():
    """Product DB data loaded into Postgres, in the raw schema."""
    load_product_db_run()


#==========================STRIPE
@asset
def stripe_raw_files():
    """Raw JSON files extracted from Stripe."""
    extract_stripe_run()


@asset(deps=[stripe_raw_files])
def stripe_loaded():
    """Stripe data loaded into Postgres, in the raw schema."""
    load_stripe_run()

#==========================AMPLITUDE
@asset
def amplitude_raw_files():
    """Raw JSON files extracted from Amplitude."""
    extract_amplitude_run()


@asset(deps=[amplitude_raw_files])
def amplitude_loaded():
    """Amplitude data loaded into Postgres, in the raw schema."""
    load_amplitude_run()

@asset(deps=[product_db_loaded, stripe_loaded, amplitude_loaded])
def dbt_run():
    """Runs all dbt models — staging and marts — transforming raw data into analytics-ready tables."""
    result = subprocess.run(
        ["dbt", "run"],
        cwd="transform_dbt",
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        raise Exception("dbt run failed")

pipeline_job = define_asset_job(
    name="full_pipeline",
    selection=[
        product_db_raw_files,
        product_db_loaded,
        stripe_raw_files,
        stripe_loaded,
        amplitude_raw_files,
        amplitude_loaded,
        dbt_run,
    ],
)

daily_schedule = ScheduleDefinition(
    job=pipeline_job,
    cron_schedule="0 6 * * *",
)

defs = Definitions(assets=[product_db_raw_files, product_db_loaded, stripe_raw_files, stripe_loaded, amplitude_raw_files, amplitude_loaded, dbt_run,],
    jobs=[pipeline_job],
    schedules=[daily_schedule],)



