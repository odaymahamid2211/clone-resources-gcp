import logging
from GetDetails import GetDetails
from CreateCloudRun import CloudRunCreator
from CreateVM import VMCreator
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from rich.panel import Panel
from rich.style import Style
import sys

def main():
    # Initialize logging
    logging.basicConfig(level=logging.INFO)

    console = Console()

    # Display welcome message
    display_welcome_message(console)

    # Get project IDs
    source_project_id = get_project_id(console, "Please enter the source project ID: ")
    target_project_id = get_project_id(console, "Please enter the target project ID: ")

    # Display service choice menu
    service_choice = display_service_choice_menu(console)

    # Initialize GetDetails
    get_details = GetDetails(source_project=source_project_id)

    # Execute based on the user choice
    execute_choice(console, service_choice, get_details, target_project_id, source_project_id)

    # Finish message
    console.print(Panel("[bold green]Copying process completed. Thank you for using GCP Service Copier![/bold green]",
                        expand=False))


def display_welcome_message(console):
    """Display the welcome message."""
    console.print(Panel("[bold cyan]Welcome to the GCP Service Copier![/bold cyan]", expand=False))


def get_project_id(console, prompt):
    """Get a valid project ID from the user."""
    while True:
        project_id = Prompt.ask(prompt, console=console).strip()
        if project_id:
            return project_id
        console.print("[bold red]Invalid input. Please enter a valid project ID.[/bold red]")


def display_service_choice_menu(console):
    """Display the service choice menu."""
    menu_options = [
        "Copy Cloud Run services",
        "Copy VM instances",
        "Copy all services",
        "Exit"
    ]

    table = Table(title="Service Choice Menu", show_header=True, header_style="bold magenta")
    table.add_column("Option", style="dim", width=12)
    table.add_column("Description")

    for idx, option in enumerate(menu_options, 1):
        table.add_row(str(idx), option)

    console.print(table)

    while True:
        choice = Prompt.ask("Enter your choice (1-4)", choices=[str(i) for i in range(1, 5)], console=console)
        if choice == '4':  # Exit
            console.print("[bold yellow]Exiting...[/bold yellow]")
            exit(0)
        return choice


def execute_choice(console, service_choice, get_details, target_project_id, source_project_id):
    """Execute the choice based on user's selection."""
    if service_choice == '1':
        console.print("[bold blue]You have chosen to copy Cloud Run services.[/bold blue]")

        cloud_run_details = get_details.get_cloud_run_details()

        # Print what will be copied
        if cloud_run_details:
            table = Table(title="Cloud Run Services to be Copied", show_header=True, header_style="bold green")
            table.add_column("Service Name", style="cyan")
            table.add_column("Location", style="cyan")
            for service in cloud_run_details:
                table.add_row(service['name'], service['location'])
            console.print(table)
        else:
            console.print("[bold red]No Cloud Run services found.[/bold red]")

        # Proceed with copying Cloud Run services
        cloud_run_creator = CloudRunCreator(target_project=target_project_id, source_project=source_project_id)
        cloud_run_creator.create_cloud_run_services(cloud_run_details)

    elif service_choice == '2':
        console.print("[bold blue]You have chosen to copy VM instances.[/bold blue]")

        instances_details = get_details.get_instance_details()

        # Print what will be copied
        if instances_details:
            table = Table(title="VM Instances to be Copied", show_header=True, header_style="bold green")
            table.add_column("Instance Name", style="cyan")
            table.add_column("Machine Type", style="cyan")
            table.add_column("Zone", style="cyan")
            for instance in instances_details:
                table.add_row(instance['name'], instance['machine_type'], instance['zone'])
            console.print(table)
        else:
            console.print("[bold red]No VM instances found.[/bold red]")

        # Proceed with copying VM instances
        vm_creator = VMCreator(target_project=target_project_id)
        vm_creator.clone_instances_to_target_project(instances_details)

    elif service_choice == '3':
        console.print("[bold blue]You have chosen to copy all services.[/bold blue]")

        # Cloud Run services
        cloud_run_details = get_details.get_cloud_run_details()
        if cloud_run_details:
            table = Table(title="Cloud Run Services to be Copied", show_header=True, header_style="bold green")
            table.add_column("Service Name", style="cyan")
            table.add_column("Location", style="cyan")
            for service in cloud_run_details:
                table.add_row(service['name'], service['location'])
            console.print(table)
        else:
            console.print("[bold red]No Cloud Run services found.[/bold red]")

        # Proceed with copying Cloud Run services
        cloud_run_creator = CloudRunCreator(target_project=target_project_id, source_project=source_project_id)
        cloud_run_creator.create_cloud_run_services(cloud_run_details)

        # VM instances
        instances_details = get_details.get_instance_details()
        if instances_details:
            table = Table(title="VM Instances to be Copied", show_header=True, header_style="bold green")
            table.add_column("Instance Name", style="cyan")
            table.add_column("Machine Type", style="cyan")
            table.add_column("Zone", style="cyan")
            for instance in instances_details:
                table.add_row(instance['name'], instance['machine_type'], instance['zone'])
            console.print(table)
        else:
            console.print("[bold red]No VM instances found.[/bold red]")

        # Proceed with copying VM instances
        vm_creator = VMCreator(target_project=target_project_id)
        vm_creator.clone_instances_to_target_project(instances_details)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        console = Console()
        console.print("\n[bold red]Process interrupted by user. Exiting.[/bold red]")
        sys.exit(0)
