# Data Cleanup App

A Dataset Tab App for Cleaning Datasets

## Prerequisites

Before using the app, ensure you have installed an embeddings model into your Dataloop datasets. This step is crucial for enabling the similarity check functionality.

## Overview

The Data Cleanup App offers three main functionalities to help you clean and organize your datasets efficiently:

### 1. Similarity Check

-   **Cluster Similar Images**: Group similar images into clusters based on chosen similarity metrics.
-   **Find Duplicates**: Easily identify and manage duplicate images within your dataset.
-   **Dataset Actions**: Perform various dataset actions on the clustered or duplicate images, such as deletion or categorization.

### 2. Darkness/Brightness Detection

-   **Identify Bright Images**: Detect and list images with high brightness levels.
-   **Identify Dark Images**: Detect and list images with low brightness levels.
-   **Dataset Actions**: Take necessary actions on bright or dark images to improve dataset quality.

### 3. Blurriness/Sharpness Detection

-   **Identify Blurred Images**: Detect images that are out of focus or blurred.
-   **Identify Sharp Images**: Detect images that are clear and well-focused.
-   **Dataset Actions**: Manage blurred or sharp images accordingly to ensure dataset integrity.

With these functionalities, the Data Cleanup App simplifies the process of maintaining high-quality datasets, making it an essential tool for any data-driven project.

## Technical Details: Similarity and Anomaly Detection

### Similarity Calculation

The similarity detection uses a hierarchical navigable small world (HNSW) index from the FAISS library for efficient similarity search. Here's how it works:

1. Feature vectors are normalized using L2 normalization to ensure all vectors have unit length
2. An HNSW index is created with the following parameters:
    - 32 connections per layer
    - Absolute inner product metric for similarity measurement
    - efSearch parameter of 50 for search accuracy/speed tradeoff
3. For each feature vector, the 150-nearest neighbors are found
4. Clusters are formed by grouping vectors that have similarity scores above the specified threshold
5. Clusters are sorted by size and filtered to only include clusters with the minimum required size
6. Items that have already been assigned to a cluster are excluded from subsequent clusters to avoid overlap

### Anomaly Detection

Anomalies are detected using a distance-based approach:

1. The same HNSW index and normalized vectors are used as in similarity detection
2. For each vector, its distance to its nearest neighbor is calculated
3. Items are considered anomalous if their distance to their nearest neighbor is greater than the specified threshold
4. This effectively identifies vectors that are "isolated" in the feature space, indicating unusual or unique items
