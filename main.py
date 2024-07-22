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
    print("3. Copy all services")
    service_choice = input("Enter 1, 2, or 3: ")
    get_details = GetDetails(source_project=source_project_id)

    if service_choice == '1':
        print("You have chosen to copy Cloud Run services.")
        cloud_run_details = get_details.get_cloud_run_details()

        # Print what will be copied
        print("\nCloud Run services to be copied:")
        for service in cloud_run_details:
            print(f"Service Name: {service['name']},Location: {service['location']}")

        # Proceed with copying Cloud Run services
        cloud_run_creator = CloudRunCreator(target_project=target_project_id, source_project=source_project_id)
        cloud_run_creator.create_cloud_run_services(cloud_run_details)

    elif service_choice == '2':
        print("You have chosen to copy VM instances.")
        instances_details = get_details.get_instance_details()

        # Print what will be copied
        print("\nVM instances to be copied:")
        for instance in instances_details:
            print(
                f"Instance Name: {instance['name']}, Machine Type: {instance['machine_type']}, Zone: {instance['zone']}")

        # Proceed with copying VM instances
        vm_creator = VMCreator(target_project=target_project_id)
        vm_creator.clone_instances_to_target_project(instances_details)

    elif service_choice == '3':
        print("You have chosen to copy all services:")

        # Cloud Run services
        cloud_run_details = get_details.get_cloud_run_details()
        print("\nCloud Run services to be copied:")
        for service in cloud_run_details:
            print(
                f"Service Name: {service['name']}, Image: {service['image']}, Memory: {service.get('memory', 'N/A')}, CPU: {service.get('cpu', 'N/A')}")

        # Proceed with copying Cloud Run services
        cloud_run_creator = CloudRunCreator(target_project=target_project_id, source_project=source_project_id)
        cloud_run_creator.create_cloud_run_services(cloud_run_details)

        # VM instances
        instances_details = get_details.get_instance_details()
        print("\nVM instances to be copied:")
        for instance in instances_details:
            print(
                f"Instance Name: {instance['name']}, Machine Type: {instance['machine_type']}, Zone: {instance['zone']}")

        # Proceed with copying VM instances
        vm_creator = VMCreator(target_project=target_project_id)
        vm_creator.clone_instances_to_target_project(instances_details)

    else:
        print("Invalid choice. Please enter 1, 2, or 3.")


if __name__ == '__main__':
    main()
