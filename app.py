import json
import logging
import os
import select
import subprocess
from collections import defaultdict

import dtlpy as dl
import numpy as np
from fastapi import APIRouter, BackgroundTasks, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from faiss import IndexFlatIP, IndexHNSWFlat, METRIC_INNER_PRODUCT
from sklearn.preprocessing import normalize

from modules.exporter import Exporter

logger = logging.getLogger('[CLEANUP]')
logging.basicConfig(level='INFO')


class Runner(dl.BaseServiceRunner):
    """
    Runner class that extends the BaseServiceRunner.

    This class is responsible for executing a bash script and capturing its output in real-time.

    Methods
    -------
    __init__():
        Initializes the Runner instance, prints the current working directory and its contents,
        and starts the bash script 'start.sh'. Captures and prints the output of the script in real-time.
        Handles KeyboardInterrupt to allow graceful termination by the user.

    run():
        Placeholder method to be implemented.
    """

    def __init__(self):
        print(f'current path: {os.getcwd()}')
        print(f'list: {os.listdir(os.getcwd())}')
        print(f'current path: {os.getcwd()}')
        proc = subprocess.Popen(
            'bash start.sh',
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            text=True,
        )
        try:
            while True:
                # Use select to wait for output
                readable, _, _ = select.select([proc.stdout, proc.stderr], [], [], 0.1)
                for f in readable:
                    line = f.readline()
                    if line:
                        print(f"Output: {line.strip()}")
                # Check if the process has terminated
                if proc.poll() is not None:
                    print("Process finished.")
                    break
        except KeyboardInterrupt:
            print("Stopped by user.")
        finally:
            proc.terminate()

    def run(self): ...


app = FastAPI()
router = APIRouter()

origins = [
    "*",  # allow all
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@router.get("/get_items")
async def get_items(
    datasetId: str,
    featureSetName: str,
    similarity: float,
    type: str,
    pagination: int = 0,
    limit: int = 10,
    min_v: float = 0,
    max_v: float = 1.0,
    clusterSize: int = 2,
):
    """
    Retrieves items from a dataset based on the specified parameters.

    Args:
        datasetId (str): The ID of the dataset to retrieve items from.
        featureSetName (str): The name of the feature set to use.
        similarity (float): The similarity threshold to use for clustering.
        type (str): The type of items to retrieve (e.g., 'Similarity', 'Anomalies', 'Darkness/Brightness').
        pagination (int): The pagination index to use.
        limit (int): The number of items to retrieve.
        min_v (float): The minimum value to use for filtering.
        max_v (float): The maximum value to use for filtering.
        clusterSize (int): The minimum number of items to include in a cluster.

    Returns:
        HTMLResponse: An HTML response containing the items in JSON format with an HTTP status code of 200.

    Notes:
        The 'type' parameter can be one of the following:
            - 'Similarity': Retrieves similar items based on the feature set and similarity threshold.
            - 'Anomalies': Retrieves anomalous items based on the feature set and similarity threshold.
            - 'Darkness/Brightness': Retrieves items based on the darkness/brightness quality score.
    """

    exporter: Exporter = Exporter(dataset_id=datasetId)
    if type == 'Similarity' or type == 'Anomalies':
        feature_vectors = exporter.feature_sets_export[featureSetName]
        item_ids = [
            {
                'itemId': item['itemId'],
                'thumbnail': item['thumbnail'],
                'name': item['name'],
                'annotated': item['annotated'],
            }
            for item in feature_vectors
        ]
        eps_value = similarity

        if type == 'Similarity':

            cluster_dict = defaultdict(list)

            # Determine clusters based on eps_value
            for i, (dist, idx) in enumerate(
                zip(exporter.distance[featureSetName], exporter.indices[featureSetName])
            ):
                cluster_dict[i] = idx[
                    : np.searchsorted(dist, eps_value, side='right')
                ].tolist()

            # Sort clusters by size
            sorted_clusters = sorted(
                cluster_dict.items(), key=lambda x: len(x[1]), reverse=True
            )

            # Use a set to track used items
            used_items = set()

            # Prepare the output data structure
            output_clusters = []
            cluster_id = 0
            page_limit = 1000
            for _, members in sorted_clusters:
                # Remove used members
                unique_members = [m for m in members if m not in used_items]
                if len(unique_members) >= clusterSize:
                    # Create a new cluster
                    main_item = item_ids[unique_members[0]]
                    rest_items = [item_ids[m] for m in unique_members[1:]]

                    cluster_info = {
                        'key': f"Cluster {cluster_id}",
                        'main_item': main_item,
                        'items': rest_items,
                        'is_choosed': False,
                    }
                    output_clusters.append(cluster_info)

                    # Mark members as used
                    used_items.update(unique_members)
                    cluster_id += 1

            # Sorting clusters by the number of items (descending order)
            output_clusters.sort(key=lambda x: len(x['items']), reverse=True)

            total_items_processed = 0
            for cluster in output_clusters:
                cluster_size = len(cluster['items'])  # Include the main item
                cluster['page'] = total_items_processed // page_limit + 1
                total_items_processed += cluster_size

            # first cluster have is_choosed = True
            if len(output_clusters) > 0:
                output_clusters[0]['is_choosed'] = True
            else:
                # create dummy cluster
                output_clusters.append(
                    {
                        'key': 'Cluster 0',
                        'main_item': '',
                        'items': [],
                        'is_choosed': True,
                    }
                )

            return HTMLResponse(json.dumps(output_clusters, indent=2), status_code=200)

        else:
            ids = [
                item_ids[i]
                for i, dist in enumerate(exporter.distance[featureSetName])
                if dist[1] > eps_value  # Adjust for cosine similarity
            ]

            return HTMLResponse(
                json.dumps({'items': ids, 'total': len(ids)}, indent=2), status_code=200
            )

    else:
        items_count, ids = exporter.quality_score(
            type, min_v, max_v, pagination, limit, True
        )
        return HTMLResponse(
            json.dumps({'items': ids, 'total': items_count}, indent=2), status_code=200
        )


@router.get("/export/status")
async def export_status(datasetId: str):
    """
    Export the status of a dataset.

    This asynchronous function creates an Exporter instance for the given dataset ID,
    retrieves the export progress, last update date, and status, and returns this information
    as an HTML response in JSON format.

    Args:
        datasetId (str): The ID of the dataset to export the status for.

    Returns:
        HTMLResponse: An HTML response containing the export status in JSON format with a status code of 200.
    """

    exporter: Exporter = Exporter(dataset_id=datasetId)
    status = {
        'progress': int(exporter.progress),
        'exportDate': exporter.last_update,
        'status': exporter.status.value,
    }
    logger.info("Returning status: %s", status)
    return HTMLResponse(json.dumps(status, indent=2), status_code=200)


@router.get("/export/run")
async def export_run(datasetId: str, cache: str, background_tasks: BackgroundTasks):
    """
    Initiates an export run for the given dataset.

    Args:
        datasetId (str): The ID of the dataset to be exported.
        cache (str): Indicates whether to use cache during the export process.
        background_tasks (BackgroundTasks): The background tasks manager to handle asynchronous tasks.

    Returns:
        HTMLResponse: A response indicating that the export process has started.
    """
    exporter: Exporter = Exporter(dataset_id=datasetId)
    exporter.progress = 0
    background_tasks.add_task(exporter.check_and_run, use_cache=cache)
    return HTMLResponse(json.dumps({'status': 'started'}), status_code=200)


@router.get("/available_feature_sets")
async def available_feature_sets(datasetId: str):
    """
    Retrieve the available feature sets for a given dataset.

    Args:
        datasetId (str): The ID of the dataset for which to retrieve feature sets.

    Returns:
        HTMLResponse: An HTML response containing a JSON-encoded list of feature set names and a status code of 200.
    """
    exporter: Exporter = Exporter(dataset_id=datasetId)
    feature_sets = exporter.get_feature_sets_names()
    return HTMLResponse(json.dumps(feature_sets), status_code=200)


@router.get("/start_execution")
async def start_execution(datasetId: str, exec_type: str):
    """
    Starts the execution of a dataset export process.
    Args:
        datasetId (str): The ID of the dataset to be exported.
        exec_type (str): The type of execution to be performed.
    Returns:
        HTMLResponse: A response object containing the status of the execution process in JSON format.
    """

    exporter: Exporter = Exporter(dataset_id=datasetId)
    exporter.start_execution(exec_type)
    status = {
        'progress': exporter.execution_running.get(exec_type)['progress'],
        'status': exporter.execution_running.get(exec_type)['status'],
        'full_status': exporter.execution_running.get(exec_type)['full_status'],
    }
    return HTMLResponse(json.dumps(status), status_code=200)


@router.get("/get_execution_status")
async def get_execution_status(datasetId: str, exec_type: str):
    """
    Asynchronously retrieves the execution status of a dataset export operation.

    Args:
        datasetId (str): The unique identifier of the dataset.
        exec_type (str): The type of execution to check the status for.

    Returns:
        HTMLResponse: A response object containing the execution status in JSON format with a status code of 200.
    """
    exporter: Exporter = Exporter(dataset_id=datasetId)
    status = {
        'progress': exporter.execution_running.get(exec_type)['progress'],
        'status': exporter.execution_running.get(exec_type)['status'],
        'full_status': exporter.execution_running.get(exec_type)['full_status'],
    }
    return HTMLResponse(json.dumps(status), status_code=200)


@router.get("/get_quality_score_exist")
async def get_quality_score_exist(datasetId: str):
    """
    Asynchronously retrieves the quality score for a given dataset.

    Args:
        datasetId (str): The ID of the dataset to retrieve the quality score for.

    Returns:
        HTMLResponse: A response object containing the quality score in JSON format and a status code of 200.
    """
    exporter: Exporter = Exporter(dataset_id=datasetId)
    items_count = exporter.quality_score('Darkness/Brightness', 0, 1)
    status = items_count
    return HTMLResponse(json.dumps(status), status_code=200)


app.include_router(router, prefix='/api')

app.mount(
    "/cleanup", StaticFiles(directory="panels/cleanup", html=True), name='cleanup'
)


if __name__ == '__main__':
    runner = Runner()
