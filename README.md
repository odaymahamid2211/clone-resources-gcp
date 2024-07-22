Clone Resources GCP
This repository contains Python scripts for cloning Google Cloud Platform (GCP) resources, including virtual machines and Cloud Run services, from one project to another. It leverages Google Cloud APIs and services to retrieve, process, and create resources programmatically.

Features
Clone Compute Engine VM instances from one GCP project to another.
Clone Cloud Run services from one GCP project to another.
Handle Docker images in Artifact Registry across GCP projects.
Configure IAM roles and permissions programmatically.
Installation
Prerequisites
Python 3.x: Ensure Python 3.x is installed on your system.
Google Cloud SDK: Install the Google Cloud SDK if you haven't already.
Docker: Install Docker on your system.
Dependencies
Clone this repository:

bash
Copy code
git clone https://github.com/odaymahamid2211/clone-resources-gcp.git
cd clone-resources-gcp
Create a virtual environment and install the required Python packages:

bash
Copy code
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
Configure Docker to authenticate with Google Cloud Artifact Registry:

bash
Copy code
gcloud auth configure-docker [region]-docker.pkg.dev
Replace [region] with the appropriate region code (e.g., us, europe-west1).
