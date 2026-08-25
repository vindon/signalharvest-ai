import json
from unittest.mock import MagicMock, patch

from schemas.signal import IntentType, RawSignal, SignalCategory, SignalSource


def _raw(idx: int = 1, text: str = "I want to switch my phone carrier.") -> RawSignal:
    return RawSignal(source=SignalSource.REDDIT, source_id=f"test_{idx}", text=text)


def _mock_resp(items: list) -> MagicMock:
    m = MagicMock()
    m.content = [MagicMock(text=json.dumps(items))]
    return m


class TestClassifyBatch:
    @patch("agents.classifier._CLIENT")
    def test_classifies_single(self, mock_client):
        from agents.classifier import _classify_batch

        s = _raw(1)
        mock_client.messages.create.return_value = _mock_resp(
            [
                {
                    "id": s.id,
                    "category": "telecom_mobile",
                    "intent_type": "churn_risk",
                    "classification_confidence": 0.9,
                    "keywords": ["switch"],
                    "competitor_mentions": ["Verizon"],
                }
            ]
        )
        results = _classify_batch([s])
        assert len(results) == 1
        assert results[0].category == SignalCategory.TELECOM_MOBILE
        assert results[0].intent_type == IntentType.CHURN_RISK
        assert results[0].classification_confidence == 0.9
        assert "Verizon" in results[0].competitor_mentions

    @patch("agents.classifier._CLIENT")
    def test_invalid_json_fallback(self, mock_client):
        from agents.classifier import _classify_batch

        s = _raw(1)
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text="NOT VALID JSON")]
        )
        results = _classify_batch([s])
        assert len(results) == 1
        assert results[0].category == SignalCategory.OTHER
        assert results[0].classification_confidence == 0.0

    @patch("agents.classifier._CLIENT")
    def test_unknown_category_fallback(self, mock_client):
        from agents.classifier import _classify_batch

        s = _raw(1)
        mock_client.messages.create.return_value = _mock_resp(
            [
                {
                    "id": s.id,
                    "category": "nonexistent_xyz",
                    "intent_type": "complaint",
                    "classification_confidence": 0.7,
                    "keywords": [],
                    "competitor_mentions": [],
                }
            ]
        )
        results = _classify_batch([s])
        assert results[0].category == SignalCategory.OTHER

    @patch("agents.classifier._CLIENT")
    def test_strips_markdown_fences(self, mock_client):
        from agents.classifier import _classify_batch

        s = _raw(1)
        wrapped = f"```json\n{json.dumps([{'id': s.id, 'category': 'fintech_credit_card', 'intent_type': 'comparison', 'classification_confidence': 0.85, 'keywords': [], 'competitor_mentions': []}])}\n```"
        mock_client.messages.create.return_value = MagicMock(content=[MagicMock(text=wrapped)])
        results = _classify_batch([s])
        assert results[0].category == SignalCategory.FINTECH_CREDIT_CARD

    @patch("agents.classifier._CLIENT")
    def test_fills_missing_with_fallback(self, mock_client):
        from agents.classifier import _classify_batch

        signals = [_raw(i) for i in range(3)]
        mock_client.messages.create.return_value = _mock_resp(
            [
                {
                    "id": signals[0].id,
                    "category": "telecom_mobile",
                    "intent_type": "complaint",
                    "classification_confidence": 0.8,
                    "keywords": [],
                    "competitor_mentions": [],
                }
            ]
        )
        results = _classify_batch(signals)
        assert len(results) == 3
        fallbacks = [r for r in results if r.id != signals[0].id]
        for r in fallbacks:
            assert r.category == SignalCategory.OTHER


class TestBatchHelper:
    def test_splits_correctly(self):
        from agents.classifier import _batch

        batches = _batch(list(range(25)), 10)
        assert len(batches) == 3
        assert [len(b) for b in batches] == [10, 10, 5]

    def test_empty_input(self):
        from agents.classifier import _batch

        assert _batch([], 10) == []

    def test_smaller_than_size(self):
        from agents.classifier import _batch

        assert _batch([1, 2, 3], 10) == [[1, 2, 3]]
