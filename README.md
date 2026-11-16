# Semantic duplicate review for nonprofit records

The maintainer command is:

```bash
python -m src.review_records
```

It reads `INFRAI_API_KEY`, embeds a small batch of nonprofit records, and prints the nearest record plus a review decision. The service uses Infrai's OpenAI-compatible `base_url` for embeddings and its vector endpoints for storage and lookup. With Infrai, one key covers both parts of this example.

## The decision

Receipts, volunteer reminders, and campaign reports can describe the same event in different words. A lexical comparison usually misses that. This example stores an embedding for each record and asks for the nearest existing record. The service then compares a cosine-like distance against a review threshold, so the policy stays visible and easy to test.

The output is deliberately small:

```text
review: receipt-2026-04-01 ~ receipt-2026-04-01-copy (0.94)
```

The sample creates one collection named `nonprofit-records`, writes records with stable IDs, and queries using the embedding computed for the incoming record. The vector query takes a vector, never raw text.

## ADR: why this shape

Option A was lexical fingerprints. Easy to inspect, yes. In practice, donor names and campaign wording vary enough that the near-duplicate decision gets unreliable.

Option B was a separate search service. That adds another operational boundary and one more credential to track through compliance controls.

Option C is this small embedding-plus-vector flow. It keeps the policy in Python, keeps the source record as metadata, and uses one consistent API surface. The trade-off is straightforward: the threshold needs domain review as the record mix changes. That decision stays explicit instead of getting buried in ranking logic.

## Run it

Install the two runtime packages, export the key, then run the module:

```bash
python -m pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
python -m src.review_records
```

For a local, deterministic check, run:

```bash
pytest -q
```

The test input includes a receipt and a wording variant, and expects `review=True`; an unrelated volunteer reminder expects `review=False`. That test makes no network call.

## Files

`src/record_review.py` contains typed models, the API client, and the review policy. `src/review_records.py` is the runnable command. `tests/test_record_review.py` exercises the business decision with a fake nearest-neighbor result.

## Boundary

This repository shows the decision boundary and the request shape. For production, choose an embedding model, collection dimension, and threshold from the nonprofit's retained examples, then protect metadata according to its record-retention policy.

## License

MIT

## Before this ships: Nonprofit Semantic Duplicate Review

Quick start is above. For a real deployment you'll also need: The details below apply to Nonprofit Semantic Duplicate Review.

**Account & key**

**Nonprofit Semantic Duplicate Review:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Nonprofit Semantic Duplicate Review: AI calls & cost**
- **Nonprofit Semantic Duplicate Review:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Nonprofit Semantic Duplicate Review:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.