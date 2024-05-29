from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, APIRouter
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from modules.exporter import Exporter
import dtlpy as dl
import subprocess
import logging
import select
import os
import json
from sklearn.preprocessing import normalize
from sklearn.cluster import DBSCAN
import numpy as np
from collections import defaultdict

logger = logging.getLogger('[CLEANUP]')
logging.basicConfig(level='INFO')


class Runner(dl.BaseServiceRunner):
    def __init__(self):
        print(f'current path: {os.getcwd()}')
        print(f'list: {os.listdir(os.getcwd())}')
        print(f'current path: {os.getcwd()}')
        proc = subprocess.Popen('bash start.sh', stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)
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

    def run(self):
        ...


class ExporterHandles:
    def __init__(self):
        self.exporters = dict()

    def get(self, dataset_id):
        if dataset_id not in self.exporters:
            self.exporters[dataset_id] = Exporter(dataset_id=dataset_id)
        print(self.exporters)
        return self.exporters[dataset_id]


app = FastAPI()
router = APIRouter()
exporters_handler = ExporterHandles()

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
def get_items(datasetId: str, featureSetName: str, similarity: float, type: str, pagination: int = 0, limit: int = 10, min_v: float = 0, max_v: float = 1.0):
    exporter: Exporter = exporters_handler.get(dataset_id=datasetId)
    if type == 'Similarity':
        feature_vectors = exporter.feature_sets_export[featureSetName]
        values = np.array([item['value'] for item in feature_vectors])
        normalized_data = normalize(values, norm='l2')
        item_ids = [item['itemId'] for item in feature_vectors]

        eps_value = similarity  # Define your own epsilon value
        min_samples_value = 2
        dbscan = DBSCAN(eps=eps_value, min_samples=min_samples_value, metric='cosine')

        clusters = dbscan.fit_predict(normalized_data)

        cluster_dict = defaultdict(list)
        for item_id, cluster in zip(item_ids, clusters):
            cluster_dict[cluster].append(item_id)

        # Prepare the output data structure
        output_clusters = []
        for cluster, items in cluster_dict.items():
            if cluster != -1 and len(items) >= 2:  # Filter out noise and ensure at least two items
                # Split the first item and the rest
                main_item = items[0]
                rest_items = items[1:]

                # Create the structured dictionary
                cluster_info = {
                    'key': f"Cluster {cluster}",
                    'main_item': main_item,
                    'items': rest_items,
                    'is_choosed': False,
                }
                output_clusters.append(cluster_info)

        # Sorting clusters by the number of items (descending order)
        output_clusters.sort(key=lambda x: len(x['items']), reverse=True)

        # first cluster have is_choosed = True
        if len(output_clusters) > 0:
            output_clusters[0]['is_choosed'] = True
        else:
            # create dummy cluster
            output_clusters.append({
                'key': 'Cluster 0',
                'main_item': '',
                'items': [],
                'is_choosed': True,
            })

        return HTMLResponse(json.dumps(output_clusters, indent=2), status_code=200)
    elif type != 'Similarity':
        items_count, ids = exporter.quality_score(type, min_v, max_v, pagination, limit, True)
        return HTMLResponse(json.dumps({'items': ids, 'total': items_count}, indent=2), status_code=200)


@router.get("/export/status")
async def export_status(datasetId: str):
    exporter: Exporter = exporters_handler.get(dataset_id=datasetId)
    status = {
        'progress': 100 if exporter.status == 'ready' else int(exporter.progress),
        'exportDate': exporter.export_date,
        'status': exporter.status,
        'exportItemId': exporter.export_item_id
    }
    logger.info(f"Returning status: {status}")
    return HTMLResponse(json.dumps(status, indent=2), status_code=200)


@router.get("/export/run")
async def export_run(datasetId: str, timezone: str):
    exporter: Exporter = exporters_handler.get(dataset_id=datasetId)
    exporter.timezone = timezone
    exporter.status = "starting"
    exporter.progress = 0
    exporter.start_export()
    return HTMLResponse(json.dumps({'status': 'started'}), status_code=200)


@router.get("/available_feature_sets")
async def available_feature_sets(datasetId: str):
    exporter: Exporter = exporters_handler.get(dataset_id=datasetId)
    feature_sets = exporter.get_feature_sets_names()
    return HTMLResponse(json.dumps(feature_sets), status_code=200)


@router.get("/start_execution")
async def start_execution(datasetId: str, exec_type: str):
    exporter: Exporter = exporters_handler.get(dataset_id=datasetId)
    exporter.start_execution(exec_type)
    status = {
        'progress': exporter.execution_running.get(exec_type)['progress'],
        'status': exporter.execution_running.get(exec_type)['status'],
        'full_status': exporter.execution_running.get(exec_type)['full_status']

    }
    return HTMLResponse(json.dumps(status), status_code=200)


@router.get("/get_execution_status")
async def get_execution_status(datasetId: str, exec_type: str):
    exporter: Exporter = exporters_handler.get(dataset_id=datasetId)
    status = {
        'progress': exporter.execution_running.get(exec_type)['progress'],
        'status': exporter.execution_running.get(exec_type)['status'],
        'full_status': exporter.execution_running.get(exec_type)['full_status']
    }
    return HTMLResponse(json.dumps(status), status_code=200)


@router.get("/get_quality_score_exist")
async def get_quality_score_exist(datasetId: str):
    exporter: Exporter = exporters_handler.get(dataset_id=datasetId)
    items_count = exporter.quality_score('Darkness/Brightness', 0, 1)
    status = items_count
    return HTMLResponse(json.dumps(status), status_code=200)


app.include_router(router, prefix='/api')

app.mount("/cleanup", StaticFiles(directory="panels/cleanup", html=True), name='cleanup')


if __name__ == '__main__':
    runner = Runner()
