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
                'type': disk_type,
                'deviceName': device_name,
                'mode': disk.get('mode', 'N/A'),
                'boot': disk.get('boot', 'N/A'),
                'interface': disk.get('interface', 'N/A'),
                'diskSizeGb': disk.get('diskSizeGb', 10),  # Include disk size
                'image': disk_image,
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


if __name__ == '__main__':

    logging.basicConfig(level=logging.INFO)
    source_project = 'wideops-support-393412'
    get_details = GetDetails(source_project)
    instance_details_list = get_details.get_instance_details()

    for instance_details in instance_details_list:
        print(instance_details)
