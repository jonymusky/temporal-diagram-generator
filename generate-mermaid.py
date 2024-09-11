# -*- coding: utf-8 -*-
import json
import os
from typing import List, Dict

# Configuration constants
OUTPUT_EVENTS_ID = False
SCHEDULED_COLOR = "#f9f"
COMPLETED_COLOR = "#bbf"
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
    
    event_count = 1
    task_index = 1
    previous_task_id = None
    
    for event in event_data.get("events", []):
        if event["eventType"] == "EVENT_TYPE_ACTIVITY_TASK_SCHEDULED":
            event_id = event["eventId"]
            event_time = event["eventTime"]
            activity_name = event["activityTaskScheduledEventAttributes"]["activityType"]["name"]
        
            input_data: List[Dict] = []
            try:
                input_data = event["activityTaskScheduledEventAttributes"]["input"]["payloads"][0]["data"]
            except:
                pass
            
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
                    
                    mermaid_code.append("{} --> {}".format(scheduled_task_id, completed_task_id))
                    
                    # Connect the previous completed task to the current scheduled task
                    if previous_task_id:
                        mermaid_code.append("{} --> {}".format(previous_task_id, scheduled_task_id))
                    
                    previous_task_id = completed_task_id
                    break

            task_index += 1
                
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