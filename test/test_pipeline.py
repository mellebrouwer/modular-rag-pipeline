import copy
import pytest
import yaml
import asyncio
import time
from langchain_core.messages import HumanMessage, SystemMessage

from src.resources import prompts
from src.pipeline import Pipeline
from src.models import Query, Data
from src.resources.llms import chat_gpt_4o


@pytest.fixture
def load_qa_pairs():
    with open("data/catbank/questions_answers.yaml", "r") as f:
        return yaml.safe_load(f)


async def judge_response(system_message, human_message):
    """Use the judge LLM asynchronously to evaluate the response."""
    return await chat_gpt_4o.ainvoke([system_message, human_message])


async def evaluate_question(idx, qa, pipeline, index_data, retrieval_latencies):
    """Evaluate a single question-answer pair."""
    question_text = qa["question"]
    expected_answer = qa["answer"]

    # Run retrieval in a thread and measure latency
    query = Query(text=question_text)
    data = Data(queries=[query], index=index_data.index)
    start_time = time.perf_counter()
    retrieval_data = await asyncio.to_thread(pipeline.run_retrieval, data)
    latency = time.perf_counter() - start_time
    retrieval_latencies.append(latency)

    # Extract pipeline answer
    token_count = retrieval_data.sum_token_count()
    pipeline_answer = retrieval_data.response

    # Prepare prompt and messages
    prompt = (
        f"Question: {question_text}\n\n"
        f"Reference Answer: {expected_answer}\n\n"
        f"Pipeline Answer: {pipeline_answer}\n\n"
    )
    system_message = SystemMessage(content=prompts.system_eval)
    human_message = HumanMessage(content=prompt)

    # Call judge asynchronously
    judgment = await judge_response(system_message, human_message)

    # Process the result
    result = judgment.content.upper().strip()
    return result, token_count, pipeline_answer, question_text, expected_answer


async def run_pipeline_test(pipeline, load_qa_pairs):
    """Run a complete pipeline test."""
    # Track indexing latency
    start_time = time.perf_counter()
    index_data = await asyncio.to_thread(pipeline.run_indexing, Data())
    indexing_latency = time.perf_counter() - start_time

    retrieval_latencies = []
    tasks = [
        evaluate_question(idx, qa, pipeline, index_data, retrieval_latencies)
        for idx, qa in enumerate(load_qa_pairs, start=1)
    ]
    results = await asyncio.gather(*tasks)

    correct_count = 0
    incorrect_count = 0
    total_tokens = 0

    for judgment, token_count, pipeline_answer, question_text, expected_answer in results:
        total_tokens += token_count
        if judgment == "TRUE":
            correct_count += 1
        else:
            incorrect_count += 1
        print(f"Q: {question_text}\nRef: {expected_answer}\nPipe: {pipeline_answer}\nJudge: {judgment}\n")

    average_retrieval_latency = sum(retrieval_latencies) / len(retrieval_latencies) if retrieval_latencies else 0
    print(f"Correct: {correct_count}\nIncorrect: {incorrect_count}")
    print(f"Total Tokens Used: {total_tokens}")
    print(f"Indexing Latency: {indexing_latency:.4f} seconds")
    print(f"Average Retrieval Latency: {average_retrieval_latency:.4f} seconds")

    return correct_count, incorrect_count, total_tokens, indexing_latency, average_retrieval_latency


@pytest.mark.asyncio
async def test_pipeline(load_qa_pairs):
    pipeline = Pipeline(config_path="test/configs/config.yaml")
    correct_count, incorrect_count, *_ = await run_pipeline_test(pipeline, load_qa_pairs)
    assert incorrect_count == 0, "Some answers were judged incorrect."


@pytest.mark.parametrize("config_path", [
    "test/configs/config_embed_small.yaml",
    "test/configs/config_embed_large.yaml",
])
@pytest.mark.asyncio
async def test_pipeline_with_configs(config_path, load_qa_pairs):
    pipeline = Pipeline(config_path=config_path)
    correct_count, incorrect_count, *_ = await run_pipeline_test(pipeline, load_qa_pairs)
    assert incorrect_count == 0, "Some answers were judged incorrect."


@pytest.mark.parametrize("modifications", [
    {"chunker_name": "FixedSizeChunker", "chunk_size": 500},
    {"chunker_name": "LcSemanticChunker"},
])
@pytest.mark.asyncio
async def test_pipeline_with_dynamic_configs(modifications, load_qa_pairs):
    with open("test/configs/config.yaml", "r") as f:
        base_config = yaml.safe_load(f)

    config = copy.deepcopy(base_config)
    config.update(modifications)
    pipeline = Pipeline(config=config)
    correct_count, incorrect_count, *_ = await run_pipeline_test(pipeline, load_qa_pairs)
    assert incorrect_count == 0, "Some answers were judged incorrect."
