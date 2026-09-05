class DockerBuildException(Exception):
    """A simple exception to raise when a Docker build fails"""
    pass

import requests
import os
import hashlib
import docker
from docker.errors import DockerException
from rich.console import Console
from rich.table import Table

# Initialize a new Rich console
console = Console()

# Data for pulling the source files from GitHub
GITHUB_DATA = {"owner": "Xenus96", "repository": "ThreatCheckerBot", "branch": "main"}
FILES_TO_DOWNLOAD = ["requirements.txt", "vars.env", "Dockerfile", "main.py"]
BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_DATA["owner"]}/{GITHUB_DATA["repository"]}/{GITHUB_DATA["branch"]}"

# A dictionary for storing the calculated Hash strings of the files pulled from GitHub
FILE_HASHES = {}

# A tuple of names of all the API Keys from the "vars.env" file
API_TOKENS = ("TELEGRAM_BOT_TOKEN", "OPENROUTER_TOKEN", "VIRUSTOTAL_TOKEN",
              "ABUSEIPDB_TOKEN", "SHODAN_TOKEN", "URLSCANIO_TOKEN",
              "PULSEDIVE_TOKEN", "MALWARE_BAZAAR_TOKEN")


def docker_build_and_run():
    """
    A function for downloading all required project files,
    verifying them and building a containerized App
    """
    # ======= LOAD THE VERIFICATION HASHES =======

    try:
        # Try to open the "hashes.txt" file
        with open("D:\\ThreatCheckerBot\\hashes.txt", "r", encoding="utf-8") as hashes_file:
            # Read the file line-by-line
            for line in hashes_file.readlines():
                # Split each line into a list and remove the "\n" symbol from the end of the hash
                line = line.replace("\n", "").split(":")
                # Add each list to the FILE_HASHES dictionary
                FILE_HASHES[line[0]] = line[1]
    # If the file wasn't found then display the warning message
    except FileNotFoundError:
        console.print(f"[bold yellow][WARNING][/bold yellow]: Unable to find the \"hashes.txt\" required for the upcoming checks.")

    # ======= FILE EXISTENCE AND VERIFICATION CHECK =======

    # A list for storing the files which have to be re-downloaded
    files_to_redownload = []

    # Check the existence of all the required files first
    for file in FILES_TO_DOWNLOAD:
        try:
            # Check if the file already exists in the OS
            with open(f"D:\\ThreatCheckerBot\\{file}", "rb") as stream:
                # Try to calculate the SHA256 Hash of the file's content
                file_hash = hashlib.sha256(stream.read()).hexdigest()

                # If the current file is "vars.env" and it's hash has been modified - skip its verification
                if file in FILE_HASHES and file == "vars.env" and file_hash != FILE_HASHES[file]:
                    console.print(f"[bold yellow][INFO][/bold yellow]: {file} is [bold green]OK[/bold green]")
                    pass
                # If there's no hash string for the current file in the FILE_HASHES dictionary
                # or the current hash of the file is different from the one stored in the FILE_HASHES dictionary
                elif file not in FILE_HASHES or file_hash != FILE_HASHES[file]:
                    # Add the current file to the "re-download" list
                    files_to_redownload.append(file)
                    # Raise the DockerBuildException exception
                    raise DockerBuildException(f"The content of the file [bold cyan]{file}[/bold cyan] was either modified or missing")
                # Else the file is OK
                else:
                    console.print(f"[bold yellow][INFO][/bold yellow]: {file} is [bold green]OK[/bold green]")
        # If the file doesn't exist
        except FileNotFoundError:
            # Warn the user about it
            console.print(f"[bold red][ERROR][/bold red]: [bold cyan]{file}[/bold cyan] is [bold red]MISSING[/bold red]")
            # Add its name to the re-download list
            files_to_redownload.append(file)
        # Handle the raised DockerBuildException
        except DockerBuildException as docker_build_exception:
            console.print(f"[bold red][ERROR][/bold red]: {docker_build_exception}. Try to re-download the file manually.")

    # ======= DOWNLOADING MISSING FILES =======

    # Prepare a list for storing missing files which have to be re-downloaded
    source_files = []

    # If the first file check shows a few missing files
    if 0 < len(files_to_redownload) < len(FILES_TO_DOWNLOAD):
        # Only the missing files will be downloaded
        source_files = files_to_redownload[:]
    elif len(files_to_redownload) == len(FILES_TO_DOWNLOAD):
        # All the required files will be downloaded
        source_files = FILES_TO_DOWNLOAD[:]

    # A variable for recounting the missing files
    missing_file_counter = 0

    # If there are missing files
    if len(source_files) != 0:
        # Pull all required files from GitHub
        for file in source_files:
            # Construct the full path to the current file
            file_url = f"{BASE_URL}/{file}"

            # Send a GET request to GitHub and save the response
            response = requests.get(file_url)
            # If the requests was successful
            if response.status_code == 200:
                try:
                    # Try to make a new folder for the source files
                    os.mkdir("D:\\ThreatCheckerBot")
                    console.print("[bold green][INFO][/bold green]: Successfully created a new folder at [bold cyan]\"D:\\ThreatCheckerBot\"[/bold cyan].")
                # If the folder already exists then skip creating it
                except FileExistsError:
                    pass

                try:
                    # Try to create a new file in the recently created folder
                    with open(f"D:\\ThreatCheckerBot\\{file}", "wb") as stream:
                        # And write the pulled file contents to it
                        stream.write(response.content)

                    # Try to read the file
                    with open(f"D:\\ThreatCheckerBot\\{file}", "rb") as stream:
                        # Calculate a SHA256 Hash string of the file content and add it to the FILE_HASHES dictionary
                        filehash = hashlib.sha256(stream.read()).hexdigest()

                        # Open the "hashes.txt" file (or create if it doesn't exist)
                        with open(f"D:\\ThreatCheckerBot\\hashes.txt", "a", encoding="utf-8") as substream:
                            # Append the current file name and its calculated hash string to the file
                            substream.write(f"{file}:{filehash}\n")

                    console.print(f"[bold green][INFO][/bold green]: Successfully pulled [bold cyan]{file}[/bold cyan] from GitHub.")
                # If the current file already exists in the folder or if it can't be found in the folder then skip it
                except (FileExistsError, FileNotFoundError) as error:
                    console.print(f"[bold yellow][WARNING][/bold yellow]: Unable to save [bold cyan]{file}[/bold cyan] from GitHub.\n{error}")
            # If not able to pull the file from GitHub then skip it
            else:
                missing_file_counter += 1
                console.print(f"[bold red][ERROR][/bold red]: Failed pulling the file [bold cyan]{file}[/bold cyan] from GitHub.")

    # If there are still missing files
    if missing_file_counter > 0:
        # Ask the user to download them manually
        console.print(f"[bold yellow][WARNING][/bold yellow]: {missing_file_counter} required file(s) were not downloaded from GitHub. Try to download them manually before proceeding.")
        # Stop the execution of the program
        return

    # ======= CHECKING THE CONTENT OF THE vars.env FILE =======

    # A variable for counting the amount of missing API Keys
    empty_token_counter = 0
    try:
        # Try to open the "vars.env" file
        with open("D:\\ThreatCheckerBot\\vars.env", "r", encoding="utf-8") as vars_file:
            # Display a dynamic task status bar in the console
            with console.status("[bold yellow][INFO][/bold yellow]: Checking the Env Vars...", spinner="dots"):
                # Read the file line-by-line
                for line in vars_file.readlines():
                    # Delete the "new line" ("\n") character in the line
                    line = line.replace("\n", "")

                    # If the line is empty
                    if line == "":
                        # Skip it
                        continue
                    else:
                        # Split the line into a list by "="
                        line = line.split("=")

                        # If the current line is an API key and its contents is empty
                        if line[0] in API_TOKENS and (line[1] == "insert_your_api_key_here" or line[1] == ""):
                            if line [0] == "TELEGRAM_BOT_TOKEN":
                                console.print(f"[bold red][ERROR][/bold red]: [bold cyan]{line[0]}[/bold cyan] must not be empty!")
                                return
                            # Update the empty API keys counter
                            empty_token_counter += 1
    # If the file doesn't exist
    except FileNotFoundError as file_not_found:
        # Display the error message in the console
        console.print(f"[bold red][ERROR][/bold red]: The file {file_not_found} was not found!")
    # Handle the other possible exceptions
    except Exception as exception:
        console.print(f"[bold red][ERROR][/bold red]: {exception}")

    # A boolean flag which indicates if a Warning message has appeared
    warning_message = False

    # If there's at least '1' empty API Key in the "vars.env" file
    if empty_token_counter > 0:
        console.print(f"[bold yellow][WARNING][/bold yellow]: {empty_token_counter} of the required API keys is empty in the \"vars.env\" file.\n")
        warning_message = True

    # If the warning message isn't empty
    if warning_message:
        user_agreement = ""
        user_answered_incorrectly = True

        while user_answered_incorrectly:
            # Ask the user for their Consent to continue the building process
            user_agreement = input("Are you sure you want to continue? [y/n]:")
            # Delete extra spaces and lowercase the user input
            user_agreement = user_agreement.lower().strip().replace(" ", "")
            # If the user input is correct
            if user_agreement in ("y", "yes", "n", "no"):
                # Break the loop
                user_answered_incorrectly = False

        # If the user answered "no"
        if user_agreement in ("n", "no"):
            # Finish the program execution
            console.print("[bold cyan][INFO][/bold cyan]: Wise decision! It's better to fill everything up and then try again.")
            return
        else:
            console.print("[bold yellow][INFO][/bold yellow]: vars.env is [bold green]OK[/bold green]")

    # ======= BUILDING A CONTAINERIZED APP =======

    # Display a dynamic task status bar in the console
    with console.status("[bold yellow][INFO][/bold yellow]: Working on the Docker container...", spinner="dots"):
        # Initialize a new client connected to the local Docker Desktop Engine
        client = docker.from_env()

        # Build a new Docker Image object
        # All the intermediate containers will be removed upon completion ("rm=True")
        image, build_logs = client.images.build(path=".", tag="threat-checker-bot:latest", rm=True)
        console.print(f"[bold yellow][INFO][/bold yellow]: Image [bold cyan]{image.tags[0]}[/bold cyan] built [bold green]successfully![/bold green]")

        # Run a new Docker Container with the Image built on the previous step
        # Detach from the container but leave it working on the background
        # The container will be removed automatically if it exists ("remove=True")
        container = client.containers.run(image="threat-checker-bot:latest", detach=True, remove=True)

    # Display the ID and the status of the current Container in the form of a table
    table = Table(title="Container Info", show_header=True)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="cyan")
    table.add_row("Container ID", container.id)
    table.add_row("Status", container.status)
    console.print(table)

    # Stop the execution of the function upon completion
    return

if __name__ == "__main__":
    try:
        # Try to build a containerized app
        docker_build_and_run()
    # If there's an error with the building process
    except docker.errors.DockerException as e:
        # Display the error message to the console
        console.print(f"[bold red][ERROR][/bold red]: Something went wrong with the connection to Docker:\n{e}\nCheck if your Docker Desktop is running!")