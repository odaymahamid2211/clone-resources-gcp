import logging
from google.cloud import run_v2
from GetDetails import GetDetails
from google.api_core.exceptions import NotFound

class CloudRunCreator:
    def __init__(self, target_project):
        self.target_project = target_project
        self.run_client = run_v2.ServicesClient()

    def create_cloud_run_services(self, cloud_run_details):
        for service_detail in cloud_run_details:
            if self.service_exists(service_detail['name'], service_detail['location']):
                logging.info(f"Service {service_detail['name']} already exists in location {service_detail['location']}. Skipping creation.")
                continue
            self.create_cloud_run_service(service_detail)

    def service_exists(self, service_name, location):
        try:
            service = self.run_client.get_service(name=f"projects/{self.target_project}/locations/{location}/services/{service_name}")
            return True
        except NotFound:
            return False
        except Exception as e:
            logging.error(f"An error occurred while checking if service '{service_name}' exists: {e}")
            return False

    def create_cloud_run_service(self, service_detail):
        location = service_detail['location']
        project = self.target_project
        service_name = service_detail['name']

        containers = []
        for image in service_detail['container_images']:
            container = run_v2.Container(image=image)
            containers.append(container)

        template = run_v2.RevisionTemplate(
            containers=containers
        )


        container_resources = service_detail['container_resources']
        cpu = container_resources['cpu']
        memory = container_resources['memory']

        resources = run_v2.ResourceRequirements(
            limits={'cpu': cpu, 'memory': memory}
        )

        service = run_v2.Service(
            template=template,
            ingress=run_v2.IngressTraffic.INGRESS_TRAFFIC_ALL
        )

        try:
            operation = self.run_client.create_service(
                parent=f"projects/{project}/locations/{location}",
                service=service,
                service_id=service_name
            )
            operation.result()
            logging.info(f"Service {service_name} created successfully.")
        except Exception as e:
            logging.error(f"An error occurred while creating the service '{service_name}': {e}")
            self.delete_cloud_run_service(service_name, location)

    def delete_cloud_run_service(self, service_name, location):
        try:
            self.run_client.delete_service(name=f"projects/{self.target_project}/locations/{location}/services/{service_name}")
        except Exception as e:
            logging.error(f"An error occurred while deleting the service '{service_name}': {e}")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    source_project_id = 'wideops-support-393412'
    target_project_id = 'wideops-internal-web-services'

    get_details = GetDetails(source_project=source_project_id)
    cloud_run_details = get_details.get_cloud_run_details()

    cloud_run_creator = CloudRunCreator(target_project=target_project_id)
    cloud_run_creator.create_cloud_run_services(cloud_run_details)
