import logging
from google.cloud import compute_v1
from GetDetails import GetDetails
from google.api_core.exceptions import NotFound


class VMCreator:
    def __init__(self, target_project):
        self.target_project = target_project
        self.compute_client = compute_v1.InstancesClient()
        self.network_client = compute_v1.NetworksClient()
        self.subnetwork_client = compute_v1.SubnetworksClient()  # Added SubnetworksClient
        self.existing_instances_details = []

    def clone_instances_to_target_project(self, instances_details):
        for instance_detail in instances_details:
            if "gke" in instance_detail['name'].lower():
                logging.info(f"Skipping instance {instance_detail['name']} as it originates from GKE")
                continue
            if self.instance_exists(instance_detail['name'], instance_detail['zone']):
                logging.info(f"Instance {instance_detail['name']} already exists in zone {instance_detail['zone']}. Skipping creation.")
                continue
            self.create_vm_instance(instance_detail)

    def instance_exists(self, instance_name, zone):
        try:
            instance = self.compute_client.get(project=self.target_project, zone=zone, instance=instance_name)
            self.existing_instances_details.append(instance)
            return True
        except NotFound:
            return False
        except Exception as e:
            logging.error(f"An error occurred while checking if instance '{instance_name}' exists: {e}")
            return False

    def vpc_exists(self, vpc_name):
        try:
            self.network_client.get(project=self.target_project, network=vpc_name)
            return True
        except NotFound:
            return False
        except Exception as e:
            logging.error(f"An error occurred while checking if VPC '{vpc_name}' exists: {e}")
            return False

    def create_vpc(self, vpc_name):
        """Create a VPC network if it does not exist."""
        network_body = {
            "name": vpc_name,
            "auto_create_subnetworks": False,  # We'll handle subnet creation separately
            "routing_config": {"routing_mode": "REGIONAL"}
        }
        try:
            operation = self.network_client.insert(
                project=self.target_project,
                network_resource=network_body
            )
            operation.result()
            logging.info(f"VPC '{vpc_name}' created successfully in project {self.target_project}.")
            return True
        except Exception as e:
            logging.error(f"An error occurred while creating VPC '{vpc_name}': {e}")
            return False

    def subnet_exists(self, subnet_name, region):
        try:
            self.subnetwork_client.get(project=self.target_project, region=region, subnetwork=subnet_name)
            return True
        except NotFound:
            return False
        except Exception as e:
            logging.error(f"An error occurred while checking if Subnetwork '{subnet_name}' exists in region {region}: {e}")
            return False

    def create_subnet(self, subnet_name, region, vpc_name, ip_cidr_range="10.0.0.0/24"):
        """Create a subnet within the specified VPC."""
        subnet_body = {
            "name": subnet_name,
            "network": f"projects/{self.target_project}/global/networks/{vpc_name}",
            "ip_cidr_range": ip_cidr_range,
            "region": region
        }
        try:
            operation = self.subnetwork_client.insert(
                project=self.target_project,
                region=region,
                subnetwork_resource=subnet_body
            )
            operation.result()
            logging.info(f"Subnet '{subnet_name}' created successfully in region {region}.")
            return True
        except Exception as e:
            logging.error(f"An error occurred while creating Subnetwork '{subnet_name}' in region {region}: {e}")
            return False

    def create_vm_instance(self, instance_detail):
        zone = instance_detail['zone']
        project = self.target_project

        region = '-'.join(zone.split('-')[:-1])

        # Prepare disks configuration
        disks = []
        for disk in instance_detail['disks']:
            disk_type = disk['type']
            disk_size_gb = disk['diskSizeGb']
            device_name = disk['deviceName']
            source_image = disk['image']  # Use the provided image for each disk
            disk_name = disk['diskName']  # Include disk name

            if source_image != 'N/A':
                source_image = f"projects/{source_image.split('/')[-4]}/global/images/{source_image.split('/')[-1]}"

            disk_config = {
                'boot': disk['boot'],
                'auto_delete': True,
                'initialize_params': {
                    'disk_name': disk_name,  # Include the disk name
                    'disk_type': f"projects/{self.target_project}/zones/{zone}/diskTypes/{disk_type}",
                    'disk_size_gb': disk_size_gb,
                    'source_image': source_image if source_image != 'N/A' else None
                },
                'device_name': device_name
            }

            if disk_config['initialize_params']['source_image'] is None:
                del disk_config['initialize_params']['source_image']

            disks.append(disk_config)

        # Check if the specified network exists, else use the default network
        network_interfaces = []
        for ni in instance_detail['network_interfaces']:
            network_name = ni['network']
            if not self.vpc_exists(network_name):
                logging.info(f"VPC '{network_name}' does not exist. Creating it.")
                if not self.create_vpc(network_name):
                    logging.warning(f"Failed to create VPC '{network_name}'. Using the default network instead.")
                    network_name = 'default'
            subnet_name = ni['subnetwork']
            if not self.subnet_exists(subnet_name, region):
                logging.info(f"Subnetwork '{subnet_name}' does not exist in region {region}. Creating it.")
                self.create_subnet(subnet_name, region, network_name)
            network_interface = {
                'network': f"projects/{self.target_project}/global/networks/{network_name}",
                'subnetwork': f"regions/{region}/subnetworks/{subnet_name}"
            }
            network_interfaces.append(network_interface)

        instance_body = {
            'name': instance_detail['name'],
            'machine_type': f"zones/{zone}/machineTypes/{instance_detail['machine_type']}",
            'disks': disks,
            'network_interfaces': network_interfaces,
            'tags': {
                'items': instance_detail.get('tags', [])
            }
        }

        try:
            operation = self.compute_client.insert(project=project, zone=zone, instance_resource=instance_body)
            operation.result()
            logging.info(f"Instance {instance_detail['name']} created successfully.")
        except Exception as e:
            logging.error(f"An error occurred while creating the instance '{instance_detail['name']}': {e}")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    source_project_id = 'wideops-support-393412'
    target_project_id = 'wideops-internal-web-services'

    get_details = GetDetails(source_project=source_project_id)
    instances_details = get_details.get_instance_details()

    vm_creator = VMCreator(target_project=target_project_id)
    vm_creator.clone_instances_to_target_project(instances_details)
