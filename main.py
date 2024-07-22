import logging
from GetDetails import GetDetails
from CreateCloudRun import CloudRunCreator
from CreateVM import VMCreator


def main():
    logging.basicConfig(level=logging.INFO)

    print("Welcome to the GCP Service Copier!")
    source_project_id = input("Please enter the source project ID: ")
    target_project_id = input("Please enter the target project ID: ")

    print("Choose the service you want to copy:")
    print("1. Copy Cloud Run services")
    print("2. Copy VM instances")
    service_choice = input("Enter 1 or 2: ")

    if service_choice == '1':
        get_details = GetDetails(source_project=source_project_id)
        cloud_run_details = get_details.get_cloud_run_details()

        cloud_run_creator = CloudRunCreator(target_project=target_project_id, source_project=source_project_id)
        cloud_run_creator.create_cloud_run_services(cloud_run_details)
    elif service_choice == '2':
        get_details = GetDetails(source_project=source_project_id)
        instances_details = get_details.get_instance_details()

        vm_creator = VMCreator(target_project=target_project_id)
        vm_creator.clone_instances_to_target_project(instances_details)
    else:
        print("Invalid choice. Please enter 1 or 2.")

if __name__ == '__main__':
    main()
