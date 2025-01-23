# Artemis CLI Tool

Artemis is a versatile command-line tool designed to interact with Microsoft Azure and Microsoft Entra ID (formerly Azure Active Directory). The tool helps you retrieve and export information about users, groups, licenses, resources, and subscriptions from your Azure tenant.

## Features

- **Full Tenant Assessment**: Retrieve users, groups, licenses, and resources within your tenant.
- **Entra ID Focused Assessment**: Focus on users, groups, and licenses only.
- **Azure Resource Assessment**: Focus on Azure resources and subscriptions only.
- **CSV Export**: Export data to well-structured CSV files for further analysis.

---

## Prerequisites

1. **Python Version**: Ensure you have Python 3.8 or higher installed.
2. **Required Files**:
   - `artemis.py`: The main script for the CLI tool.
   - `artemis.db`: SQLite database used for resolving license SKU IDs to product names.
   - `LICENSE`: Licensing information for the project.
   - `pyproject.toml`: Defines the build and package details.

3. **Dependencies**: Ensure the following Python libraries are installed:
   - `click`: For command-line interface options.
   - `azure-identity`: For Azure authentication.
   - `azure-mgmt-resource`: For interacting with Azure resources.
   - `requests`: For making HTTP requests.

## Installation

1. **Build Locally**:
   - `python -m build`: The following command will build the package starting from the .toml file
2. **Install**:
   - `pip install path/to/dist/{file}.whl`: Install locally the script and use it
   
