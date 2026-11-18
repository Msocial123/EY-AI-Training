"""Builds the ShopEase pipeline as an Azure Machine Learning pipeline (SDK v2) and submits it.

    python -m azureml.aml_pipeline --dry-run   # build only and print the pipeline YAML
    python -m azureml.aml_pipeline             # submit to your Azure ML workspace

Before submitting: run `az login` and set AZURE_SUBSCRIPTION_ID, AZURE_RESOURCE_GROUP,
AZUREML_WORKSPACE and AZUREML_COMPUTE (the name of a compute cluster).
"""
import argparse
import os
from pathlib import Path

from azure.ai.ml import Input, MLClient, Output, command
from azure.ai.ml.dsl import pipeline
from azure.ai.ml.entities import Environment
from azure.identity import DefaultAzureCredential

PROJECT_ROOT = Path(__file__).resolve().parent.parent

pipeline_env = Environment(
    name="shopease-pipeline-env",
    image="mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu22.04:latest",
    conda_file=str(PROJECT_ROOT / "azureml" / "environment.yml"),
)

transform_step = command(
    name="transform_orders",
    display_name="Extract + Transform",
    code=str(PROJECT_ROOT),
    command="python -m pipeline.run_pipeline --stage transform "
            "--input ${{inputs.raw_data}} --output ${{outputs.staged_data}}",
    inputs={"raw_data": Input(type="uri_folder")},
    outputs={"staged_data": Output(type="uri_folder")},
    environment=pipeline_env,
)

load_step = command(
    name="load_warehouse",
    display_name="Load to warehouse",
    code=str(PROJECT_ROOT),
    command="python -m pipeline.run_pipeline --stage load "
            "--input ${{inputs.staged_data}} --output ${{outputs.report}}",
    inputs={"staged_data": Input(type="uri_folder")},
    outputs={"report": Output(type="uri_folder")},
    environment=pipeline_env,
)


@pipeline(description="ShopEase daily sales: raw files -> clean data -> warehouse")
def shopease_pipeline(raw_data):
    """Connect the two steps: the output of transform becomes the input of load."""
    transform_job = transform_step(raw_data=raw_data)
    load_job = load_step(staged_data=transform_job.outputs.staged_data)
    return {"report": load_job.outputs.report}


def main():
    """Create the pipeline job and either print it (--dry-run) or submit it."""
    parser = argparse.ArgumentParser(description="Submit the ShopEase Azure ML pipeline")
    parser.add_argument("--dry-run", action="store_true", help="print the job, do not submit")
    options = parser.parse_args()

    pipeline_job = shopease_pipeline(
        raw_data=Input(type="uri_folder", path=str(PROJECT_ROOT / "data" / "raw"))
    )
    pipeline_job.experiment_name = "shopease-daily-sales"
    if options.dry_run:
        print(pipeline_job)
        return

    pipeline_job.settings.default_compute = os.environ["AZUREML_COMPUTE"]
    ml_client = MLClient(
        DefaultAzureCredential(),
        subscription_id=os.environ["AZURE_SUBSCRIPTION_ID"],
        resource_group_name=os.environ["AZURE_RESOURCE_GROUP"],
        workspace_name=os.environ["AZUREML_WORKSPACE"],
    )
    submitted = ml_client.jobs.create_or_update(pipeline_job)
    print("Submitted pipeline job:", submitted.name)
    print("Track it in Azure ML Studio:", submitted.studio_url)


if __name__ == "__main__":
    main()
