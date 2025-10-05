# Brick Manager

Brick Manager is a Flask-based web application designed to help users manage Brick parts and sets. This application allows users to manually enter parts, look up part details, search for parts by set number, and print labels. It leverages the Rebrickable API to fetch part details and uses a SQLite database to manage categories locally, helping to avoid hitting API rate limits.

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Install Dependencies](#2-install-dependencies)
  - [3. Set Up the Database](#3-set-up-the-database)
  - [4. Set Environment Variables](#4-set-environment-variables)
  - [5. Run the Application](#5-run-the-application)
- [Usage](#usage)
  - [Manual Part Entry](#manual-part-entry)
  - [Part Lookup](#part-lookup)
  - [Set Search](#set-search)
  - [Print Labels](#print-labels)
  - [Load Categories](#load-categories)
- [Docker](#docker)
  - [1. Build the Docker Image](#1-build-the-docker-image)
  - [2. Run the Docker Container](#2-run-the-docker-container)
- [Running Tests](#running-tests)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Manual Part Entry**: Add or update Brick parts in the local database.
- **Part Lookup**: Search for parts by their ID and view details including location and category.
- **Set Search**: Enter a Brick set number to retrieve a list of all parts in the set.
- **Print Labels**: Generate and print labels for Brick parts with details like part number, name, category, and location.
- **Category Management**: Load and update part categories from Rebrickable to avoid hitting API rate limits.

## Prerequisites

- Python 3.8 or higher
- [Poetry](https://python-poetry.org/) (for dependency management)
- [Docker](https://www.docker.com/) (optional, for running the app in a container)

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/Brick-scanner.git
cd Brick-scanner
```

### 2. Install Dependencies
Using Poetry:

```bash
poetry install
```

### 3. Set Up the Database
Initialize the database with the following commands:

```bash
poetry run flask db init
poetry run flask db migrate -m "Initial migration."
poetry run flask db upgrade
```

### 4. Set Environment Variables
Create a `.env` file in the root directory and add the following environment variables:

```env
FLASK_APP=app.py
FLASK_ENV=development
REBRICKABLE_TOKEN=your_rebrickable_api_key
```

### 5. Run the Application
Start the Flask application:

```bash
poetry run flask run
```

The application should be accessible at http://127.0.0.1:5000.

## Usage
### Manual Part Entry
Navigate to the "Manual Entry" page from the menu to manually add or update parts in the database. Enter the part ID, location (schrank), level (fach), and box details.

### Part Lookup
Use the "Part Lookup" feature to search for parts by their ID. The application will display details such as part number, name, category, color, quantity, and location.

### Set Search
Enter a Brick set number on the "Set Search" page to retrieve a list of all parts in that set. The list includes part numbers, names, categories, colors, quantities, and locations.

### Print Labels
Labels can be generated and printed for Brick parts. The label will include details like part number, name, category, and box location.

### Load Categories
To avoid hitting the Rebrickable API rate limits, use the "Load Categories" page to preload or update part categories in the local database. This will save the categories in the database, so subsequent requests will not need to hit the API.

## Docker
### 1. Build the Docker Image
To build the Docker image:

```bash

docker build -t Brick-scanner .
```

### 2. Run the Docker Container
To run the Docker container:

```bash
docker run -p 5000:5000 Brick-scanner
```
The application should now be accessible at http://localhost:5000.

## Running Tests
You can run the test suite using Poetry:

```bash
poetry run pytest
```

This will run all the unit tests and report the results.

## Contributing
Contributions are welcome! Please follow these steps:

1. Fork this repository.
2. Create a feature branch (`git checkout -b feature/your-feature-name`).
3. Commit your changes (`git commit -m 'Add some feature'`).
4. Push to the branch (`git push origin feature/your-feature-name`).
5. Open a pull request.
6. Please make sure to update tests as appropriate.

### License
This project is licensed under the MIT License. See the LICENSE file for details.

### Explanation:

- **Introduction**: Provides an overview of the project and its purpose.
- **Table of Contents**: Lists the major sections of the README for easy navigation.
- **Features**: Summarizes the key functionalities of the application.
- **Prerequisites**: Lists the software and tools needed to set up the project.
- **Setup Instructions**: Guides users through the process of setting up the project, including cloning the repository, installing dependencies, setting up the database, and running the application.
- **Usage**: Describes how to use the various features of the application.
- **Docker**: Instructions for building and running the application using Docker.
- **Running Tests**: Explains how to run the test suite.
- **Contributing**: Provides guidelines for contributing to the project.
- **License**: Details the licensing information for the project.

Feel free to customize any part of this `README.md` file to better suit your project!