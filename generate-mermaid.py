# -*- coding: utf-8 -*-
import argparse
import json
import logging
import os
import sys
from typing import List, Dict

logging.basicConfig(level=logging.INFO, stream=sys.stderr,
                    format='%(asctime)s - %(levelname)s - %(message)s')


# Configuration constants
OUTPUT_EVENTS_ID = False
SCHEDULED_COLOR = "#f9f"
COMPLETED_COLOR = "#bbf"
ACTIVITY_COLOR = "#C8E6C9"  # Color for activity
NEXUS_STYLE_COLOR = "#FFF9C4"  # Specific color for styling Nexus tasks
WORKFLOWS_DIR = os.getenv("WORKFLOWS_DIR", "workflows_history")
MERMAID_DIR = os.getenv("MERMAID_DIR", "mermaid_diagrams")



def escape_string(s):
    """
    Escapes special characters in strings for Mermaid compatibility.
    """
    if isinstance(s, str):
        return s.replace('"', '\\"').replace('\n', '\\n')
    return s

def generate_mermaid_code(event_data):
    mermaid_code = ["graph TD;"]
    activity_ids = []  # To store activity task IDs
    nexus_ids = []  # To store Nexus task IDs
    event_count = 1
    task_index = 1
    previous_task_id = None  # Tracks the previous task to maintain flow
    last_nexus_task_id = None  # Tracks the last Nexus task for sequential linking

    for event in event_data.get("events", []):
        # Handle activity scheduled
        if event["eventType"] == "EVENT_TYPE_ACTIVITY_TASK_SCHEDULED":
            event_id = event["eventId"]
            event_time = event["eventTime"]
            activity_name = event["activityTaskScheduledEventAttributes"]["activityType"]["name"]

            input_data = event["activityTaskScheduledEventAttributes"]["input"]["payloads"][0]["data"]

            scheduled_task_id = "Task{}".format(task_index)
            activity_ids.append(scheduled_task_id)  # Track the activity task ID

            mermaid_code.append('subgraph {}["Activity: {}"]'.format(scheduled_task_id, escape_string(activity_name)))
            mermaid_code.append("class {} scheduled;".format(scheduled_task_id))
            if OUTPUT_EVENTS_ID:
                mermaid_code.append('eventId{}["eventId: {}"]'.format(event_count, escape_string(str(event_id))))
                mermaid_code.append('eventTime{}["eventTime: {}"]'.format(event_count, escape_string(event_time)))
            mermaid_code.append('activityTypeName{}["activityType.name: {}"]'.format(event_count, escape_string(activity_name)))

            input_subgraph = "InputData{}".format(event_count)
            mermaid_code.append('subgraph {}["Input Fields"]'.format(input_subgraph))

            if isinstance(input_data, dict):
                for key in input_data.keys():
                    mermaid_code.append('{}{}["{}"]'.format(key, event_count, escape_string(key)))
            else:
                mermaid_code.append('inputData{}["{}"]'.format(event_count, escape_string(str(input_data))))

            mermaid_code.append("end")
            mermaid_code.append("end")

            event_count += 1

            # Connect previous task to this one
            if previous_task_id:
                mermaid_code.append("{} --> {}".format(previous_task_id, scheduled_task_id))
            previous_task_id = scheduled_task_id  # Update previous task

            # Search for corresponding completed event
            for completed_event in event_data.get("events", []):
                if (completed_event["eventType"] == "EVENT_TYPE_ACTIVITY_TASK_COMPLETED" and
                        completed_event["activityTaskCompletedEventAttributes"]["scheduledEventId"] == event_id):
                    completed_event_id = completed_event["eventId"]
                    completed_event_time = completed_event["eventTime"]
                    output_data = completed_event["activityTaskCompletedEventAttributes"].get("result", {}).get("payloads", [{}])[0].get("data", {})

                    completed_task_id = "CompletedTask{}".format(task_index)
                    activity_ids.append(completed_task_id)  # Track the activity task ID

                    mermaid_code.append('subgraph {}["Completed: {}"]'.format(completed_task_id, escape_string(activity_name)))
                    mermaid_code.append("class {} completed;".format(completed_task_id))
                    if OUTPUT_EVENTS_ID:
                        mermaid_code.append('eventId{}["eventId: {}"]'.format(event_count, escape_string(str(completed_event_id))))
                        mermaid_code.append('eventTime{}["eventTime: {}"]'.format(event_count, escape_string(completed_event_time)))

                    output_subgraph = "OutputData{}".format(event_count)
                    mermaid_code.append('subgraph {}["Output Fields"]'.format(output_subgraph))

                    if isinstance(output_data, dict):
                        for key in output_data.keys():
                            mermaid_code.append('{}{}["{}"]'.format(key, event_count, escape_string(key)))
                    else:
                        mermaid_code.append('outputData{}["{}"]'.format(event_count, escape_string(str(output_data))))

                    mermaid_code.append("end")
                    mermaid_code.append("end")

                    # Connect scheduled task to completed task
                    mermaid_code.append("{} --> {}".format(scheduled_task_id, completed_task_id))

                    # Update previous task to the completed task
                    previous_task_id = completed_task_id
                    break

            task_index += 1

        # Handle Nexus operation scheduled
        elif event["eventType"] == "EVENT_TYPE_NEXUS_OPERATION_SCHEDULED":
            event_id = event.get("eventId", "")
            nexus_attributes = event["nexusOperationScheduledEventAttributes"]
            endpoint = nexus_attributes.get("endpoint", "")
            service = nexus_attributes.get("service", "")
            operation = nexus_attributes.get("operation", "")

            # Only add NexusScheduled if it contains meaningful data (endpoint, service, operation)
            if endpoint or service or operation:
                nexus_task_id_scheduled = "NexusScheduled{}".format(task_index)
                nexus_ids.append(nexus_task_id_scheduled)  # Track the Nexus task ID

                mermaid_code.append('subgraph {}["Nexus Operation Scheduled: {}"]'.format(nexus_task_id_scheduled, escape_string(operation)))
                mermaid_code.append("class {} nexus;".format(nexus_task_id_scheduled))
                mermaid_code.append('endpoint{}["endpoint: {}"]'.format(event_count, escape_string(endpoint)))
                mermaid_code.append('service{}["service: {}"]'.format(event_count, escape_string(service)))
                mermaid_code.append('operation{}["operation: {}"]'.format(event_count, escape_string(operation)))
                if OUTPUT_EVENTS_ID:
                    mermaid_code.append('eventId{}["eventId: {}"]'.format(event_count, escape_string(str(event_id))))
                mermaid_code.append("end")
                event_count += 1

                # Connect previous task to this Nexus scheduled operation
                if previous_task_id:
                    mermaid_code.append("{} --> {}".format(previous_task_id, nexus_task_id_scheduled))
                previous_task_id = nexus_task_id_scheduled  # Update previous task
                last_nexus_task_id = nexus_task_id_scheduled  # Track this as the last Nexus task for sequential linking

        # Handle Nexus operation started (optional)
        elif event["eventType"] == "EVENT_TYPE_NEXUS_OPERATION_STARTED":
            event_id = event.get("eventId", "")
            operation_id = event["nexusOperationStartedEventAttributes"].get("operationId", "")

            # Only add NexusStart if operationId is valid
            if operation_id:
                nexus_task_id = "NexusStart{}".format(task_index)
                nexus_ids.append(nexus_task_id)  # Track the Nexus start ID

                mermaid_code.append('subgraph {}["Nexus Operation Started: {}"]'.format(nexus_task_id, escape_string(operation_id)))
                mermaid_code.append("class {} nexus;".format(nexus_task_id))
                if OUTPUT_EVENTS_ID:
                    mermaid_code.append('eventId{}["eventId: {}"]'.format(event_count, escape_string(str(event_id))))
                mermaid_code.append("end")
                event_count += 1

                # Ensure sequential linking for Nexus tasks
                if last_nexus_task_id:
                    mermaid_code.append("{} --> {}".format(last_nexus_task_id, nexus_task_id))

                # Update previous task to the current Nexus task
                previous_task_id = nexus_task_id
                last_nexus_task_id = nexus_task_id  # Track this as the last Nexus task for sequential linking

        # Handle Nexus operation completed
        elif event["eventType"] == "EVENT_TYPE_NEXUS_OPERATION_COMPLETED":
            event_id = event.get("eventId", "")
            scheduled_event_id = event["nexusOperationCompletedEventAttributes"].get("scheduledEventId", "")

            # Ensure NexusComplete and NexusScheduled are valid
            if scheduled_event_id:
                nexus_complete_id = "NexusComplete{}".format(scheduled_event_id)
                nexus_ids.append(nexus_complete_id)  # Track the Nexus complete ID

                mermaid_code.append('subgraph {}["Nexus Operation Completed: {}"]'.format(nexus_complete_id, escape_string(scheduled_event_id)))
                mermaid_code.append("class {} nexus;".format(nexus_complete_id))

                if OUTPUT_EVENTS_ID:
                    mermaid_code.append('eventId{}["eventId: {}"]'.format(event_count, escape_string(str(event_id))))

                mermaid_code.append("end")
                event_count += 1

                # Ensure sequential linking for Nexus tasks
                if last_nexus_task_id:
                    mermaid_code.append("{} --> {}".format(last_nexus_task_id, nexus_complete_id))

                # Update previous task to the current Nexus task
                previous_task_id = nexus_complete_id
                last_nexus_task_id = nexus_complete_id  # Track this as the last Nexus task for sequential linking

            task_index += 1  # Increment task index for uniqueness

    # Apply styles dynamically
    for activity_id in activity_ids:
        mermaid_code.append("style {} fill:{};".format(activity_id, ACTIVITY_COLOR))

    for nexus_id in nexus_ids:
        mermaid_code.append("style {} fill:{};".format(nexus_id, NEXUS_STYLE_COLOR))

    return "\n".join(mermaid_code)


def process_workflows(input_dir, output_dir):
    for filename in os.listdir(input_dir):
        if filename.endswith(".json"):
            file_path = os.path.join(input_dir, filename)
            output_file = os.path.join(output_dir, "{}.mmd".format(filename[:-5]))
            process_history(file_path, output_file)
            logging.info("mermaid generated src={} dest={}".format(file_path, output_file))

def process_history(input_file, output_file):
    """ process """
    with open(input_file, 'r') as file:
        try:
            event_data = json.load(file)
            mermaid_code = generate_mermaid_code(event_data)
            if output_file == "-" or output_file is None:
                print(mermaid_code)
            else:
                with open(output_file, 'w') as mermaid_file:
                    mermaid_file.write(mermaid_code)
        except Exception as e:
            logging.error("Error processing {}: {}".format(input_file, e))


def main():
    parser = argparse.ArgumentParser(
                prog='GenerateMermaid',
                description='Generate Mermaid output from a Temporal history JSON. Use on either a single JSON file or on a directory of JSON histories.',
                epilog='Additional effective env vars: WORKFLOWS_DIR MERMAID_DIR')
    parser.add_argument('-f', '--file')
    parser.add_argument('-o', '--out')
    parser.add_argument('-w', '--workflows-dir')
    parser.add_argument('-m', '--mermaid-dir')

    args = parser.parse_args()
    input_dir = args.workflows_dir or WORKFLOWS_DIR
    output_dir = args.mermaid_dir or MERMAID_DIR
    if args.file:
        process_history(args.file, args.out)
    else:
        process_workflows(input_dir, output_dir)

if __name__ == "__main__":
    main()
