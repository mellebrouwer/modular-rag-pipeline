import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio

import streamlit as st

from component_config import ComponentConfig, Field
from controller import Controller

controller = Controller()


def _prettify_title(text: str) -> str:
    """
    Splits on underscores, capitalizes each segment, then joins with space.
    e.g. 'query_transformer' -> 'Query Transformer'
    """
    return " ".join(word.capitalize() for word in text.split("_"))

def render_run_tab():
    qa_file_path = st.text_input("Path to Q&A file (YAML)", "data/catbank/questions_answers.yaml")
    if st.button("Run Evaluation"):
        results = asyncio.run(run_eval_wrapper(qa_file_path))
        if "message" in results:
            st.write(results["message"])
        display_run_result(results)

async def run_eval_wrapper(qa_path):
    results = await controller.run_evaluation(
        st.session_state.index.values(),
        st.session_state.retrieval.values(),
        qa_path
    )
    return results

def render_pipeline_config_tab(phase: str):
    """
    Renders a tab that shows pipeline config for either Index or Retrieval,
    but does not run it. Just sets up st.session_state with user choices.
    """
    components = st.session_state[phase].values()
    for component in components:
        title = _prettify_title(component.name)
        with st.expander(title, expanded=True):
            display_component(component)

def create_components_configs(phase: str) -> dict[str, ComponentConfig]:
    """Convert a phase's config into a dictionary of Component objects."""
    config_data = controller.load_config()
    st.session_state[phase] = {}
    return {
        component.name: component
        for component in (create_component_config(step, phase) for step in config_data.get(phase, []))
    }

def create_component_config(step, phase):
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


def get_chosen_implementation(step, available_implementations):
    implementation = step["implementation"]
    if implementation not in available_implementations and available_implementations:
        implementation = available_implementations[0]
        step["implementation"] = implementation
    return implementation


def display_component(component: ComponentConfig):
    component.fields = get_fields(component)
    display_component_fields(component)


def get_fields(component: ComponentConfig) -> list[Field]:
    # First field will always be the selected implementation
    fields = [Field(label="Implementation", type="implementation")]

    # Now define the rest of the fields based on resources and args
    for param_name, param_type in component.constructor_params.items():
        fields.append(Field(
            label=_prettify_title(param_name),
            param_name=param_name,
            param_type=param_type
        ))
    return fields


def display_component_fields(component):
    field_iter = iter(component.fields)
    for field_1 in field_iter:
        col1, col2 = st.columns(2)
        with col1:
            display_field(component, field_1)

        field_2 = next(field_iter, None)
        if field_2 is not None:
            with col2:
                display_field(component, field_2)


def display_field(component, field):
    resources = ["embedding_model", "llm", "prompt"]
    if field.type == "implementation":
        display_implementation_field(component, field)
    elif field.param_name in resources:
        display_resource_field(component, field)
    else:
        display_argument_field(component, field)


def display_implementation_field(component, field):
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
    param_name = field.param_name
    resources = component.resources
    available_resources = controller.get_resource_options(param_name)
    current_resource = resources.get(param_name, "")
    phase = component.phase
    name = component.name

    default_idx = 0
    if current_resource in available_resources:
        default_idx = available_resources.index(current_resource)

    chosen_resource = st.selectbox(
        label=field.label,
        options=available_resources,
        index=default_idx,
        key=f"{name}_{param_name}"
    )
    if chosen_resource != current_resource:
        component.resources = {param_name: chosen_resource}
        st.session_state[phase][name] = component
        print(f"Updated {name} {param_name} to {chosen_resource}")
        st.rerun()


def display_argument_field(component, field):
    param_name = field.param_name
    param_type = field.param_type
    args = component.args
    current_value = args.get(param_name, "")
    phase = component.phase
    name = component.name

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

    if new_val != current_value:
        component.args = {param_name: new_val}
        st.session_state[phase][name] = component
        print(f"Updated {name} {param_name} to {new_val}")
        st.rerun()


def display_run_result(results: dict):
    """Display a run summary in Streamlit."""
    correct_count = results.get("correct_count", 0)
    incorrect_count = results.get("incorrect_count", 0)
    indexing_latency = results.get("indexing_latency", 0)
    avg_retrieval_latency = results.get("avg_retrieval_latency", 0)
    total_tokens = results.get("total_tokens", 0)
    message = results.get("message", "")

    to_string = (
        f"**Message**: {message}\n\n"
        f"**Correct**: {correct_count}\n\n"
        f"**Incorrect**: {incorrect_count}\n\n"
        f"**Indexing Latency**: {indexing_latency:.4f}s\n\n"
        f"**Average Retrieval Latency**: {avg_retrieval_latency:.4f}s\n\n"
        f"**Total Tokens**: {total_tokens}"
    )

    if incorrect_count > 0:
        st.error(to_string)
    else:
        st.success(to_string)

def main():
    st.set_page_config(page_title="Modular RAG Pipeline")
    st.title("Modular RAG Pipeline")

    # Store components in session state
    if "index" not in st.session_state:
        st.session_state.index = create_components_configs("index")
    if "retrieval" not in st.session_state:
        st.session_state.retrieval = create_components_configs("retrieval")

    tab_run, tab_index, tab_retrieval = st.tabs(["Run", "Index", "Retrieval"])

    with tab_run:
        render_run_tab()

    with tab_index:
        render_pipeline_config_tab("index")

    with tab_retrieval:
        render_pipeline_config_tab("retrieval")


if __name__ == "__main__":
    main()
