import logging
from google.cloud import asset_v1


class GetDetails:
    def __init__(self, source_project):
        self.source_project = source_project
        self.asset_client = asset_v1.AssetServiceClient()

    def format_network_interfaces(self, network_interfaces):
        formatted_interfaces = []
        for ni in network_interfaces:
            ni_details = {
                'network': ni.get('network', 'N/A').split('/')[-1],
                'subnetwork': ni.get('subnetwork', 'N/A').split('/')[-1]
            }
            formatted_interfaces.append(ni_details)
        return formatted_interfaces

    def format_disks(self, disks):
        formatted_disks = []
        for disk in disks:
            disk_details = {
                'type': disk.get('type', 'N/A').split('/')[-1],
                'deviceName': disk.get('deviceName', 'N/A'),
                'mode': disk.get('mode', 'N/A'),
                'boot': disk.get('boot', 'N/A'),
                'interface': disk.get('interface', 'N/A'),
                'diskSizeGb': disk.get('diskSizeGb', 10)  # Include disk size
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
                    instance_details = {
                        'name': asset.resource.data.get('name', 'N/A'),
                        'zone': asset.resource.data.get('zone', 'N/A').split('/')[-1],
                        'machine_type': asset.resource.data.get('machineType', 'N/A').split('/')[-1],
                        'network_interfaces': self.format_network_interfaces(
                            asset.resource.data.get('networkInterfaces', [])),
                        'disks': self.format_disks(asset.resource.data.get('disks', [])),
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
    # Set the logging level to INFO
    logging.basicConfig(level=logging.INFO)
    source_project = 'wideops-support-393412'
    get_details = GetDetails(source_project)
    instance_details_list = get_details.get_instance_details()

    # Print the instance details
    for instance_details in instance_details_list:
        print(instance_details)
