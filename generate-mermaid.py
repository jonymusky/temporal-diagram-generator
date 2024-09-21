# -*- coding: utf-8 -*-
import json
import os
from typing import List, Dict

# Configuration constants
OUTPUT_EVENTS_ID = False
SCHEDULED_COLOR = "#f9f"
COMPLETED_COLOR = "#bbf"
NEXUS_COLOR = "#ffa"  # Color for Nexus operations
WORKFLOWS_DIR = "workflows_history"
OUTOUT_DIR = "mermaid_diagrams"

def escape_string(s):
    """
    Escapes special characters in strings for Mermaid compatibility.
    """
    if isinstance(s, str):
        return s.replace('"', '\\"').replace('\n', '\\n')
    return s

def generate_mermaid_code(event_data):
    mermaid_code = ["graph TD;"]
    mermaid_code.append("classDef scheduled fill:{},stroke:#333,stroke-width:2px;".format(SCHEDULED_COLOR))
    mermaid_code.append("classDef completed fill:{},stroke:#333,stroke-width:2px;".format(COMPLETED_COLOR))
    mermaid_code.append("classDef nexus fill:{},stroke:#333,stroke-width:2px;".format(NEXUS_COLOR))  # Nexus operations class
    event_count = 1
    task_index = 1
    previous_task_id = None  # Tracks the previous task to maintain flow

    for event in event_data.get("events", []):
        # Handle activity scheduled
        if event["eventType"] == "EVENT_TYPE_ACTIVITY_TASK_SCHEDULED":
            event_id = event["eventId"]
            event_time = event["eventTime"]
            activity_name = event["activityTaskScheduledEventAttributes"]["activityType"]["name"]
        
            input_data = event["activityTaskScheduledEventAttributes"]["input"]["payloads"][0]["data"]
            
            scheduled_task_id = "Task{}".format(task_index)
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
            endpoint = nexus_attributes.get("endpoint", "Unknown endpoint")
            service = nexus_attributes.get("service", "Unknown service")
            operation = nexus_attributes.get("operation", "Unknown operation")
            
            nexus_task_id_scheduled = "NexusScheduled{}".format(task_index)
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

        # Handle Nexus operation started (optional)
        elif event["eventType"] == "EVENT_TYPE_NEXUS_OPERATION_STARTED":
            event_id = event.get("eventId", "")
            operation_id = event["nexusOperationStartedEventAttributes"].get("operationId", "UnknownOperation")
            
            nexus_task_id = "NexusStart{}".format(task_index)
            mermaid_code.append('subgraph {}["Nexus Operation Started: {}"]'.format(nexus_task_id, escape_string(operation_id)))
            mermaid_code.append("class {} nexus;".format(nexus_task_id))
            if OUTPUT_EVENTS_ID:
                mermaid_code.append('eventId{}["eventId: {}"]'.format(event_count, escape_string(str(event_id))))
            mermaid_code.append("end")
            event_count += 1

            # Connect previous task to this Nexus operation
            if previous_task_id:
                mermaid_code.append("{} --> {}".format(previous_task_id, nexus_task_id))
            previous_task_id = nexus_task_id  # Update previous task

        # Handle Nexus operation completed
        elif event["eventType"] == "EVENT_TYPE_NEXUS_OPERATION_COMPLETED":
            event_id = event.get("eventId", "")
            scheduled_event_id = event["nexusOperationCompletedEventAttributes"].get("scheduledEventId", "")
            operation_id = "NexusOp{}".format(scheduled_event_id)  # Use the scheduled event ID for linking
            
            nexus_complete_id = "NexusComplete{}".format(scheduled_event_id)
            
            mermaid_code.append('subgraph {}["Nexus Operation Completed: {}"]'.format(nexus_complete_id, escape_string(scheduled_event_id)))
            mermaid_code.append("class {} nexus;".format(nexus_complete_id))
            
            if OUTPUT_EVENTS_ID:
                mermaid_code.append('eventId{}["eventId: {}"]'.format(event_count, escape_string(str(event_id))))
            
            mermaid_code.append("end")
            event_count += 1
            
            # Link the completed Nexus operation to its start event
            nexus_task_id_start = "NexusStart{}".format(scheduled_event_id)
            nexus_task_id_scheduled = "NexusScheduled{}".format(scheduled_event_id)
            if nexus_task_id_start in "\n".join(mermaid_code):
                mermaid_code.append("{} --> {}".format(nexus_task_id_start, nexus_complete_id))
            else:
                mermaid_code.append("{} --> {}".format(nexus_task_id_scheduled, nexus_complete_id))

            # Connect the previous task to the start of this Nexus operation if not linked yet
            if previous_task_id and previous_task_id != nexus_task_id_start:
                mermaid_code.append("{} --> {}".format(previous_task_id, nexus_task_id_scheduled))

            previous_task_id = nexus_complete_id  # Update previous task after completion

            task_index += 1  # Increment task index for uniqueness
                            
    return "\n".join(mermaid_code)

def process_workflows():
    for filename in os.listdir(WORKFLOWS_DIR):
        if filename.endswith(".json"):
            file_path = os.path.join(WORKFLOWS_DIR, filename)
            with open(file_path, 'r') as file:
                event_data = json.load(file)
                try:
                    mermaid_code = generate_mermaid_code(event_data)
                    output_file = os.path.join(OUTOUT_DIR, "{}.mmd".format(filename[:-5]))
                    with open(output_file, 'w') as mermaid_file:
                        mermaid_file.write(mermaid_code)
                    print("Generated Mermaid code for {} at {}".format(filename, output_file))
                except Exception as e:
                    print("Error processing {}: {}".format(filename, e))

if __name__ == "__main__":
    process_workflows()