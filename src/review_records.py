from .record_review import InfraiClient, NonprofitRecord, decide


def main() -> None:
    records = [
        NonprofitRecord("receipt-2026-04-01", "donor_receipt", "Receipt for April donation to the food bank."),
        NonprofitRecord("receipt-2026-04-01-copy", "donor_receipt", "April food bank donation receipt for the donor."),
        NonprofitRecord("volunteer-2026-04-02", "volunteer_reminder", "Reminder: Saturday pantry volunteer shift."),
    ]
    client = InfraiClient()
    embeddings = [client.embed(record.text) for record in records]
    client.ensure_collection(len(embeddings[0]))
    client.upsert(records, embeddings)
    result = decide(records[1], client.query(embeddings[1]))
    print(f"review: {result.incoming_id} ~ {result.nearest_id} ({result.score:.2f})")


if __name__ == "__main__":
    main()
