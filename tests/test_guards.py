import time
from src.cache import SemanticCache


def test_paraphrase_hit():
    cache = SemanticCache(threshold=0.80, use_cloud=False)
    cache.store(
        "Can I cancel my order after it has been shipped?",
        "Orders cannot be cancelled once shipped.",
        faq_id="faq_05",
    )
    res = cache.lookup("Is it possible to cancel my order after shipping?")
    assert res["hit"] is True
    assert res["faq_id"] == "faq_05"


def test_english_and_hinglish_negation_guard():
    cache = SemanticCache(threshold=0.80, use_cloud=False)
    cache.store(
        "Can I cancel my order after it has been shipped?",
        "Orders cannot be cancelled once shipped.",
        faq_id="faq_05",
    )

    eng_neg = cache.lookup("Can I not cancel my order after it has been shipped?")
    assert eng_neg["hit"] is False
    assert eng_neg["reason"] == "negation_mismatch"

    hinglish_neg = cache.lookup("Kya main order ship hone ke baad cancel nahi kar sakta?")
    assert hinglish_neg["hit"] is False


def test_pii_hygiene_blocks_storage():
    cache = SemanticCache(threshold=0.80, use_cloud=False)
    assert cache.store("Where is my order?", "Your order ORD-98231 is out for delivery.") is False
    assert cache.store("Call me back", "We will reach you at 9876543210.") is False
    assert cache.store("Email receipt", "Sent to customer@example.com.") is False


def test_ttl_eviction():
    cache = SemanticCache(threshold=0.80, ttl_seconds=1, use_cloud=False)
    cache.store("What is the return policy?", "30-day return window.")
    time.sleep(1.1)

    res = cache.lookup("What is the return policy?")
    assert res["hit"] is False
    assert res["reason"] == "expired_ttl"
    assert cache.client.count(cache.collection_name).count == 0