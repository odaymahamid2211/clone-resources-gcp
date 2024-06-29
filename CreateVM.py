import logging
from google.cloud import compute_v1
from GetDetails import GetDetails
from google.api_core.exceptions import NotFound

class VMCreator:
    def __init__(self, target_project):
        self.target_project = target_project
        self.compute_client = compute_v1.InstancesClient()
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

        network_interfaces = [
            {
                'network': f"projects/{self.target_project}/global/networks/{ni['network']}",
                'subnetwork': f"regions/{region}/subnetworks/{ni['subnetwork']}"
            } for ni in instance_detail['network_interfaces']
        ]

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
