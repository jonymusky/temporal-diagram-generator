# Temporal Diagram Generator
A tool to automate the creation of visual workflow diagrams from Temporal.IO Event History JSON data. Generates Mermaid.js diagrams, ensuring sequential activity flow and customizable appearances. Ideal for documenting and visualizing complex workflows.

# Usage

The primary script, generate_mermaid.py, processes JSON files from the workflows_history/ directory and generates Mermaid.js diagram files. Simply run the script and check the output directory for your visual diagrams.

# Example

For instance, I used the workflow history from `Temporal-money-transfer-java` [repository](https://github.com/temporal-sa/temporal-money-transfer-java/blob/2d1a7e17029290623f192cb07bb3dbe43d6c4028/workflowHistories/happy-path-ui-decoded.json)  and generated the following diagram:

![money-transfer-workflow](https://github.com/user-attachments/assets/940d1262-2b29-432d-b490-2283cd5bec11)


# Contributing

Contributions are welcome! Please fork the repository and submit pull requests with your enhancements and bug fixes.

# License

This project is licensed under the MIT License.
