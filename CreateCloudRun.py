import subprocess
import logging
from google.api_core.exceptions import NotFound, AlreadyExists
from google.cloud import run_v2
from google.cloud import resourcemanager_v3
from google.iam.v1 import iam_policy_pb2 as iam_policy
from google.iam.v1 import policy_pb2 as policy
from GetDetails import GetDetails
from google.cloud import artifactregistry_v1beta2


class CloudRunCreator:
    def __init__(self, target_project, source_project):
        self.target_project = target_project
        self.source_project = source_project
        self.get_details = GetDetails(source_project)
        self.run_client = run_v2.ServicesClient()
        self.iam_client = resourcemanager_v3.ProjectsClient()
        self.user_choice = self.prompt_user_choice()
        self.artifact_registry_client = artifactregistry_v1beta2.ArtifactRegistryClient()

    def create_cloud_run_services(self, cloud_run_details):
        if self.user_choice == 'copy_images':
            self.copy_images_to_target_project(cloud_run_details)
        elif self.user_choice == 'grant_role':
            email = self.get_source_service_account_email()
            self.grant_artifact_registry_reader_role(email)

        for service_detail in cloud_run_details:
            if self.service_exists(service_detail['name'], service_detail['location']):
                logging.info(
                    f"Service {service_detail['name']} already exists in location {service_detail['location']}. Skipping creation.")
                continue
            self.create_cloud_run_service(service_detail)

    def service_exists(self, service_name, location):
        try:
            service = self.run_client.get_service(
                name=f"projects/{self.target_project}/locations/{location}/services/{service_name}")
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
            if self.user_choice == 'copy_images':
                image = image.replace(self.source_project, self.target_project)
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
            logging.info(f"Service {service_name} created with an error!")

    def get_source_service_account_email(self):
        project = self.iam_client.get_project(name=f"projects/{self.target_project}")
        project_number = project.name.split('/')[-1]
        return f"service-{project_number}@serverless-robot-prod.iam.gserviceaccount.com"

    def grant_artifact_registry_reader_role(self, email):
        policy_client = resourcemanager_v3.ProjectsClient()


        request = iam_policy.GetIamPolicyRequest(resource=f"projects/{self.source_project}")
        current_policy = policy_client.get_iam_policy(request=request)

        # Create a binding for the Artifact Registry Reader role
        binding = policy.Binding(
            role="roles/artifactregistry.reader",
            members=[f"serviceAccount:{email}"],
        )

        current_policy.bindings.append(binding)

        set_policy_request = iam_policy.SetIamPolicyRequest(
            resource=f"projects/{self.source_project}",
            policy=current_policy,
        )
        policy_client.set_iam_policy(request=set_policy_request)

        logging.info(f"Granted Artifact Registry Reader role to {email}")

    def copy_images_to_target_project(self,cloud_run_details):
        cloud_run_details_list = cloud_run_details

        for cloud_run_details in cloud_run_details_list:
            if 'container_images' in cloud_run_details:
                for image in cloud_run_details['container_images']:
                    if self.source_project not in image:
                        continue
                    try:
                        image_parts = image.split('/')
                        location = image_parts[0]
                        source_repository = image_parts[-2]
                        name_and_tag = image_parts[-1].split(':')
                        name = name_and_tag[0]
                        image_tag = name_and_tag[1] if len(
                            name_and_tag) > 1 else 'latest'  # Tag is the second part if available, else 'latest'

                        self.ensure_repository_exists(location.split('-')[0] + '-' + location.split('-')[1], source_repository)

                        # Pull
                        subprocess.run(['docker', 'pull', image], check=True)

                        # Tag
                        target_repository = f'{location}/{self.target_project}/{source_repository}'
                        subprocess.run(['docker', 'tag', image, f'{target_repository}/{name}:{image_tag}'], check=True)

                        # Push
                        subprocess.run(['docker', 'push', f'{target_repository}/{name}:{image_tag}'], check=True)

                        logging.info(f"Image {image} copied to target project successfully with tag '{image_tag}'.")
                    except subprocess.CalledProcessError as e:
                        logging.error(f"Error while copying image {image}: {e}")

    def ensure_repository_exists(self, location, repository_name):

        repository_path = f"projects/{self.target_project}/locations/{location}/repositories/{repository_name}"
        try:
            self.artifact_registry_client.get_repository(name=repository_path)
        except NotFound:
            self.create_repository(location, repository_name)

    def create_repository(self, location, repository_name):
        parent = f'projects/{self.target_project}/locations/{location}'

        repository_id = repository_name.lower().replace("_", "-")

        repository = artifactregistry_v1beta2.Repository(
            name=f'{parent}/repositories/{repository_id}',
            format='DOCKER'
        )

        try:
            response = self.artifact_registry_client.create_repository(
                parent=parent,
                repository=repository,
                repository_id=repository_id
            )
            logging.info(f"Repository {repository_name} created in {location}.")
        except AlreadyExists:
            logging.info(f"Repository {repository_name} already exists in {location}.")
        except Exception as e:
            logging.error(f"Error creating repository: {e}")


    def prompt_user_choice(self):
        print("Choose an option:")
        print("1. Copy images to the Artifact Registry in the target project")
        print("2. Use the images from Artifact registry in the source project")
        choice = input("Enter 1 or 2: ")

        if choice == '1':
            return 'copy_images'
        elif choice == '2':
            return 'grant_role'
        else:
            print("Invalid choice. Please enter 1 or 2.")
            return self.prompt_user_choice()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    source_project_id = 'wideops-support-393412'
    target_project_id = 'wideops-internal-web-services'
    get_details = GetDetails(source_project=source_project_id)

    cloud_run_details = get_details.get_cloud_run_details()

    cloud_run_creator = CloudRunCreator(target_project=target_project_id, source_project=source_project_id)
    cloud_run_creator.create_cloud_run_services(cloud_run_details)

