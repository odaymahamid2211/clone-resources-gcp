# Clone Resources GCP

This repository contains Python scripts for cloning Google Cloud Platform (GCP) resources, including virtual machines and Cloud Run services, from one project to another. It leverages Google Cloud APIs and services to retrieve, process, and create resources programmatically.

## Features

- Clone Compute Engine VM instances from one GCP project to another.
- Clone Cloud Run services from one GCP project to another.
- Handle Docker images in Artifact Registry across GCP projects.
- Configure IAM roles and permissions programmatically.
  
### installation
1. Clone the repository:
   ```bash
   git clone https://github.com/odaymahamid2211/clone-resources-gcp.git
   cd clone-resources-gcp

2. run
   ```bash
   python main.py

### Prerequisites

1. **Python 3.x**: Ensure Python 3.x is installed on your system.
2. **Google Cloud SDK**: Install the [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) if you haven't already.
3. **Docker**: Install [Docker](https://docs.docker.com/get-docker/) on your system.
   
### Dependencies

1. Install additional required packages
   ```bash
   pip install google-cloud-asset
   pip install google-cloud-compute
   pip install google-cloud-run
   pip install google-cloud-artifactregistry
   pip install google-cloud-resourcemanager
   pip install google-api-core
   pip install google-iam
   pip install rich


2. Configure Docker to authenticate with Google Cloud Artifact Registry:
  ```bash
  gcloud auth configure-docker [region]-docker.pkg.dev

  Replace [region] with the region of your Artifact Registry.
   
