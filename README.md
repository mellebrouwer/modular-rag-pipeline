# Modular RAG Pipeline

This project implements a modular retrieval-augmented generation (RAG) pipeline using various components for data processing, vector storage, and answer generation.

## Setup

1. **Create a virtual environment:**

    ```sh
    python -m venv .venv
    ```

2. **Activate the virtual environment:**

    - On macOS and Linux:

        ```sh
        source .venv/bin/activate
        ```

    - On Windows:

        ```sh
        .venv\Scripts\activate
        ```

3. **Install the required packages:**
    ```sh
    pip install uv
    ```

    ```sh
    uv sync
    ```

## Running the Application

To run the application using Streamlit:

```sh
streamlit run ui.py
```

## Running Tests
To run the tests located in the test directory:
pytest test/

## Configuration
You can modify the default configuration by editing the config.yaml file. 
This file allows you to set different configurations for the Modular RAG Pipeline components

Check the existing config.yaml to help you understand.

## Create your own components
You can create your own components by following the structure of the existing base components 
in the components directory. They will automatically be populated in the streamlit UI for you to select.
You can also just include them in the config.yaml file to use them.
