from src.record_review import NonprofitRecord, decide


def test_similar_receipt_is_sent_for_review_but_unrelated_record_is_not() -> None:
    receipt = NonprofitRecord("receipt-copy", "donor_receipt", "April donation receipt")
    assert decide(receipt, [{"id": "receipt-original", "score": 0.94}]).review is True

    reminder = NonprofitRecord("volunteer-reminder", "volunteer_reminder", "Saturday shift reminder")
    result = decide(reminder, [{"id": "campaign-report", "score": 0.31}])
    assert result.review is False
