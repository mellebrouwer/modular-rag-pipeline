import sys
import os

# Add the project root to sys.path so that it streamlit can be placed in subdirectory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
import streamlit as st
from component_config import ComponentConfig, Field
from controller import Controller
from ui import utilities


controller = Controller()

def main():
    """
    Main entry point for the Streamlit application.

    - Configures the Streamlit page.
    - Initializes and stores pipeline configurations (index and retrieval)
      in Streamlit's session state if they are not already present.
    - Renders three tabs in the UI:
        1. "Run" Tab: Allows the user to run the evaluation pipeline.
        2. "Index" Tab: Allows configuration of the indexing phase.
        3. "Retrieval" Tab: Allows configuration of the retrieval phase.
    """
    st.set_page_config(page_title="Modular RAG Pipeline")
    st.title("Modular RAG Pipeline")

    # Store components in session state
    if "index" not in st.session_state:
        st.session_state.index = create_components_configs("index")
    if "retrieval" not in st.session_state:
        st.session_state.retrieval = create_components_configs("retrieval")

    # Render the tabs
    tab_run, tab_index, tab_retrieval,  = st.tabs(["Run", "Index", "Retrieval"])

    with tab_run:
        render_run_tab()

    with tab_index:
        render_pipeline_config_tab("index")

    with tab_retrieval:
        render_pipeline_config_tab("retrieval")


def render_run_tab():
    """
    Render the Run tab in the Streamlit UI.
    Allows the user to provide a Q&A YAML file path and triggers evaluation.
    """
    qa_file_path = st.text_input("Path to Q&A file (YAML)", "data/catbank/questions_answers.yaml")
    if st.button("Run Evaluation"):
        results = asyncio.run(run_eval_wrapper(qa_file_path))
        if "message" in results:
            st.write(results["message"])
        display_run_result(results)

async def run_eval_wrapper(qa_path: str) -> dict:
    """
    Wrapper to asynchronously run the evaluation.

    Args:
        qa_path (str): Path to the Q&A YAML file.

    Returns:
        dict: Results from the evaluation.
    """
    results = await controller.run_evaluation(
        st.session_state.index.values(),
        st.session_state.retrieval.values(),
        qa_path
    )
    return results

def render_pipeline_config_tab(phase: str):
    """
    Render the pipeline configuration tab (e.g., Index or Retrieval).

    Args:
        phase (str): The phase to configure ("index" or "retrieval").
    """
    components = st.session_state[phase].values()
    for component in components:
        title = utilities.prettify_title(component.name)
        with st.expander(title, expanded=True):
            display_component(component)

def create_components_configs(phase: str) -> dict[str, ComponentConfig]:
    """
    Create configuration dictionaries for a specific pipeline phase.

    Args:
        phase (str): The phase to configure ("index" or "retrieval").

    Returns:
        dict[str, ComponentConfig]: A dictionary of component configurations.
    """
    config_data = utilities.load_config()
    st.session_state[phase] = {}
    return {
        component.name: component
        for component in (create_component_config(step, phase) for step in config_data.get(phase, []))
    }

def create_component_config(step: dict, phase: str) -> ComponentConfig:
    """
    Create a ComponentConfig object for a specific pipeline step.

    Args:
        step (dict): Configuration data for the step.
        phase (str): The phase of the pipeline ("index" or "retrieval").

    Returns:
        ComponentConfig: The created ComponentConfig object.
    """
    name = step["component"]
    available_implementations = controller.get_component_implementations(name)
    implementation = get_chosen_implementation(step, available_implementations)
    constructor_params = controller.get_constructor_params(name, implementation)
    resources = step.get("resources", {})
    args = step.get("args", {})
    return ComponentConfig(
        name=name,
        available_implementations=available_implementations,
        implementation=implementation,
        constructor_params=constructor_params,
        resources=resources,
        args=args,
        phase=phase,
        step=step
    )

def get_chosen_implementation(step: dict, available_implementations: list[str]) -> str:
    """
    Get the chosen implementation for a component, defaulting to the first
    available implementation if none is provided.

    Args:
        step (dict): Configuration data for the step.
        available_implementations (list[str]): List of available implementations.

    Returns:
        str: The chosen implementation.
    """
    implementation = step["implementation"]
    if implementation not in available_implementations and available_implementations:
        implementation = available_implementations[0]
        step["implementation"] = implementation
    return implementation

def get_fields(component: ComponentConfig) -> list[Field]:
    """
    Generate fields for a component based on its parameters and resources.

    Args:
        component (ComponentConfig): The component to generate fields for.

    Returns:
        list[Field]: A list of Field objects for the component.
    """
    fields = [Field(label="Implementation", type="implementation")]
    for param_name, param_type in component.constructor_params.items():
        fields.append(Field(
            label=utilities.prettify_title(param_name),
            param_name=param_name,
            param_type=param_type
        ))
    return fields

def display_component(component: ComponentConfig):
    """
    Display the fields of a component in two columns in the Streamlit UI.

    Args:
        component (ComponentConfig): The component whose fields are to be displayed.
    """
    component.fields = get_fields(component)
    field_iter = iter(component.fields)
    for field_1 in field_iter:
        col1, col2 = st.columns(2)
        with col1:
            display_field(component, field_1)
        field_2 = next(field_iter, None)
        if field_2:
            with col2:
                display_field(component, field_2)

def display_field(component: ComponentConfig, field: Field):
    """
    Display an individual field in the Streamlit UI.

    Args:
        component (ComponentConfig): The parent component of the field.
        field (Field): The field to display.
    """
    resources = ["embedding_model", "llm", "prompt"]
    if field.type == "implementation":
        display_implementation_field(component, field)
    elif field.param_name in resources:
        display_resource_field(component, field)
    else:
        display_argument_field(component, field)

def display_implementation_field(component, field):
    """
    Display the implementation dropdown for a component in Streamlit.

    Allows the user to select an implementation from the available options.
    Updates the component's implementation, constructor parameters, resources,
    and arguments when a new implementation is chosen.

    Args:
        component (ComponentConfig): The component to display the implementation field for.
        field (Field): The field object representing the implementation field.
    """
    phase = component.phase
    name = component.name
    available_implementations = controller.get_component_implementations(component.name)
    implementation = component.implementation

    # Default to the first implementation if the current one is not available
    chosen_idx = 0
    if implementation in available_implementations:
        chosen_idx = available_implementations.index(implementation)

    # Create the implementation dropdown
    chosen_implementation = st.selectbox(
        label=field.label,
        options=available_implementations,
        index=chosen_idx,
        key=f"{name}_impl"
    )

    # When the user changes the implementation, update the component and rerun
    if chosen_implementation != implementation:
        component.implementation = chosen_implementation
        component.constructor_params = controller.get_constructor_params(name, chosen_implementation)
        component.resources = {}
        component.args = {}
        st.session_state[phase][name] = component
        print(f"Updated {name} implementation to {chosen_implementation}")
        st.rerun()

def display_resource_field(component, field):
    """
    Display the resource dropdown for a component in Streamlit.

    Allows the user to select a resource (e.g., embedding model or prompt).
    Updates the component's resources when a new resource is selected.

    Args:
        component (ComponentConfig): The component to display the resource field for.
        field (Field): The field object representing the resource field.
    """
    param_name = field.param_name
    resources = component.resources
    available_resources = controller.get_resource_implementations(param_name)
    current_resource = resources.get(param_name, "")
    phase = component.phase
    name = component.name

    # Default to the first resource if the current one is not available
    default_idx = 0
    if current_resource in available_resources:
        default_idx = available_resources.index(current_resource)

    # Create the resource dropdown
    chosen_resource = st.selectbox(
        label=field.label,
        options=available_resources,
        index=default_idx,
        key=f"{name}_{param_name}"
    )

    # Update the resource if changed
    if chosen_resource != current_resource:
        component.resources = {param_name: chosen_resource}
        st.session_state[phase][name] = component
        print(f"Updated {name} {param_name} to {chosen_resource}")
        st.rerun()

def display_argument_field(component, field):
    """
    Display an argument input field for a component in Streamlit.

    Renders a number input for integer arguments or a text input for other types.
    Updates the component's arguments when a new value is entered.

    Args:
        component (ComponentConfig): The component to display the argument field for.
        field (Field): The field object representing the argument field.
    """
    param_name = field.param_name
    param_type = field.param_type
    args = component.args
    current_value = args.get(param_name, "")
    phase = component.phase
    name = component.name

    # Render the appropriate input field
    if param_type is int:
        numeric_val = int(current_value) if str(current_value).isdigit() else 0
        new_val = st.number_input(
            label=field.label,
            value=numeric_val,
            key=f"{name}_{param_name}"
        )
    else:
        new_val = st.text_input(
            label=field.label,
            value=str(current_value),
            key=f"{name}_{param_name}"
        )

    # Update the argument if changed
    if new_val != current_value:
        component.args = {param_name: new_val}
        st.session_state[phase][name] = component
        print(f"Updated {name} {param_name} to {new_val}")
        st.rerun()

def display_run_result(results: dict):
    """
    Display the results of a run evaluation in Streamlit.

    Shows key metrics such as the number of correct and incorrect answers,
    indexing latency, average retrieval latency, and total tokens processed.
    Displays the results as a success or error message based on correctness.

    Args:
        results (dict): A dictionary containing run evaluation results with keys:
            - "correct_count" (int): Number of correct results.
            - "incorrect_count" (int): Number of incorrect results.
            - "indexing_latency" (float): Time taken for indexing.
            - "avg_retrieval_latency" (float): Average time taken for retrieval.
            - "total_tokens" (int): Total tokens processed.
            - "message" (str): Additional message or summary.
    """
    correct_count = results.get("correct_count", 0)
    incorrect_count = results.get("incorrect_count", 0)
    indexing_latency = results.get("indexing_latency", 0)
    avg_retrieval_latency = results.get("avg_retrieval_latency", 0)
    total_tokens = results.get("total_tokens", 0)
    message = results.get("message", "")

    # Format the result string
    to_string = (
        f"**Message**: {message}\n\n"
        f"**Correct**: {correct_count}\n\n"
        f"**Incorrect**: {incorrect_count}\n\n"
        f"**Indexing Latency**: {indexing_latency:.4f}s\n\n"
        f"**Average Retrieval Latency**: {avg_retrieval_latency:.4f}s\n\n"
        f"**Total Tokens**: {total_tokens}"
    )

    # Display results as success or error
    if incorrect_count > 0:
        st.error(to_string)
    else:
        st.success(to_string)


if __name__ == "__main__":
    main()
