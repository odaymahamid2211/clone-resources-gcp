import logging
from google.cloud import asset_v1
from google.cloud import compute_v1


class GetDetails:
    def __init__(self, source_project):
        self.source_project = source_project
        self.asset_client = asset_v1.AssetServiceClient()
        self.compute_client = compute_v1.DisksClient()

    def format_network_interfaces(self, network_interfaces):
        formatted_interfaces = []
        for ni in network_interfaces:
            ni_details = {
                'network': ni.get('network', 'N/A').split('/')[-1],
                'subnetwork': ni.get('subnetwork', 'N/A').split('/')[-1]
            }
            formatted_interfaces.append(ni_details)
        return formatted_interfaces

    def get_disk_type(self, zone, disk_name):
        try:
            disk = self.compute_client.get(project=self.source_project, zone=zone, disk=disk_name)
            return disk.type.split('/')[-1]
        except Exception as e:
            logging.error(f"Failed to get disk type for {disk_name} in zone {zone}: {e}")
            return 'N/A'

    def get_disk_image(self, disk_name, zone):
        try:
            disk = self.compute_client.get(project=self.source_project, zone=zone, disk=disk_name)
            return disk.source_image if disk.source_image else 'N/A'
        except Exception as e:
            logging.error(f"Failed to get disk image for {disk_name} in zone {zone}: {e}")
            return 'N/A'

    def format_disks(self, disks, zone):
        formatted_disks = []
        for disk in disks:
            device_name = disk.get('deviceName', 'N/A')
            disk_name = disk.get('source', '').split('/')[-1]
            disk_type = self.get_disk_type(zone, disk_name) if disk_name != '' else 'N/A'
            disk_image = self.get_disk_image(disk_name, zone) if disk_name != '' else 'N/A'
            disk_details = {
                'diskName': disk_name,
                'image': disk_image,
                'diskSizeGb': disk.get('diskSizeGb', 10),
                'deviceName': device_name,
                'type': disk_type,
                'mode': disk.get('mode', 'N/A'),
                'boot': disk.get('boot', 'N/A'),
                'interface': disk.get('interface', 'N/A'),
            }
            formatted_disks.append(disk_details)
        return formatted_disks

    def get_instance_details(self):
        project_resource = f"projects/{self.source_project}"
        request = asset_v1.ListAssetsRequest(
            parent=project_resource,
            asset_types=['compute.googleapis.com/Instance'],
            content_type=asset_v1.ContentType.RESOURCE
        )

        instance_details_list = []

        try:
            response = self.asset_client.list_assets(request=request)

            for asset in response:
                instance_details = {}
                if asset.resource:
                    zone = asset.resource.data.get('zone', 'N/A').split('/')[-1]
                    instance_details = {
                        'name': asset.resource.data.get('name', 'N/A'),
                        'zone': zone,
                        'machine_type': asset.resource.data.get('machineType', 'N/A').split('/')[-1],
                        'network_interfaces': self.format_network_interfaces(
                            asset.resource.data.get('networkInterfaces', [])),
                        'disks': self.format_disks(asset.resource.data.get('disks', []), zone),
                        'tags': asset.resource.data.get('tags', {}).get('items', [])
                    }
                else:
                    instance_details = {
                        'name': asset.name,
                        'error': 'No resource data available for this asset.',
                        'update_time': asset.update_time
                    }
                instance_details_list.append(instance_details)

        except Exception as e:
            logging.error(f"An error occurred: {e}")

        return instance_details_list

    def get_cloud_run_details(self):
        cloud_run_details_list = []

        try:
            project_resource = f"projects/{self.source_project}"
            request = asset_v1.ListAssetsRequest(
                parent=project_resource,
                asset_types=['run.googleapis.com/Service'],
                content_type=asset_v1.ContentType.RESOURCE
            )

            response = self.asset_client.list_assets(request=request)

            for asset in response:
                cloud_run_details = {}
                if asset.resource:
                    data = asset.resource.data
                    metadata = data.get('metadata', {})
                    spec = data.get('spec', {})
                    status = data.get('status', {})

                    containers = spec.get('template', {}).get('spec', {}).get('containers', [])
                    container_images = [container.get('image', 'N/A') for container in containers]

                    cloud_run_details = {
                        'name': metadata.get('name', 'N/A'),
                        'location': metadata.get('labels', {}).get('cloud.googleapis.com/location', 'N/A'),
                        'url': status.get('address', {}).get('url', 'N/A'),
                        'ingress': metadata.get('annotations', {}).get('run.googleapis.com/ingress', 'N/A'),
                        'ingress_status': metadata.get('annotations', {}).get('run.googleapis.com/ingress-status',
                                                                              'N/A'),
                        'operation_id': metadata.get('annotations', {}).get('run.googleapis.com/operation-id', 'N/A'),
                        'api_version': data.get('apiVersion', 'N/A'),
                        'kind': data.get('kind', 'N/A'),
                        'generation': data.get('generation', 'N/A'),
                        'latest_revision': status.get('traffic', [{}])[0].get('latestRevision', False),
                        'percent_traffic': status.get('traffic', [{}])[0].get('percent', 'N/A'),
                        'latest_created_revision_name': status.get('latestCreatedRevisionName', 'N/A'),
                        'latest_ready_revision_name': status.get('latestReadyRevisionName', 'N/A'),
                        'container_images': container_images
                    }
                else:
                    cloud_run_details = {
                        'name': asset.name,
                        'error': 'No resource data available for this asset.',
                        'update_time': asset.update_time
                    }
                cloud_run_details_list.append(cloud_run_details)

        except Exception as e:
            logging.error(f"An error occurred while fetching Cloud Run details: {e}")

        return cloud_run_details_list


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    source_project = 'wideops-support-393412'
    get_details = GetDetails(source_project)

    instance_details_list = get_details.get_instance_details()
    for instance_details in instance_details_list:
        print(instance_details)


    # Get Cloud Run details
    cloud_run_details_list = get_details.get_cloud_run_details()
    for cloud_run_details in cloud_run_details_list:
        print(cloud_run_details)