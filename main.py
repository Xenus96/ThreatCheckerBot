# A custom exception for the user's input
class DataInputError(ValueError):
    pass

# Library imports
import os
import requests
import telebot
from telebot import types
from dotenv import load_dotenv
import json
from datetime import datetime
import asyncio
import re
import ipaddress
from urllib.parse import urlparse


# Use the "dotenv" library to load the API KEY environmental variable to the 'os.environ' list
load_dotenv("vars.env")
# Prepare a variable for storing the Telegram Bot API Key
bot_token = ""

# Try to import the API KEY and save it into a variable
try:
    if os.getenv("TELEGRAM_BOT_TOKEN") is not None:
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    else:
        raise DataInputError("Bot token not found in the Environment variables")
except DataInputError as ie:
    # If the API KEY file doesn't exist then print the warning to the console
    print(f"ERROR: {ie}")


# ======= BOT CREATION & UI CONFIGURATION =======

# Create a new Telegram Bot with the extracted API KEY
bot = telebot.TeleBot(bot_token)

def get_main_menu_markup():
    """
    Create a Main navigation menu markup\n
    === Returns: ===\n
    main_menu_markup: ReplyKeyboardMarkup - A ReplyKeyboardMarkup object which holds a frame with In-App interactive buttons\n
    """
    # Create a Frame which will hold Keyboard Buttons inside the Telegram chat
    main_menu_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    # Create Button objects for each Bot's feature
    ip_button = types.KeyboardButton("🔎 IP Address")
    url_button = types.KeyboardButton("🌐 URL")
    domain_button = types.KeyboardButton("🖥️ Domain")
    file_hash_button = types.KeyboardButton("📄 File Hash")
    # Add the Buttons to the Frame. Two couples of buttons will be displayed on separate lines
    main_menu_markup.add(ip_button, url_button)
    main_menu_markup.add(domain_button, file_hash_button)

    # Return the Main Menu markup
    return main_menu_markup

def get_return_button_markup():
    """
    Create a Return navigation menu markup\n
    === Returns: ===\n
    return_button_markup: ReplyKeyboardMarkup - A ReplyKeyboardMarkup object which holds a frame with In-App interactive buttons\n
    """
    # Create a Markup for a Return button
    return_button_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    # Create the button object
    return_button = types.KeyboardButton("⬅️ Return")
    # Add the Button object to the Markup
    return_button_markup.add(return_button)

    # Return the Markup
    return return_button_markup

# Display the Main menu with the list of the Bot's available features
@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Ask the user what Indicator of Compromise they want to scan and display the Main Menu options
    bot.send_message(message.chat.id, "What do you want to scan?", parse_mode="HTML", reply_markup=get_main_menu_markup())

# Handle the "🔎 IP Address" command
@bot.message_handler(func=lambda message: message.text == "🔎 IP Address")
def send_ip(message):
    # Save the Message object for the upcoming processing. The Message holds the Return button Markup
    send_msg = bot.send_message(message.chat.id, "Paste an IP address you want to scan.\n"
                                                      "Format: IPv4\n"
                                                      "Example: 192.168.1.1", reply_markup=get_return_button_markup())
    # Invoke the "process_next_step" function to define which function to send the user to
    bot.register_next_step_handler(send_msg, process_next_step, "ip_scan")

# Handle the "🌐 URL" command
@bot.message_handler(func=lambda message: message.text == "🌐 URL")
def send_url(message):
    # Save the Message object for the upcoming processing. The Message holds the Return button Markup
    send_msg = bot.send_message(message.chat.id, "Paste a URL you want to scan.\n"
                                                      "Example: https://example.com", reply_markup=get_return_button_markup())
    # Invoke the "process_next_step" function to define which function to send the user to
    bot.register_next_step_handler(send_msg, process_next_step, "url_scan")

# Handle the "🖧 Domain" command
@bot.message_handler(func=lambda message: message.text == "🖥️ Domain")
def send_domain(message):
    # Save the Message object for the upcoming processing. The Message holds the Return button Markup
    send_msg = bot.send_message(message.chat.id, "Paste a domain you want to scan.\n"
                                                      "Example: domain.com", reply_markup=get_return_button_markup())
    # Invoke the "process_next_step" function to define which function to send the user to
    bot.register_next_step_handler(send_msg, process_next_step, "domain_scan")

# Handle the "📄 File Hash" command
@bot.message_handler(func=lambda message: message.text == "📄 File Hash")
def send_hash(message):
    # Save the Message object for the upcoming processing. The Message holds the Return button Markup
    send_msg = bot.send_message(message.chat.id, "Paste the hash string of a file you want to scan:\n"
                                                      "Formats: SHA-1, MD5 or SHA-256", reply_markup=get_return_button_markup())
    # Invoke the "process_next_step" function to define which function to send the user to
    bot.register_next_step_handler(send_msg, process_next_step, "hash_scan")

# A function which handles returning to the Main menu
@bot.message_handler(func=lambda message: message.text == "⬅️ Return")
def return_to_main(message):
    send_welcome(message)

def process_next_step(message, caller):
    """
    Navigate the user to the Scan features of the Bot.\n
    === Parameters: ===\n
    message: Message - A TeleBot Message object\n
    caller: str - The marker of the function to be called
    """
    # If the user clicks on the "⬅️ Return" button then send them to the Main Menu markup
    if message.text == "⬅️ Return":
        return_to_main(message)
        return

    # Otherwise assume that the user isn't done yet and just invoke the appropriate Scanning function again
    if caller == "ip_scan":
        # Invoke the IP Scanning function and wait for its status (either "True - Succeed" or "False - Failed")
        success = do_ip_scan(message)

        if success:
            # After each Successful IP Scan ask the user if they want to return to the Main menu or Scan a new IP
            send_msg = bot.send_message(message.chat.id, "🔄 Type a new IP address to scan:",
                                        reply_markup=get_return_button_markup())
            bot.register_next_step_handler(send_msg, process_next_step, "ip_scan")
        else:
            # If the previous IP Scan failed (e.g. due to the bad user's input) then allow the user to try again
            bot.register_next_step_handler(message, process_next_step, "ip_scan")

    elif caller == "url_scan":
        success = do_url_scan(message)

        if success:
            send_msg = bot.send_message(message.chat.id, "🔄 Type a new URL to scan:",
                                        reply_markup=get_return_button_markup())
            bot.register_next_step_handler(send_msg, process_next_step, "url_scan")
        else:
            bot.register_next_step_handler(message, process_next_step, "url_scan")

    elif caller == "domain_scan":
        success = do_domain_scan(message)

        if success:
            send_msg = bot.send_message(message.chat.id, "🔄 Type a new Domain to scan:",
                                        reply_markup=get_return_button_markup())
            bot.register_next_step_handler(send_msg, process_next_step, "domain_scan")
        else:
            bot.register_next_step_handler(message, process_next_step, "domain_scan")

    elif caller == "hash_scan":
        success = do_hash_scan(message)

        if success:
            send_msg = bot.send_message(message.chat.id, "🔄 Type a new HASH string to scan:",
                                        reply_markup=get_return_button_markup())
            bot.register_next_step_handler(send_msg, process_next_step, "hash_scan")
        else:
            bot.register_next_step_handler(message, process_next_step, "hash_scan")


# ======= HELPER FUNCTIONS =======

def get_nested(data, path, default="Not detected"):
    """
    A helper function which allows to extract nested JSON keys safely\n
    === Parameters: ===\n
    data: JSON - A JSON object which holds the Response from a Scan Service\n
    path: str - The full path to where the nested JSON key is stored in the Response JSON object\n
    default: str - The default value for the nested JSON key\n
    """
    # Split the path into a list of keys
    parts = path.split(".")

    def search(object, remaining):
        """
        Recursive helper function for searching for the specific nested "key:value"
        inside the Response JSON object\n
        === Parameters: ===\n
        object: dict, list or default datatype - The current object being inspected\n
        remaining: list - The list of path components that still need to be processed\n
        === Returns: ===\n
        The extracted value or the default value if the path doesn't exist\n
        """

        # If all Path components have been processed and the desired value has been reached AND it's not empty - return it
        if not remaining:
            if object != "" or object is not None or len(object) != 0 or object != {}:
                return object
            else:
                return default

        # Extract the next key from the remaining Path
        key = remaining[0]

        # If the current object is a dictionary
        if isinstance(object, dict):
            # If the required key doesn't exist in the current object then the requested Path is invalid
            if key not in object:
                return default

            # Continue the recurse search with the corresponding value
            return search(object[key], remaining[1:])

        # If the current object is a list
        elif isinstance(object, list):
            # If the Path explicitly specifies a list index (e.g. "data.requests.0.text") then use that element only
            if key.isdigit():
                index = int(key)

                # Prevent IndexError by verifying that the index exists
                if index > len(object):
                    return default

                # Continue the recurse search with the corresponding value
                return search(object[index], remaining[1:])

            # Otherwise, if no index was provided in the Path then search element on the list
            # until one contains the remaining Path
            for item in object:
                result = search(item, remaining)

                # If a valid result was found AND it's not empty - then return it
                if result is not default:
                    return result

            # If None of the list elements contained the requested Path then return the default value
            return default

        # If the primitive value encountered before the Path ended then return the defaul value
        return default

    # Start the recursive search from the root of the JSON object
    return search(data, parts)

def escape_special_symbols(string):
    """
    Escape all special symbols, which can cause the Telegram API
    "Can't parse the entity" error, in the provided string\n
    === Parameters: ===\n
    string: AnyType - A string where special symbols has to be escaped is expected\n
    === Returns: ===\n
    The string with escaped special symbols OR if the input data wasn't a string - unmodified input data\n
    """
    # Check if the provided data is a String
    if isinstance(string, str):
        # Split the string into a list of characters
        string = list(string)

        # Iterate through each character in the list
        for i in range(len(string)):
            # Check if the current character is a special symbol
            if string[i] in "<>&":
                # Escape this symbol by adding a backslash "\" in front of it
                string[i] = f"\\{string[i]}"

        # Transform the list back into a string and return it
        return "".join(string)

    # Otherwise return the data back as it is
    return string

async def gather_scan_results(subject_to_scan, flag):
    """
    Send asynchronous GET requests to the specified Scan Services to check the provided IP / URL / Domain / File Hash\n
    === Parameters: ===\n
    subject_to_scan: str - The actual IP / URL / Domain / File Hash to scan\n
    flag: str - The metadata which defines what scan mechanism to use
    === Returns: ===\n
    responses_data: dict - A dictionary which holds the Response JSON objects from the Scan Services
    """
    # A dictionary which will hold all scan services responses
    responses_data = {}

    # Gather Scan data for the specified IP address
    if flag == "ip_address":
        # Construct headers for the GET requests to the API Endpoints of the Scan Services
        virustotal_headers = {"accept": "application/json", "x-apikey": f"{os.getenv('VIRUSTOTAL_TOKEN')}", "content-type": "application/x-www-form-urlencoded"}
        abuseipdb_headers = {"Accept": "application/json", "Key": f"{os.getenv('ABUSEIPDB_TOKEN')}"}
        abuseipdb_querystring = {"ipAddress": subject_to_scan}

        # Create asynchronous tasks which send GET requests to the API Endpoints of the Scan Services
        virustotal_task = asyncio.to_thread(requests.get,
                                            f"{os.getenv('VIRUSTOTAL_IP_SCAN_API')}{subject_to_scan}",
                                            headers=virustotal_headers)
        abuseipdb_task = asyncio.to_thread(requests.request,
                                           method="GET",
                                           url=f"{os.getenv('ABUSEIPDB_IP_SCAN_API')}",
                                           headers=abuseipdb_headers,
                                           params=abuseipdb_querystring)
        shodan_task = asyncio.to_thread(requests.get,
                                        f"{os.getenv('SHODAN_IP_SCAN_API')}{subject_to_scan}?key={os.getenv('SHODAN_TOKEN')}")

        # Wait for all the requests to complete and then save them to the variables
        virustotal_data, abuseipdb_data, shodan_data = await asyncio.gather(virustotal_task, abuseipdb_task, shodan_task)

        # Transform the responses from VirusTotal, AbuseIPDB and Shodan into JSON objects and add them to the "responses" dictionary
        if virustotal_data.status_code == 200:
            responses_data["virustotal"] = virustotal_data.json()
        if abuseipdb_data.status_code == 200:
            responses_data["abuseipdb"] = abuseipdb_data.json()
        if shodan_data.status_code == 200:
            responses_data["shodan"] = shodan_data.json()

    # Gather Scan data for the specified URL
    elif flag == "url":
        # Construct a POST request to VirusTotal
        virustotal_headers = {"accept": "application/json", "x-apikey": f"{os.getenv('VIRUSTOTAL_TOKEN')}"}
        virustotal_payload = {"url": f"{subject_to_scan}"}
        # Import the VirusTotal API links as a list
        virustotal_api_urls = str(os.getenv("VIRUSTOTAL_URL_SCAN_API")).split("|")

        # Construct a POST request to URLScan.io
        urlscanio_headers = {"Content-Type": "application/json", "api-key": f"{os.getenv('URLSCANIO_TOKEN')}"}
        urlscanio_payload = {"url": f"{subject_to_scan}", "visibility": "public", "country": "de"}

        # Create asynchronous tasks for the URL Scans
        virustotal_scan_task = asyncio.to_thread(requests.post,
                                                 url=virustotal_api_urls[0],
                                                 data=virustotal_payload,
                                                 headers=virustotal_headers)
        urlscanio_scan_task = asyncio.to_thread(requests.post,
                                                url=str(os.getenv("URLSCANIO_URL_SCAN_API")),
                                                json=urlscanio_payload,
                                                headers=urlscanio_headers)

        # Execute the asynchronous tasks and wait for their results to be gathered and saved locally
        # As for now, these tasks will return only "ScanId" Objects which are used to retrieve the actual Results
        virustotal_scanid_object, urlscanio_scanid_object = await asyncio.gather(virustotal_scan_task, urlscanio_scan_task)

        # Try to extract the Scan IDs from the VirusTotal and URLScan.io response
        try:
            virustotal_analysis_id_encoded = virustotal_scanid_object.json()["data"]["id"]
            urlscanio_submission_status = urlscanio_scanid_object.json()["message"]
        # If the KeyError exception raises then just return an empty dictionary
        except KeyError:
            return responses_data

        # Check if the GET requests to both VirusTotal and URLScan.io are successful
        if virustotal_analysis_id_encoded and urlscanio_submission_status == "Submission successful":
            # Extract the actual ID from the received scanId object from URLScan.io
            virustotal_analysis_id_unencoded = virustotal_analysis_id_encoded.split("-")[1]
            # Extract a certain part of the VirusTotal's ScanId which allows to retrieve the cached Scan Result for a given URL
            urlscanio_analysis_id = urlscanio_scanid_object.json()["api"]

            # Construct the headers and the link for the GET request for pulling the Analysis Results from VirusTotal and URLScan.io
            virustotal_headers = {"x-apikey": f"{os.getenv('VIRUSTOTAL_TOKEN')}", "accept": "application/json"}
            urlscanio_headers = {"api-key": f"{os.getenv('URLSCANIO_TOKEN')}"}

            # Try to gather the cached scan results for the given URL from VirusTotal
            virustotal_analysis_results = await asyncio.to_thread(requests.get,
                                                url=f"{virustotal_api_urls[0]}/{virustotal_analysis_id_unencoded}",
                                                headers=virustotal_headers)

            # If there's a cached Scan Result for the given URL
            if virustotal_analysis_results.status_code == 200:
                # Add the cached Scan Result to the dictionary
                responses_data["virustotal"] = virustotal_analysis_results.json()

            # Enter the attempt loop
            for attempt in range(12):
                # If there's already a Scan Result object retrieved from the VirusTotal's cache in the "responses_data" dictionary
                if "virustotal" in responses_data:
                    # Try to gather scan results from URLScan.io (usually takes up to 30 seconds for URLScan.io to finish scanning)
                    urlscanio_analysis_results = await asyncio.to_thread(requests.get,
                                                       url=urlscanio_analysis_id,
                                                       headers=urlscanio_headers)

                    # If the Scan Result object was retrieved from URLScan.io
                    if urlscanio_analysis_results.status_code == 200:
                        # Add it to the "responses_data" dictionary
                        responses_data["urlscanio"] = urlscanio_analysis_results.json()

                # If the Scan Result object from VirusTotal is not present in the "responses_data" dictionary
                elif "virustotal" not in responses_data:
                    # Otherwise construct a new asynchronous GET request for a fresh URL scan on VirusTotal
                    new_virustotal_task = asyncio.to_thread(requests.get,
                                                            url=f"{virustotal_api_urls[1]}{virustotal_analysis_id_encoded}",
                                                            headers=virustotal_headers)
                    # Construct a new asynchronous GET request to URLScan.io
                    urlscanio_task = asyncio.to_thread(requests.get,
                                                       url=urlscanio_analysis_id,
                                                       headers=urlscanio_headers)

                    # Try to gather Scan Results from both VirusTotal and URLScan.io in parallel
                    virustotal_analysis_results, urlscanio_analysis_results = await asyncio.gather(new_virustotal_task, urlscanio_task)

                    # Extract the status code of the response from VirusTotal (it can be "in-progress", "completed" or "failed")
                    virustotal_status_code = virustotal_analysis_results.json()["data"]["attributes"]["status"]

                    # Check the status codes of both responses and if such responses are already present in the "responses_data" dictionary - then add them there
                    if virustotal_status_code == "completed" and "virustotal" not in responses_data:
                        responses_data["virustotal"] = virustotal_analysis_results[0].json()
                    if urlscanio_analysis_results[0].status_code == 200 and "urlscanio" not in responses_data:
                        responses_data["urlscanio"] = urlscanio_analysis_results[0].json()

                # If the responses from both Scan Services were retrieved successfully - break the loop
                if "virustotal" in responses_data and "urlscanio" in responses_data:
                    break

                # Wait for 15 seconds before the next retrieval attempt
                await asyncio.sleep(15)

    # Gather Scan data for the specified Domain address
    elif flag == "domain":
        # Construct a new GET request to the VirusTotal Domain Scan API
        virustotal_headers = {"accept": "application/json", "x-apikey": f"{os.getenv('VIRUSTOTAL_TOKEN')}"}
        # Construct a new POST request to the PulseDive Domain Scan API
        pulsedive_payload = {"value": f"{subject_to_scan}", "key": f"{os.getenv('PULSEDIVE_TOKEN')}"}

        # Construct asynchronous tasks to scan the specified Domain via VirusTotal and Pulsedive
        virustotal_task = asyncio.to_thread(requests.get,
                                            url=f"{os.getenv('VIRUSTOTAL_DOMAIN_SCAN_API')}{subject_to_scan}",
                                            headers=virustotal_headers)
        pulsedive_task = asyncio.to_thread(requests.post,
                                           url=f"{os.getenv("PULSEDIVE_DOMAIN_SCAN_API")}",
                                           data=pulsedive_payload)

        # Gather the Domain Scan Results from both VirusTotal and PulseDive.
        # PulseDive returns a QID string which is used to GET the actual Scan Results
        virustotal_analysis_results, pulsedive_query_id = await asyncio.gather(virustotal_task, pulsedive_task)

        # Check if VirusTotal returns the Scan Results for the given domain. If it is then add the Scan Results to the dictionary
        if virustotal_analysis_results.status_code == 200 and not virustotal_analysis_results.json().get("error") and "virustotal" not in responses_data:
            responses_data["virustotal"] = virustotal_analysis_results.json()

        # Extract the QID string from PulseDive
        pulsedive_query_id = pulsedive_query_id.json().get("qid")

        # Enter the attempt loop
        for attempt in range(10):
            # Construct the params for the asynchronous GET request to PulseDive to gather the Scan Results
            pulsedive_params = {"qid": f"{pulsedive_query_id}", "key": f"{os.getenv('PULSEDIVE_TOKEN')}"}

            # Send the GET request to PulseDive and gather the Scan Results, and transform them into a JSON object
            pulsedive_analysis_results = await asyncio.to_thread(requests.get,
                                               url=f"{os.getenv("PULSEDIVE_DOMAIN_SCAN_API")}",
                                               params=pulsedive_params)

            try:
                # Try to extract the status code of the Scan Results
                pulsedive_status_code = pulsedive_analysis_results.json().get("status")

                # If the status code is "done" and the Scan Results are not present in the "responses_data" dictionary
                if pulsedive_status_code == "done" and not pulsedive_analysis_results.json().get("error") and "pulsedive" not in responses_data:
                    responses_data["pulsedive"] = pulsedive_analysis_results.json()
                    break

            # If the Key "status" isn't present in the PulseDive's response then the Scan Results are not ready yet
            except KeyError as ke:
                print(f"A KeyError occurred: {ke}")

            # Wait for 5 seconds before the next retrieval attempt
            await asyncio.sleep(5)


    # Gather Scan data for the specified Hash string of a file
    elif flag == "filehash":
        # Prepare the headers and the payload for new GET and POST requests to the Scan Services
        virustotal_headers = {"accept": "application/json", "x-apikey": f"{os.getenv('VIRUSTOTAL_TOKEN')}"}
        malware_bazaar_payload = {"query": "get_info", "hash": f"{subject_to_scan}"}
        malware_bazaar_headers = {"Auth-Key": f"{os.getenv('MALWARE_BAZAAR_TOKEN')}"}

        # Construct asynchronous tasks to retrieve the Scan Results
        virustotal_task = asyncio.to_thread(requests.get,
                                            url=f"{os.getenv('VIRUSTOTAL_HASH_SCAN_API')}{subject_to_scan}",
                                            headers=virustotal_headers)
        malware_bazaar_task = asyncio.to_thread(requests.post,
                                                url=f"{os.getenv('MALWARE_BAZAAR_HASH_SCAN_API')}",
                                                data=malware_bazaar_payload,
                                                headers=malware_bazaar_headers)

        # Execute the asynchronous tasks and gather their results
        virustotal_scan_results, malware_bazaar_results = await asyncio.gather(virustotal_task, malware_bazaar_task)

        # If the result from VirusTotal is valid (i.e. has the HTTP status code "200 OK")
        if virustotal_scan_results.status_code == 200:
            # Add the gathered Response object to the "responses_data" dictionary
            responses_data["virustotal"] = virustotal_scan_results.json()

        # If the result from Malware Bazaar is valid (i.e. has the HTTP code "200 OK" and the Response "query_status" field set to "ok")
        if malware_bazaar_results.json().get("query_status") == "ok" and malware_bazaar_results.status_code == 200:
            # Add the gathered Response object to the dictionary
            responses_data["malware_bazaar"] = malware_bazaar_results.json()

    # Return the dictionary with all responses
    return responses_data

def generate_final_report(responses_data, report_titles, report_header, flag):
    """
    Generate the Final Report for the given Indicator of Compromise.\n
    === Parameters: ===\n
    responses_data: dict - The Responses data which was generated by the Scan Services' APIs.\n
    report_titles: dict - The dictionary which holds the "title:json_value_to_extract" mapping for the construction of the Final Report.\n
    report_header: str - The Header for the Final Report.\n
    flag: str - The name of the function caller.\n
    === Returns: ===\n
    final_report: str - The well-formatted Final Report for the AL models to assess.
    """
    # Create a variable to hold the contents of the Final Report
    final_report = report_header
    # Prepare a dictionary for storing the Final Report and the calculated Composite Risk Score [IP SCAN]
    outputs = {}
    # A variable for storing the calculated Composite Risk Score [IP SCAN]
    composite_risk_score = 0.0
    # A default value for the extracted data from the Responses
    extracted_data = "Not detected"

    # Iterate through each "key:value" pair from the "report_titles" dictionary
    for key, value in report_titles.items():
        # Look through each Response data in the "responses_data" dictionary
        for response in responses_data.values():
            try:
                # If the current Value from the "report_titles" dictionary has the "List" type
                if isinstance(value, list):
                    # Then iterate through each element of the List
                    for subvalue in value:
                        # Utilize the "get_nested" function to extract the exact data from the "responses_data" dictionary
                        extracted_data = get_nested(response, subvalue)
                        # If the data extraction is successful then break the loop
                        if extracted_data != "Not detected":
                            break
                # If the current Value from the "report_titles" dictionary is a common String
                else:
                    # Then try to extract the data associated with this String (Key) from the "responses_data" dictionary
                    extracted_data = get_nested(response, value)
                    # If the extracted data is a string then escape all special symbols in it
                    extracted_data = escape_special_symbols(extracted_data)

                # If the extracted data isn't the default "Not detected" string then break the loop
                if extracted_data != "Not detected":
                    break
            # If an unexpected ValueError or KeyError exception has been raised then handle it
            except (ValueError, KeyError) as error:
                print(f"Couldn't find the \"{key}:{value}\" pair you're searching for in the responses data.")

        # Generate the Final Report for the scanned IP Address
        if flag == "ip_scan":
            # Prepare a variable for storing an intermediate calculation result of the CRS
            votes_total = 0.0

            # If the current key equals to "Related Hostnames"
            if key == "Related Hostnames":
                # And it's a non-empty list
                if isinstance(extracted_data, list) and len(extracted_data) >= 1:
                    hostnames = ""
                    counter = 0

                    # Iterate through each hostname
                    for hostname in extracted_data:
                        counter += 1
                        # Limit the amount of hostnames displayed inside the Telegram message to "5"
                        if 5 < counter < len(extracted_data):
                            break

                        # Add each hostname to a String
                        hostnames += f"  ‣ {hostname}\n"
                    # Append the Key and the String to the Final Report
                    final_report += f"\n<b>{key}</b>:\n{hostnames}\n"
                # Otherwise display the default "Not detected" value
                else:
                    final_report += f"\n<b>{key}</b>: {extracted_data}\n"

            # If the current key equals to "Hostname Open Ports"
            elif key == "Hostname Open Ports":
                # And it's a non-empty list
                if isinstance(extracted_data, list) and len(extracted_data) >= 1:
                    # Iterate through each element of the list and add it to the "open_ports" string
                    open_ports = ""
                    for i in range(len(extracted_data)):
                        open_ports += f"{extracted_data[i]}" if i == len(extracted_data) - 1 else f"{extracted_data[i]}, "

                    # Display all tags related to the current IP
                    final_report += f"<b>{key}</b>: {open_ports}\n"
                else:
                    # Otherwise display the default "Not detected" value
                    final_report += f"<b>{key}</b>: Not detected\n"

            # If current Key equals to "JARM"
            elif key == "JARM":
                # Then format its value as an easy-to-copy code block
                final_report += f"\n<b>{key}</b>: <code>{extracted_data}</code>\n"

            # If current Key equals to "Is a Tor end node"
            elif key == "Is a Tor end node":
                final_report += f"\n<b>{key}</b>: {extracted_data}\n"

            # If the current Key equals to "IP Abuse score"
            elif key == "IP Abuse score (0 = safe; 100 = malicious)":
                # Add this title and its Key to the report
                final_report += f"<b>{key}</b>: {extracted_data}\n"

                # Start the calculation of the Composite Risk Score (CRS) for the scanned IP address
                # The formula: Score = (AbuseScore x 0.4) + (IP Votes: malicious / IP Votes: total) * 100
                composite_risk_score = int(extracted_data) * 0.4

            # If the current Key equals to "IP Votes"
            elif key == "IP Votes":
                # Transform the nested dictionary into a String, replace single quotas with double quotas in it, and transform the String back into a Dictionary with json.loads()
                # Replacing single quotas with double quotas is necessary for the json.loads() method to work properly
                extracted_data = json.loads(str(extracted_data).replace("'", "\""))

                # Prepare a Title for the nested dictionary
                final_report += f"<b>{key}</b>:\n"

                # Iterate through each "key:value" pair in the nested dictionary and print them on a separate line in the Final Report
                for subkey, subvalue in extracted_data.items():
                    if subkey == "malicious" and subvalue >= 0:
                        # Add the Title with its value to the Scan Report
                        final_report += f"  ‣ <b>{subkey.title()}</b>: {subvalue}\n"

                        # And finish the calculation of the CRS
                        # First, add the "malicious" votes to the total votes count
                        votes_total += int(subvalue)

                        # Second, calculate the final CRS in %. If the total vote count is '0' - then just add '0' to the CRS
                        composite_risk_score += (int(subvalue) / votes_total) * 100 if votes_total > 0 else 0
                    else:
                        final_report += f"  ‣ <b>{subkey.title()}</b>: {subvalue}\n"
                        # Add the "harmless" IP votes to the total vote count
                        votes_total = int(subvalue)

            # If the current Key equals to "Third-party detection"
            elif key == "Third-party detection" and extracted_data != "Not detected":
                # Extract the nested Dictionary from the list, transform it into a String, replace single quotas in it, and transform it back into a Dictionary
                extracted_data = json.loads(str(extracted_data[0]).replace("'", "\""))

                # Prepare a title for the nested Dictionary
                final_report += f"\n<b>{key}</b>:\n"

                # Iterate through the "key:value" pairs of the Dictionary
                for subkey, subvalue in extracted_data.items():
                    # If the key is "timestamp"
                    if subkey == "timestamp":
                        # Then transform its value from a timestamp into a regular date and time
                        final_report += f"  ‣ <b>{subkey.title()}</b>: {datetime.fromtimestamp(subvalue)}\n"
                    else:
                        # Add all the other key:value pairs as they are
                        final_report += f"  ‣ <b>{subkey.title()}</b>: {subvalue}\n"

            # # If the current Key equals to "Tags"
            elif key == "Tags":
                # And it's a non-empty list
                if isinstance(extracted_data, list) and len(extracted_data) >= 1:
                    # Extract all Tags from the list and append them to a String
                    tags = ""
                    for i in range(len(extracted_data)):
                        # If it's the last tag in the list
                        if i == len(extracted_data) - 1:
                            # Add it without a comma at the end
                            tags += f"{extracted_data[i]}"
                        else:
                            # Add a tag with a comma after it
                            tags += f"{extracted_data[i]}, "

                    # Display all tags related to the current IP
                    final_report += f"<b>{key}</b>: <code>{tags}</code>\n"
                else:
                    # Otherwise display the default "Not detected" value
                    final_report += f"<b>{key}</b>: Not detected\n"

            else:
                # Append all the other data to the Final Report as it is
                final_report += f"<b>{key}</b>: {extracted_data}\n"

        # Generate the Final Report for the scanned URL
        elif flag == "url_scan":
            # If current Key equals to "Categories"
            if key == "Categories":
                # If the extracted data is a non-empty dictionary
                if isinstance(extracted_data, dict) and len(extracted_data) >= 1:
                    # Create a new String to save the extracted key:value pairs to it
                    categories = ""

                    # Iterate through each key:value pair
                    for subkey, subvalue in extracted_data.items():
                        # Escape special symbols in the subvalue
                        subvalue = escape_special_symbols(subvalue)
                        # Add each Key and its cleaned Value to the String
                        categories += f"  ‣ <b>{subkey.title()}</b>: {subvalue}\n"

                    # Add all extracted categories to the Final Report
                    final_report += f"<b>{key}</b>:\n{categories}\n"
                else:
                    # Otherwise display the default "Not detected" value
                    final_report += f"<b>{key}</b>: Not detected\n"

            # If current Key equals to "Linked URLs" it actually holds a list of URLs
            elif key == "Linked URLs":
                # Check if the extracted data is a non-empty list
                if isinstance(extracted_data, list) and len(extracted_data) >= 1:
                    # Create a new string to save a certain amount of extracted URLs
                    links = ""
                    counter = 0
                    # Iterate through the list of URLs
                    for link in extracted_data:
                        counter += 1
                        # Limit the amount of URLs displayed to "2" to avoid reaching the Telegram's message character limit
                        if 2 < counter < len(extracted_data):
                            break

                        # Append each URL to a new line inside the String
                        links += f"  ‣ {link}\n"
                    # Append the Title with the String to the Final Report
                    final_report += f"\n<b>{key}</b>:\n{links}\n"
                else:
                    # Otherwise display the default "Not detected" value
                    final_report += f"<b>{key}</b>: Not detected\n"

            # If current Key equals to "Linked Domains" (it actually holds a list of Domains)
            elif key == "Linked Domains":
                # If the extracted data is a non-empty list
                if isinstance(extracted_data, list) and len(extracted_data) >= 1:
                    # Create a new String to save the extracted domains
                    domains = ""
                    counter = 0
                    # Extract each domain from the list
                    for domain in extracted_data:
                        counter += 1
                        # Limit the amount of Domains displayed in the Telegram message to "5" (due to the Telegram's message length limit)
                        if 5 < counter < len(extracted_data):
                            break

                        # Add each Domain to a new line of the string
                        domains += f"  ‣ {domain}\n"

                    # Append the Key with the String to the Final Report
                    final_report += f"<b>{key}</b>:\n{domains}\n"
                else:
                    # Otherwise display the default "Not detected" value
                    final_report += f"<b>{key}</b>: Not detected\n"

            # If current Key equals to "Linked URL IPs"
            elif key == "Linked IPs":
                # And it's a non-empty list
                if isinstance(extracted_data, list) and len(extracted_data) >= 1:
                    # Create a new String to save all extracted IPs
                    ips = ""
                    counter = 0

                    # Iterate through each IP address and add it to the String
                    for ip in extracted_data:
                        counter += 1

                        # Limit the amount of IPs displayed in the Final Report to "6"
                        if 6 < counter < len(extracted_data):
                            break

                        # Add current IP to the String
                        ips += f"  ‣ {ip}\n"

                    # Append the Key and the String to the Final Report
                    final_report += f"<b>{key}</b>:\n{ips}"
                else:
                    # Otherwise display the default "Not detected" value
                    final_report += f"<b>{key}</b>: Not detected\n"

            # If current Key equals to "TLS Certificates"
            elif key == "TLS Certificates":
                # And it's a non-empty dictionary
                if isinstance(extracted_data, list) and len(extracted_data) >= 1:
                    certs = ""
                    counter = 0

                    # Iterate through each certificate
                    for certificate in extracted_data:
                        counter += 1
                        # Limit the amount of TLS Certs displayed in the Telegram message to "3"
                        if 3 < counter < len(extracted_data):
                            break

                        # If current certificate is a dictionary
                        if isinstance(certificate, dict):
                            # Iterate through each item of the certificate
                            for subkey, subvalue in certificate.items():
                                # If the subkey is a Linux timestamp then transform it to a readable date and time
                                if subkey == "validFrom" or subkey == "validTo":
                                    subvalue = datetime.fromtimestamp(subvalue)

                                # Escape all special symbols in the subvalue
                                subvalue = escape_special_symbols(subvalue)

                                # Add each item of the certificate to a new line of the String
                                certs += f"  ‣ <b>{subkey.title()}</b>: {subvalue}\n"

                    # Append the Key and the String to the Final Report
                    final_report += f"\n<b>{key}</b>:\n{certs}\n"
                else:
                    # Otherwise display the default "Not detected" value
                    final_report += f"<b>{key}</b>: {extracted_data}\n"

            # If current Key equals to "URL Votes"
            elif key == "URL Votes":
                # If the extracted data is a non-empty dictionary
                if isinstance(extracted_data, dict) and len(extracted_data) >= 1:
                    # Iterate through each vote category
                    for subkey, subvalue in extracted_data.items():
                        # Escape special symbols in it
                        subvalue = escape_special_symbols(subvalue)
                        # And then add it to the Final Report
                        final_report += f"  ‣ <b>{subkey.title()}</b>: {subvalue}\n"
                else:
                    # Otherwise display the default "Not detected" value
                    final_report += f"<b>{key}</b>: {extracted_data}\n"

            # If current Key equals to "Community Verdicts" (which is actually a dictionary)
            elif key == "Community Verdicts":
                # If the extracted data is a non-empty dictionary
                if isinstance(extracted_data, dict) and len(extracted_data) >= 1:
                    community_verdicts = ""

                    # Iterate through all community verdicts
                    for verdict_name, data in extracted_data.items():
                        # Add a title to each Community Verdict
                        community_verdicts += f"{verdict_name}\n"

                        # Escape all special symbols in the "data" variable, if it's a string
                        data = escape_special_symbols(data)

                        # If the "data" variable is a dictionary
                        if isinstance(data, dict):
                            # Iterate through each key:value pair in the dictionary
                            for subkey, subvalue in data.items():
                                # Escape all special symbols in the current value
                                subvalue = escape_special_symbols(subvalue)

                                # Add only those key:value pairs to the String which are not empty and are not forbidden
                                if subkey not in ["hasVerdicts", "brands"] and (subvalue != [] or subvalue != 0):
                                    community_verdicts += f"{subkey.title()}: {subvalue}\n"
                else:
                    # Otherwise display the default "Not detected" value
                    final_report += f"<b>{key}</b>: {extracted_data}\n"
            else:
                # Add all the other keys as they are
                final_report += f"<b>{key}</b>: {extracted_data}\n"

        # Generate the Final Report for the scanned Domain
        elif flag == "domain_scan":
            # If the current Key equals to "Creation Date"
            if key == "Creation Date":
                # And it doesn't hold the default value
                if extracted_data != "Not detected":
                    # Transform the Linux timestamp stored inside the Value into a standard date and time
                    final_report += f"<b>{key}</b>: {datetime.fromtimestamp(extracted_data)}\n"
                else:
                    # Otherwise just display the default value
                    final_report += f"<b>{key}</b>: {extracted_data}\n"

            # If the current Key equals to "JARM"
            elif key == "JARM":
                # And it doesn't hold the default value
                if extracted_data != "Not detected":
                    # Format it as a code block which is easy to copy
                    final_report += f"\n<b>{key}</b>: <code>{extracted_data}</code>\n"
                else:
                    # Otherwise just display the default value
                    final_report += f"\n<b>{key}</b>: {extracted_data}\n"

            # If the current Key equals to "Alternative Names"
            elif key == "Alternative Names":
                # And it's a list which is not empty
                if isinstance(extracted_data, list) and len(extracted_data) >= 1:
                    domains = ""
                    counter = 0

                    # Iterate through each domain in the list
                    for domain in extracted_data:
                        counter += 1

                        # Limit the amount of domains displayed inside the Telegram message to "5"
                        if 5 < counter < len(extracted_data):
                            break

                        # Add each domain to a String
                        domains += f"  ‣ {domain}\n"
                    # Append the Key and the String to the Final Report
                    final_report += f"\n<b>{key}</b>:\n{domains}\n"
                else:
                    # Otherwise just display the default value
                    final_report += f"\n<b>{key}</b>: {extracted_data}\n\n"

            # If the current Key equals to "Open Ports"
            elif key == "Open Ports":
                # And it's a dictionary which is not empty
                if isinstance(extracted_data, list) and len(extracted_data) >= 1:
                    ports = ""
                    counter = 0

                    # Iterate through each port
                    for port in extracted_data:
                        counter += 1

                        # Limit the amount of ports displayed inside the Telegram message to "9"
                        if 9 < counter < len(extracted_data):
                            break

                        # Add each port to a String
                        if port == extracted_data[-1]:
                            ports += f"{port}"
                        else:
                            ports += f"{port}, "
                    # Append the Key with the String to the Final Report
                    final_report += f"<b>{key}</b>: {ports}\n"
                else:
                    # Otherwise just display the default value
                    final_report += f"<b>{key}</b>: Not detected\n"

            # If the current Key equals to "SSL Certificates"
            elif key == "SSL Certificates":
                # And it's a dictionary which is not empty
                if isinstance(extracted_data, dict) and len(extracted_data) >= 1:
                    # Add the category title to the Telegram message
                    final_report += f"<b>{key}</b>:\n"

                    # Iterate through the key:value pairs of the SSL certificates
                    for subkey, subvalue in extracted_data.items():
                        # If the current subkey equals to "domain" and it's a list
                        if subkey == "domain" and isinstance(subvalue, list):
                            domains = ""
                            counter = 0

                            # Iterate through each domain
                            for domain in subvalue:
                                counter += 1

                                # Limit the amount of domains displayed inside the Telegram message to "5"
                                if 5 < counter < len(subvalue):
                                    break

                                # Add each domain to a String
                                domains += f"     ‣ {domain}\n"
                            # Append the titled Subkey and the String to the Final Report
                            final_report += f"<b>  ‣ {subkey.title()}</b>:\n{domains}"
                        # If the current subkey equals to "issuer"
                        elif subkey == "issuer":
                            # Extract the exact name of the Certificate Issuer by utilizing the ".find()" method, and then append it to the Final Report
                            final_report += f"  ‣ <b>{subkey.title()}</b>: {subvalue[subvalue.find("O=") + 2:subvalue.find("/", subvalue.find("O="))]}\n"
                        # If the current subkey equals to "subject"
                        elif subkey == "subject":
                            # Extract the exact name of the Certificate Subject by utilizing the ".find()" method, and then append it to the Final Report
                            final_report += f"  ‣ <b>{subkey.title()}</b>: {subvalue[subvalue.find("CN=") + 3:]}\n"
                        # If the current subkey equals to "fingerprint"
                        elif subkey == "fingerprint":
                            # Append the Fingerprint value formatted as a code block to the Final Report
                            final_report += f"  ‣ <b>{subkey.title()}</b>: <code>{subvalue}</code>\n"
                        else:
                            # Don't change the other key:value pairs of the SSL Certificates in any form
                            final_report += f"  ‣ <b>{subkey.title()}</b>: {subvalue}\n"
                else:
                    # Otherwise just display the default value
                    final_report += f"<b>{key}</b>: {extracted_data}\n"

            # If the current Key equals to "Categories"
            elif key == "Categories":
                # And it's a dictionary which is not empty
                if isinstance(extracted_data, dict) and len(extracted_data) >= 1:
                    # Add the category title to the Telegram message
                    final_report += f"\n<b>{key}</b>:\n"

                    # Iterate through each category
                    for subkey, subvalue in extracted_data.items():
                        # Append the Key and its Value to the Final Report
                        final_report += f"  ‣ <b>{subkey.title()}</b>: {subvalue}\n"
                else:
                    # Otherwise just display the default value
                    final_report += f"<b>{key}</b>: Not detected\n"

            # If the current Key equals to "Tags"
            elif key == "Tags":
                # ANd it's a list which is not empty
                if isinstance(extracted_data, list) and len(extracted_data) >= 1:
                    tags = ""
                    counter = 0

                    # Iterate through each tag
                    for tag in extracted_data:
                        counter += 1

                        # Limit the amount of tags displayed inside the Telegram message to "8"
                        if 8 < counter < len(extracted_data):
                            break

                        # Add each tag to a String
                        tags += f"{tag}"
                    # Append the Key and the String to the Final Report
                    final_report += f"\n<b>{key}</b>:\n{tags}\n"
                else:
                    # Otherwise just display the default value
                    final_report += f"\n<b>{key}</b>: Not detected\n"

            # If the current Key equals to "Total Votes"
            elif key == "Total Votes":
                # And it's a dictionary
                if isinstance(extracted_data, dict):
                    # Add the category title to the Telegram message
                    final_report += f"<b>{key}</b>:\n"

                    # Iterate through each key:value pair
                    for subkey, subvalue in extracted_data.items():
                        # Add the titled Key and its Value to the Final Report
                        final_report += f"  ‣ <b>{subkey.title()}</b>: {subvalue}\n"
                else:
                    # Otherwise just display the default value
                    final_report += f"<b>{key}</b>: {extracted_data}\n"
            # Append all the other data as it is
            else:
                final_report += f"<b>{key}</b>: {extracted_data}\n"

        # Generate the Final Report for the scanned File Hash
        elif flag == "filehash_scan":
            # If the current Key equals to "Scanned Hash"
            if key == "Scanned Hash":
                # Format its value as an easy-to-copy code block
                final_report += f"<b>{key}</b>: <code>{extracted_data}</code>\n"

            # If the current Key equals to "File Name"
            elif key == "File Name":
                # And it doesn't hold the default "Not detected" value
                if extracted_data != "Not detected":
                    # Format its value as a code block
                    final_report += f"\n<b>{key}</b>: <code>{extracted_data}</code>\n\n"
                else:
                    # Otherwise display the default "Not detected" value
                    final_report += f"<b>{key}</b>: {extracted_data}\n"

            # If the current Key equals to "File Size"
            elif key == "File Size":
                # And it doesn't hold the default "Not detected" value
                if extracted_data != "Not detected":
                    # Transform its value datatype into a Float, multiply it by 1^-6 (to transform bytes into megabytes),
                    # and display only 2 digits after the floating point
                    final_report += f"<b>{key}</b>: {float(extracted_data) * 1E-6: .2f} MB\n"
                else:
                    # Otherwise display the default "Not detected" value
                    final_report += f"<b>{key}</b>: {extracted_data}\n"

            # If the current Key equals to "Creation Date" or "First Submission Date"
            elif key == "Creation Date" or key == "First Submission Date":
                # And it doesn't hold the default "Not detected" value
                if extracted_data != "Not detected":
                    # Transform its value into a real date and time from the Linux timestamp
                    final_report += f"<b>{key}</b>: {datetime.fromtimestamp(float(extracted_data))}\n"
                else:
                    # Otherwise display the default "Not detected" value
                    final_report += f"<b>{key}</b>: {extracted_data}\n"

            # If the current Key equals to "ImpHash"
            elif key == "ImpHash":
                # And it doesn't hold the default "Not detected" value
                if extracted_data != "Not detected":
                    # Format its value as an easy-to-copy code block
                    final_report += f"\n<b>{key}</b>: <code>{extracted_data}</code>\n\n"
                else:
                    # Otherwise display the default "Not detected" value
                    final_report += f"<b>{key}</b>: {extracted_data}\n"

            # If the current Key equals to "Archive Password" and it's not "None"
            elif key == "Archive Password" and extracted_data is not None:
                # Add it to the Final Report as an easy-to-copy code block
                final_report += f"\n<b>{key}</b>: <code>{extracted_data}</code>\n\n"

            # If the current Key equals to "Threat Classification"
            elif key == "Threat Classification":
                # And it's a non-empty dictionary
                if isinstance(extracted_data, dict) and len(extracted_data) >= 1:
                    # Append the category title to the Final Report
                    final_report += f"\n<b>{key}</b>:\n"

                    # Iterate through each kev:value pair in the extracted data
                    for subkey, subvalue in extracted_data.items():
                        # If the current Key is "popular_threat_category"
                        if subkey == "popular_threat_category":
                            # And its value is a non-empty list
                            if isinstance(subvalue, list) and len(subvalue) >= 1:
                                # Append the subcategory title to the Final Report
                                final_report += "  ‣ <b>Categories:</b>\n"

                                # Iterate through each element in the list
                                for category_item in subvalue:
                                    # If the current element is a dictionary
                                    if isinstance(category_item, dict):
                                        # Export its values into a list
                                        data = list(category_item.values())
                                        # Add the elements of the list to the Final Report
                                        final_report += f"     ‣ <b>{str(data[1]).title()}</b> - {data[0]}\n"
                            else:
                                # Otherwise display the default "Not detected" value
                                final_report += "  ‣ <b>Categories:</b> Not detected\n"

                        # If the current Key is "popular_threat_name"
                        elif subkey == "popular_threat_name":
                            # And its value is a non-empty list
                            if isinstance(subvalue, list) and len(subvalue) >= 1:
                                # Append the subcategory title to the Final Report
                                final_report += "  ‣ <b>Names:</b>\n"

                                # Iterate through each element in the list
                                for threat in subvalue:
                                    # If the current element is a dictionary
                                    if isinstance(threat, dict):
                                        # Export its values into a list
                                        data = list(threat.values())
                                        # Add the list elements to the Final Report
                                        final_report += f"     ‣ <b>{str(data[1]).title()}</b> - {data[0]}\n"
                            else:
                                # Otherwise display the default "Not detected" value
                                final_report += "  ‣ <b>Names:</b> Not detected\n"
                else:
                    # Otherwise display the default "Not detected" value
                    final_report += f"<b>{key}</b>: Not detected\n\n"

            # If the current Key equals to "Sigma Analysis Summary"
            elif key == "Sigma Analysis Summary":
                # And it's a non-empty dictionary
                if isinstance(extracted_data, dict) and len(extracted_data) >= 1:
                    # Append the category title to the Final Report
                    final_report += f"\n<b>{key}</b>:\n"
                    # Iterate through each key:value pair in the dictionary
                    for rule, results in extracted_data.items():
                        # Append the current subcategory title to the Final Report
                        final_report += f"  ● <b>Rule Set</b>: {rule.title()}\n"

                        # If the Value of the current subcategory is a dictionary
                        if isinstance(results, dict):
                            # Iterate through each key:value pair in the dictionary
                            for severity, count in results.items():
                                # Add the pair to the Final Report
                                final_report += f"     ‣ <b>{severity.title()}</b>: {count}\n"
                else:
                    # Otherwise display the default "Not detected" value
                    final_report += f"\n<b>{key}</b>: Not detected\n\n"

            # If the current Key equals to "YARA Detection Summary"
            elif key == "YARA Detection Rules":
                # And it's a non-empty list
                if isinstance(extracted_data, list) and len(extracted_data) >= 1:
                    # Append the category title to the Final Report
                    final_report += f"<b>{key}</b>:\n"
                    counter = 0

                    # Iterate through each element of the list
                    for rule in extracted_data:
                        # Limit the amount of YARA Rules displayed in the Telegram message to "5"
                        counter += 1
                        if counter > 5:
                            break

                        # If the current element is a dictionary
                        if isinstance(rule, dict):
                            # Iterate through it's key:value pairs
                            for subkey, subvalue in rule.items():
                                # Skip the "reference" key
                                if subkey != "reference":
                                    # Delete the underscore in the "rule_name" key, capitalize it and add the whole key:value pair to the Final Report
                                    if subkey == "rule_name":
                                        final_report += f"  ● <b>{subkey.title().replace("_", " ")}</b>: {subvalue}\n"
                                    # All the other key:value pairs only capitalize and add to the Final Report
                                    else:
                                        final_report += f"     ‣ <b>{subkey.title()}</b>: {subvalue}\n"
                else:
                    # Otherwise display the default "Not detected" value
                    final_report += f"\n\n<b>{key}</b>: Not detected\n"

            # If the current Key equals to "Tags"
            elif key == "Tags":
                # And it's a non-empty list
                if isinstance(extracted_data, list) and len(extracted_data) >= 1:
                    tags = ""
                    # iterate through each index of the list
                    for i in range(len(extracted_data)):
                        # If the current element is the last in the list then don't add a comma after it, else - add a comma
                        tags += f"{extracted_data[i]}" if i == len(extracted_data) - 1 else f"{extracted_data[i]}, "
                    # Add the Key and the formatted Tags to the Final Report
                    final_report += f"\n<b>{key}</b>: <code>{tags}</code>\n"
                else:
                    # Otherwise display the default "Not detected" value
                    final_report += f"\n<b>{key}</b>: Not detected\n"

            # If the current Key equals to "Total Votes"
            elif key == "Total Votes":
                # And it's a non-empty dictionary
                if isinstance(extracted_data, dict):
                    # Add the Title of the category to the Final Report
                    final_report += f"\n<b>{key}</b>:\n"
                    # Iterate through each key:value pair in the dictionary
                    for subkey, subvalue in extracted_data.items():
                        # Add the pair to the Final Report
                        final_report += f"  ‣ <b>{subkey.title()}</b>: {subvalue}\n"
                else:
                    # Otherwise display the default "Not detected" value
                    final_report += f"\n<b>{key}</b>: Not detected\n"

            # Append all the other Final Report categories as they are
            else:
                final_report += f"<b>{key}</b>: {extracted_data}\n"


    # If the Final Report was generated for an IP Address
    if flag == "ip_scan":
        # Add the formatted report and the Composite Risk Score to the "output" dictionary
        outputs["final_report"] = final_report
        outputs["composite_risk_score"] = composite_risk_score
        # Return the "outputs" dictionary
        return outputs

    # Return the Final Report
    return final_report

def get_ai_overview(scan_report):
    """
    Get a short overview of the Subject of the Scan Report from an AI model.\n
    === Parameters: ===\n
    scan_report: str - A Scan Report to be analyzed\n
    === Returns: ===\n
    ai_report_overview: str - A short Report overview for the AI model
    """
    # Get the AI Models string and split it into a list
    ai_models = str(os.getenv("AI_MODELS_QUEUE")).split("|")

    # Construct a POST request to an AI model and save its response into a variable
    # There are three specifically chosen models, one of which (the top one) is used first and the others are used only if the first (main) one doesn't respond
    # "role": "system" is to give a certain instructions to the AI and "role": "user" represents the user's standard prompts
    # A request can have NOT MORE than 3 models in its model queue
    ai_response = requests.post(url=f"{os.getenv("OPENROUTER_API_URL")}",
                                headers={"Authorization": f"Bearer {os.getenv("OPENROUTER_TOKEN")}",
                                          "Content-Type": "application/json"},
                                data=json.dumps({"models": ai_models,
                                                 "messages": [
                                                     {
                                                         "role": "system",
                                                         "content": f"{str(os.getenv("AI_SUPER_PROMPT"))}"
                                                     },
                                                     {
                                                         "role": "user",
                                                         "content": f"Here is the Scan Report to analyze: {scan_report}"}
                                                     ]}))

    # If the response has got the HTTP status "200", then extract the AI's Report overview and return it
    if ai_response.status_code == 200:
        ai_response_data = ai_response.json()
        # The AI's response text extraction is implemented according to the OpenAI's Chat Completions schema
        ai_report_overview = ai_response_data["choices"][0]["message"]["content"]
        return ai_report_overview
    else:
        # If all models don't respond - return the default "N/A"
        return "N/A"


# ======= IP SCANNING FUNCTIONALITY =======

def validate_ip(message):
    """
    Check the validity of an IP address.\n
    === Parameters: ===\n
    message: Message - a TeleBot Message object which contains an IP address to scan\n
    === Returns: ===\n
    ip_address: str - a String containing the valid IPv4 which passed the validation check\n
    """
    # Delete extra spaces from the message text
    message_content = message.text.strip()
    # Try to validate the IP
    try:
        # Create an IPv4 object from the cleaned message text
        ip_address = ipaddress.IPv4Address(message_content)

        # If the IP is Private, Loopback or Multicast - raise the DataInputError exception
        if ip_address.is_private or ip_address.is_loopback or ip_address.is_multicast:
            raise DataInputError("Private or local IP addresses can't be scanned")
        # Else if the IP isn't an IPv4 address - raise the DataInputError exception
        elif ip_address.version != 4:
            raise DataInputError("Isn't an IPv4 address")

        # Return the IPv4 address after passing the validation
        return str(ip_address)
    # If the provided message text doesn't represent a valid IP address than raise the DataInputError exception
    except DataInputError:
        raise
    except ValueError:
        raise DataInputError(f"Invalid IP address: {message_content}")

def do_ip_scan(message):
    """
    Scan the provided IP address.\n
    === Parameters: ===\n
    message: Message - a TeleBot Message object which contains an IP address to scan\n
    === Returns: ===\n
    Boolean - "True" if the scan is successful or "False" otherwise\n
    """
    # Check if the User wants to return to the Main Menu
    if message.text == "⬅️ Return":
        # If True - send the confirmation message, display the Main Menu Markup and leave the function
        bot.register_next_step_handler(message, process_next_step, "⬅️ Return")
        return

    try:
        # Validate the provided IP address
        ip_address = validate_ip(message)

        # Warn the user that the Scan Results may take some time to retrieve
        bot.send_message(message.chat.id, "️<b>⚠️ Scanning your IP Address. This may take some time!</b>", parse_mode="HTML")

        # Pause the execution of the "do_ip_scan" function until the "gather_scan_responses" function returns the Scan Reports for the given IP address
        responses = asyncio.run(gather_scan_results(ip_address, "ip_address"))

        # A dictionary with a set of "key:value" pairs which are used to generate an IP Scan Report
        # Each Key represents a Title of a new line in the Scan Report and each Value represents the full path to the specific nested key in the "responses" dictionary
        # Format: "report_new_line_title":"full_path_to_json_nested_key"
        main_keys_for_report = {"Scanned IP": "data.id", "Network": "data.attributes.network", "Domain": "data.domain", "Usage Type": "data.usageType",
                                "Owner": "data.attributes.as_owner", "Country": "data.attributes.country", "Region": "region_code", "City": "city",
                                "ASN": "data.attributes.asn", "IP Last Reported At": "data.lastReportedAt", "Related Hostnames": "hostnames", "Hostname Open Ports": "ports",
                                "JARM": "data.attributes.jarm", "Is a Tor end node": "data.isTor", "IP Reputation (negative = malicious)": "data.attributes.reputation",
                                "IP Abuse score (0 = safe; 100 = malicious)": "data.abuseConfidenceScore", "Tags": "data.attributes.tags", "IP Votes": "data.attributes.total_votes",
                                "Third-Party Detection": "data.attributes.crowdsourced_context"
                                }

        # A variable for storing the final report's structure. Currently, it holds the starting string for the report
        final_report_header = f"📃 <b>Scan Services</b>: <i>VirusTotal</i> | <i>AbuseIPDB</i> | <i>Shodan</i>\n"

        # Generate the Final Report for the given IP Address
        outputs = generate_final_report(responses, main_keys_for_report, final_report_header, flag="ip_scan")
        # Extract the Final Report and the calculated Composite Risk Score
        final_report, composite_risk_score = outputs["final_report"], float(outputs["composite_risk_score"])

        # Get an AI overview on the Subject of the Final Report
        ai_overview = get_ai_overview(final_report)

        # Add the AI overview to the Scan Report if it's not empty
        if ai_overview != "N/A":
            final_report += "\n<b>🤖 Final verdict ⚠️</b>:\n" + ai_overview

        # If the AI overview is empty then add the calculated CRS to the Scan Report
        elif ai_overview == "N/A":
            # Assess severity of the scanned IP address based on the CRS value
            if 0 <= composite_risk_score < 20:
                severity = "🟢 Informational / Benign"
            elif 20 <= composite_risk_score < 50:
                severity = "🟡 Low Risk"
            elif 50 <= composite_risk_score < 75:
                severity = "🟠 Medium Risk / Potentially Malicious"
            else:
                severity = "🔴 High / Critical Malicious Risk"
            # Construct the final message and add it to the Scan Report
            final_report += (f"\n🛡️ <b>Composite Risk Score (0 - 100)</b>:\n{composite_risk_score: .2f} ({severity})\n"
                            f"️\n️⚠️ <b>NOTE</b>: The <b>Compromise Risk Score (CRS)</b> is calculated based on the amount of <b>IP Votes</b> "
                            f"and the <b>Abuse Score</b>. Thus, if there's not enough data on the Report then <b>CRS</b> can't be trustworthy.")

        # Send the messages containing the final report to the user
        bot.send_message(message.chat.id, "✅ <b>Your scan results are ready!</b>", parse_mode="HTML")
        bot.send_message(message.chat.id, final_report, parse_mode="HTML")

        # If the IP Scan succeed then return True
        return True

    # If the IP address user entered is invalid then send an error message to the user
    except DataInputError as error:
        bot.send_message(message.chat.id, f"❌ <b>Error</b>: {error}. Try again!", parse_mode="HTML")
        # If the IP Scan failed then return False
        return False
    # Handle the other possible errors
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error: Something went wrong. Try again!", parse_mode="HTML")
        return False


# ======= URL SCANNING FUNCTIONALITY =======

def validate_url(message):
    """
    Check the validity of a URL\n
    === Parameters: ===\n
    message: Message - a TeleBot Message object which contains a URL to scan\n
    === Returns: ===\n
    parsed_url: str - a String containing the valid URL which passed the validation check\n
    """
    # Delete extra spaces from the message text
    message_content = message.text.strip()
    # If the original URL doesn't start with "https://" or "http://"
    if not (message_content.startswith("https://") or message_content.startswith("http://")):
        # Manually add the "https://" prefix
        message_content = "https://" + message_content

    # Try to deconstruct the given URL into parts with "urlparse"
    parsed_url = urlparse(message_content)

    # If the URL doesn't have the correct scheme or doesn't have the "authority" (netloc) part
    if parsed_url.scheme not in ("http", "https") or not parsed_url.netloc:
        # Raise the DataInputError exception
        raise DataInputError("Invalid URL structure")

    # Try to extract the "hostname" parameter from the URL.
    # If this parameter is present then lowercase it, otherwise - just assign an empty string
    hostname = parsed_url.hostname.lower() if parsed_url.hostname else ""
    # If there's no hostname extracted from the URL
    if not hostname or "." not in hostname:
        # Raise the DataInputError exception
        raise DataInputError("URL must contain a valid domain name")

    # Return the validated URL
    return parsed_url.geturl()

def do_url_scan(message):
    """
    Get scan reports for the specified URL.\n
    === Parameters: ===\n
    message: Message - a TeleBot Message object which contains a URL to scan\n
    === Returns: ===\n
    Boolean - "True" if the scan is successful or "False" otherwise\n
    """
    # Check if the User wants to return to the Main Menu
    if message.text == "⬅️ Return":
        # If True - send the confirmation message, display the Main Menu Markup and leave the function
        bot.register_next_step_handler(message, process_next_step, "⬅️ Return")
        return

    try:
        # Validate the provided URL
        url = validate_url(message)

        # Warn the user that the Scan Results may take some time to retrieve
        bot.send_message(message.chat.id, "️<b>⚠️ Scanning your URL. This may take some time!</b>", parse_mode="HTML")

        # Gather Scan results for the URL
        responses = asyncio.run(gather_scan_results(url, "url"))

        # If the "responses" dictionary is empty then the given URL probably cause a DNS error
        if not responses:
            raise DataInputError("The URL you typed can't be scanned (potentially due to the DNS error)")

        # A dictionary with a set of "key:value" pairs which are used to generate a URL Scan Report
        # Format: "report_new_line_title":"full_path_to_json_nested_key"
        main_keys_for_report = {
            "Scanned URL": "page.url", "Response Code": ["data.attributes.response_code", "data.attributes.last_http_response_code"],
            "Page Title": ["data.attributes.title", "data.attributes.title"], "Associated Domain": "page.domain",
            "Domain Age (days)": "page.apexDomainAgeDays", "Associated IP": "page.ip", "Network Route": "meta.processors.asn.data.0.route",
            "Server": "page.server", "Country": ["page.country", "data.attributes.proxy_country"], "City": "page.city", "ASN": "page.asn",
            "ASN Owner": "page.asnname", "Linked URLs": "lists.urls", "Linked Domains": "lists.domains", "Linked IPs": "lists.ips",
            "TLS Certificates": "lists.certificates", "Categories": "data.attributes.categories", "URL Umbrella Rank": "page.umbrellaRank",
            "URL Reputation": "data.attributes.reputation", "Is URL Malicious (\"0\" is \"Safe\")": "stats.malicious",
            "URL Votes": ["data.attributes.stats", "data.attributes.total_votes"], "Community Verdicts": "verdicts"
        }

        # A variable for storing the final report's structure. Currently, it holds the starting string for the report
        final_report_header = f"📃 <b>Scan Services</b>: <i>VirusTotal</i> | <i>URLScan</i>\n"

        # Generate the Final Report for the given URL
        final_report = generate_final_report(responses, main_keys_for_report, final_report_header, flag="url_scan")

        # Get an AI overview on the Subject of the Scan Report
        ai_overview = get_ai_overview(final_report)

        # Add the AI overview to the Scan Report if it's not empty
        if ai_overview != "N/A":
            final_report += "\n<b>🤖 Final verdict ⚠️</b>:\n" + ai_overview
        # If the AI overview is empty then add the calculated CRS to the Scan Report
        elif ai_overview == "N/A":
            pass

        # Notify the user that their Scan Results are ready
        bot.send_message(message.chat.id, "✅ <b>Your scan results are ready!</b>", parse_mode="HTML")
        bot.send_message(message.chat.id, final_report, parse_mode="HTML")

        # If the URL Scan succeed then return True
        return True

    # If the URL has an incorrect HTTP link format then send a warning message to the user and allow them to try to type a different URL
    except DataInputError as error:
        bot.send_message(message.chat.id, f"❌ <b>Error</b>: {error}. Try again!", parse_mode="HTML")
        # If the URL Scan failed then return False
        return False
    # Handle the other types of possible exceptions
    except Exception:
        bot.send_message(message.chat.id, f"❌ <b>Error</b>: Something went wrong. Try again!", parse_mode="HTML")
        return False


# ======= DOMAIN SCANNING FUNCTIONALITY =======

def validate_domain(message):
    """
    Check the validity of a Domain\n
    === Parameters: ===\n
    message: Message - a TeleBot Message object which contains a Domain to scan\n
    === Returns: ===\n
    domain: str - a String containing the valid Domain which passed the validation check\n
    """
    # Prepare a Regular Expression for the provided domain structure verification
    # Each domain has to contain only Latin letters and numbers, separated by dots.
    # Also, each domain has to have a valid Top-Level Domain (TLD) (e.g. ".com")
    domain_regex = r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"

    # Delete extra spaces from the message text
    message_content = message.text.strip()

    # Strip protocols in the Domain name
    cleaned_domain = re.sub(r"https?://", "", message_content)

    # Strip paths, ports or query parameters if the user provided a URL by accident
    domain = cleaned_domain.split("/")[0].split(":")[0].split("?")[0]

    # Check the validity of the Domain by matching it with the Regular Expression
    if not re.match(domain_regex, domain):
        # If the domain is not valid then raise the DataInputError exception
        raise DataInputError(f"Invalid domain format: {domain}")

    # Return the validated Domain
    return domain

def do_domain_scan(message):
    """
    Get scan reports for the specified domain.\n
    === Parameters: ===\n
    domain: Message - a TeleBot Message object which contains a Domain to scan\n
    === Returns: ===\n
    Boolean - "True" if the scan is successful or "False" otherwise\n
    """
    # Check if the User wants to return to the Main Menu
    if message.text == "⬅️ Return":
        # If True - send the confirmation message, display the Main Menu Markup and leave the function
        bot.register_next_step_handler(message, process_next_step, "⬅️ Return")
        return

    try:
        # Validate the provided Domain
        domain = validate_domain(message)

        # Warn the user that the Scan Results may take some time to retrieve
        bot.send_message(message.chat.id, "️<b>⚠️ Scanning your Domain. This may take some time!</b>", parse_mode="HTML")

        # Gather Scan Analysis results for the specified Domain
        responses = asyncio.run(gather_scan_results(domain, "domain"))

        # A dictionary with a set of "key:value" pairs which are used to generate a Domain Scan Report
        # Format: "report_new_line_title":"full_path_to_json_nested_key"
        main_keys_for_report = {"Scanned Domain": ["data.id", "data.umbrella_domain", "data.properties.ssl.domain"], "Response Code": "data.properties.http.++code",
                                "Creation Date": ["data.attributes.creation_date", "data.properties.whois.creation date"], "Server": "data.properties.http.server",
                                "Domain Owner": ["data.properties.geo.org", "data.properties.whois.registrant organization"], "Domain Registrar": ["data.attributes.registrar", "data.properties.whois.registrar"],
                                "Country": "data.properties.geo.country", "Host Type": "data.attributes.hosttype", "Open Ports": "data.attributes.port",
                                "JARM": "data.attributes.jarm", "Alternative Names": "data.attributes.last_https_certificate.extensions.subject_alternative_name",
                                "SSL Certificates": "data.properties.ssl", "Categories": "data.attributes.categories", "Tags": "data.attributes.tags",
                                "Domain Reputation": "data.attributes.reputation", "Domain Risk": "data.risk", "Domain Umbrella Rank": "data.umbrella_rank",
                                "Total Votes": "data.attributes.total_votes"
                                }

        # A variable for storing the final report's structure. Currently, it holds the starting string for the report
        final_report_header = f"📃 <b>Scan Services</b>: <i>VirusTotal</i> | <i>PulseDive</i>\n"

        # Generate the Final Report for the given Domain
        final_report = generate_final_report(responses, main_keys_for_report, final_report_header, flag="domain_scan")

        # Get an AI overview on the Subject of the Scan Report
        ai_overview = get_ai_overview(final_report)

        # Add the AI overview to the Scan Report if it's not empty
        if ai_overview != "N/A":
            final_report += "\n<b>🤖 Final verdict ⚠️</b>:\n" + ai_overview
        # If the AI overview is empty then add the calculated CRS to the Scan Report
        elif ai_overview == "N/A":
            pass

        # Notify the user that their Scan Results are ready
        bot.send_message(message.chat.id, "✅ <b>Your scan results are ready!</b>", parse_mode="HTML")
        bot.send_message(message.chat.id, final_report, parse_mode="HTML")

        # Return True on success
        return True

    # Error handling
    except DataInputError as error:
        bot.send_message(message.chat.id, f"❌ <b>Error</b>: {error}. Try again!", parse_mode="HTML")
        return False
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ <b>Error</b>: Something went wrong. Try again!", parse_mode="HTML")
        return False


# ======= HASH SCANNING FUNCTIONALITY =======

def validate_hash(message):
    """
    Check the validity of a File Hash\n
    === Parameters: ===\n
    message: Message - a TeleBot Message object which contains a File Hash to scan\n
    === Returns: ===\n
    filehash: str - a String containing the valid File Hash which passed the validation check\n
    """
    # A dictionary of the acceptable hash formats (MD5, SHA1 and SHA256)
    hash_patterns = {32: r"^[a-f0-9]{32}$",
                     40: r"^[a-f0-9]{40}$",
                     64: r"^[a-f0-9]{64}$"
                     }

    # Delete extra spaces from the message text
    filehash = message.text.strip().lower()
    # The length of the provided filehash string
    hash_length = len(filehash)

    # Verify the pattern of the given file hash string
    if hash_length in hash_patterns and re.match(hash_patterns[hash_length], filehash):
        # If the pattern verified then return the validated hash string
        return filehash

    # Otherwise raise the DataInputError exception
    raise DataInputError(f"Invalid hash format. Only MD5, SHA1 or SHA256 are accepted")

def do_hash_scan(message):
    """
    Get scan reports for the specified has of a file.\n
    === Parameters: ===\n
    filehash: Message - a TeleBot Message object which contains a hash string of the file to scan\n
    === Returns: ===\n
    Boolean - "True" if the scan is successful or "False" otherwise\n
    """
    # Check if the User wants to return to the Main Menu
    if message.text == "⬅️ Return":
        # If True - send the confirmation message, display the Main Menu Markup and leave the function
        bot.register_next_step_handler(message, process_next_step, "⬅️ Return")
        return

    try:
        # Validate the provided File Hash
        filehash = validate_hash(message)

        # Warn the user that the Scan Results may take some time to retrieve
        bot.send_message(message.chat.id, "️<b>⚠️ Scanning your Hash string. This may take some time!</b>", parse_mode="HTML")

        # Gather Scan Analysis results for the specified File Hash
        responses = asyncio.run(gather_scan_results(filehash, "filehash"))

        # A dictionary with a set of "key:value" pairs which are used to generate a File Hash Scan Report
        # Format: "report_new_line_title":"full_path_to_json_nested_key"
        main_keys_for_report = {"Scanned Hash": ["data.id", "data.0.sha256_hash"], "File Name": "data.0.file_name", "File Type": ["data.0.file_type", "data.attributes.type_extension"],
                                "File Type MIME": "data.0.file_type_mime", "Type Description": "data.attributes.type_description", "File Magic": "data.attributes.magic", "File Size": ["data.0.file_size", "data.attributes.size"],
                                "Origin Country": "data.0.origin_country", "File Architecture": "data.0.file_arch", "Creation Date": "data.attributes.creation_date", "First Submission Date": ["data.attributes.first_submission_date", "data.0.first_seen"],
                                "ImpHash": "data.0.imphash", "Hash Reporter": "data.0.reporter", "Reporter Comments": "data.0.comments", "Archive Password": "data.0.archive_pw", "Delivery Method": "data.0.delivery_method",
                                "Threat Classification": "data.attributes.popular_threat_classification", "Sigma Analysis Summary": "data.attributes.sigma_analysis_summary", "YARA Detection Rules": "data.0.yara_rules",
                                "Tags": ["data.attributes.tags", "data.attributes.type_tags"], "Hash Reputation": "data.attributes.reputation", "Total Votes": "data.attributes.total_votes"
                               }

        # A variable for storing the final report's structure. Currently, it holds the starting string for the report
        final_report_header = f"📃 <b>Scan Services</b>: <i>VirusTotal</i> | <i>PulseDive</i>\n"

        # Generate the Final Report for the given File Hash
        final_report = generate_final_report(responses, main_keys_for_report, final_report_header, flag="filehash_scan")

        # Get an AI overview on the Subject of the Scan Report
        ai_overview = get_ai_overview(final_report)

        # Add the AI overview to the Scan Report if it's not empty
        if ai_overview != "N/A":
            final_report += "\n<b>🤖 Final verdict ⚠️</b>:\n" + ai_overview
        # If the AI overview is empty then add the calculated CRS to the Scan Report
        elif ai_overview == "N/A":
            pass

        # Notify the user that their Scan Results are ready
        bot.send_message(message.chat.id, "✅ <b>Your scan results are ready!</b>", parse_mode="HTML")
        bot.send_message(message.chat.id, final_report, parse_mode="HTML")

        # Return True on success
        return True

    # Error handling
    except DataInputError as error:
        bot.send_message(message.chat.id, f"❌ <b>Error</b>: {error}. Try again!", parse_mode="HTML")
        return False
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ <b>Error</b>: Something went wrong. Try again!", parse_mode="HTML")
        return False

# Keep the bot awake and listening to the user's next messages
bot.infinity_polling()