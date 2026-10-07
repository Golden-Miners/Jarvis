from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from jarvis.agents.fury import FuryOutput, FurySettings, NewsClassification, run_fury


def test_run_fury_empty_feed() -> None:
    now = datetime.now(UTC)
    settings = FurySettings(rss_urls=["http://invalid.url.that.does.not.exist"])
    # The feed parser will fail to parse, resulting in empty raw_news
    impacts = run_fury(now, ["XAUUSD"], settings, llm=None)
    assert "XAUUSD" in impacts
    assert len(impacts["XAUUSD"]) == 0

@patch("jarvis.agents.fury.feedparser.parse")
def test_run_fury_with_mock_llm(mock_parse: MagicMock) -> None:
    now = datetime.now(UTC)
    
    # Mock RSS feed
    mock_feed = MagicMock()
    mock_entry = MagicMock()
    mock_entry.title = "Gold rises on inflation fears"
    mock_entry.summary = "Some summary"
    mock_feed.entries = [mock_entry]
    mock_parse.return_value = mock_feed
    
    settings = FurySettings(rss_urls=["http://mock"])
    
    # Mock LLM
    mock_llm = MagicMock()
    mock_chain = MagicMock()
    mock_llm.with_structured_output.return_value = mock_chain
    @patch("jarvis.agents.fury.ChatPromptTemplate")
    def do_test(mock_prompt_cls: MagicMock) -> None:
        mock_prompt = MagicMock()
        mock_prompt_cls.from_messages.return_value = mock_prompt
        
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = FuryOutput(
            classifications=[
                NewsClassification(
                    symbol="XAUUSD",
                    bias="BULLISH",
                    impact=8,
                    is_high_impact_event=True,
                    summary="Gold rises on inflation fears"
                )
            ]
        )
        mock_prompt.__or__.return_value = mock_chain
        
        impacts = run_fury(now, ["XAUUSD"], settings, llm=mock_llm)
        
        assert "XAUUSD" in impacts
        assert len(impacts["XAUUSD"]) == 1
        assert impacts["XAUUSD"][0].bias == "BULLISH"
        assert impacts["XAUUSD"][0].impact == 8
        assert impacts["XAUUSD"][0].blackout_until is not None
        
    do_test()
