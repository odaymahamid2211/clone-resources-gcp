import logging
from google.cloud import compute_v1
from GetDetails import GetDetails


class VMCreator:
    def __init__(self, target_project):
        self.target_project = target_project
        self.compute_client = compute_v1.InstancesClient()

    def clone_instances_to_target_project(self, instances_details, default_source_image=None):
        for instance_detail in instances_details:
            if "gke" in instance_detail['name'].lower():
                logging.info(f"Skipping instance {instance_detail['name']} as it contains 'gke'")
                continue
            self.create_vm_instance(instance_detail, default_source_image)

    logging.basicConfig(level=logging.INFO)

    def create_vm_instance(self, instance_detail, default_source_image=None):
        """"
        TODO:
        check for gke named mahcines
        """

        zone = instance_detail['zone']
        project = self.target_project

        region = '-'.join(zone.split('-')[:-1])

        if default_source_image is None:
            default_source_image = "projects/debian-cloud/global/images/family/debian-10"

        disks = []
        for disk in instance_detail['disks']:
            disk_type = disk['type']
            if disk_type == 'PERSISTENT':
                disk_type = 'pd-standard'

            disk_size_gb = disk['diskSizeGb']
            device_name = disk['deviceName']

            disk_config = {
                'boot': disk['boot'],
                'auto_delete': True,
                'initialize_params': {
                    'disk_type': f"projects/{self.target_project}/zones/{zone}/diskTypes/{disk_type}",
                    'disk_size_gb': disk_size_gb,
                },
                'device_name': device_name
            }
            if disk['boot']:
                disk_config['initialize_params']['source_image'] = default_source_image
            disks.append(disk_config)

        instance_body = {
            'name': instance_detail['name'],
            'machine_type': f"zones/{zone}/machineTypes/{instance_detail['machine_type']}",
            'disks': disks,
            'network_interfaces': [
                {
                    'network': f"projects/{self.target_project}/global/networks/{ni['network']}",
                    'subnetwork': f"regions/{region}/subnetworks/{ni['subnetwork']}"
                } for ni in instance_detail['network_interfaces']
            ]
        }

        try:
            operation = self.compute_client.insert(project=project, zone=zone, instance_resource=instance_body)
            operation.result()
            logging.info(f"Instance {instance_detail['name']} created successfully.")
        except Exception as e:
            logging.error(f"An error occurred while creating the instance: {e}")


if __name__ == '__main__':
    source_project_id = 'wideops-support-393412'
    target_project_id = 'wideops-internal-web-services'

    Details = GetDetails(source_project=source_project_id)
    instances_details = Details.get_instance_details()

    vm_creator = VMCreator(target_project=target_project_id)
    vm_creator.clone_instances_to_target_project(instances_details)

