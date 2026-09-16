import requests


RETRIEVAL_URL = "http://localhost:8002/retrieve"

DOCUMENT_ID = "6c0689e5-b58c-470c-ae99-aabc6ea81961"


TEST_CASES = [
    {
        "question": "What technologies did I use in Distributed Real-time Chat System?",
        "expected_chunks": [4],
    },
    {
        "question": "How did the chat system handle database outages?",
        "expected_chunks": [4],
    },
    {
        "question": "How many virtual users did I use for load testing the chat system?",
        "expected_chunks": [4],
    },
    {
        "question": "What was the response time improvement I achieved at PatternLab?",
        "expected_chunks": [2],
    },
    {
        "question": "How did I optimize the API at PatternLab?",
        "expected_chunks": [2],
    },
    {
        "question": "What technologies are listed in my backend skills?",
        "expected_chunks": [8],
    },
    {
        "question": "What is Braino?",
        "expected_chunks": [7],
    },
    {
        "question": "What technologies did I use to build Braino?",
        "expected_chunks": [7],
    },
    {
        "question": "What is my educational background?",
        "expected_chunks": [10],
    },
    {
        "question": "What does my resume summary say about my backend experience?",
        "expected_chunks": [1],
    },
]


def retrieve(question: str, top_k: int = 5):
    response = requests.post(
        RETRIEVAL_URL,
        json={
            "query": question,
            "top_k": top_k,
            "document_id": DOCUMENT_ID,
        },
        timeout=60,
    )

    response.raise_for_status()

    return response.json()["results"]


def evaluate_case(case):
    results = retrieve(case["question"])

    retrieved_chunks = [
        result["chunk_index"]
        for result in results
    ]

    expected = set(case["expected_chunks"])

    recall_at_1 = bool(
        set(retrieved_chunks[:1]) & expected
    )

    recall_at_3 = bool(
        set(retrieved_chunks[:3]) & expected
    )

    recall_at_5 = bool(
        set(retrieved_chunks[:5]) & expected
    )

    return {
        "question": case["question"],
        "expected": list(expected),
        "retrieved": retrieved_chunks,
        "recall_at_1": recall_at_1,
        "recall_at_3": recall_at_3,
        "recall_at_5": recall_at_5,
    }


def main():
    results = []

    for case in TEST_CASES:
        result = evaluate_case(case)
        results.append(result)

        print("\nQuestion:")
        print(result["question"])

        print(f"Expected:  {result['expected']}")
        print(f"Retrieved: {result['retrieved']}")

        print(
            f"R@1={result['recall_at_1']} "
            f"R@3={result['recall_at_3']} "
            f"R@5={result['recall_at_5']}"
        )

    total = len(results)

    recall_1 = sum(r["recall_at_1"] for r in results) / total
    recall_3 = sum(r["recall_at_3"] for r in results) / total
    recall_5 = sum(r["recall_at_5"] for r in results) / total

    print("\n==============================")
    print("RETRIEVAL EVALUATION")
    print("==============================")

    print(f"Recall@1: {recall_1:.2%}")
    print(f"Recall@3: {recall_3:.2%}")
    print(f"Recall@5: {recall_5:.2%}")


if __name__ == "__main__":
    main()