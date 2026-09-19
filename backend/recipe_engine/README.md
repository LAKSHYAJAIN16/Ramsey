# Recipe engine

Turns acquired recipe content into the structured ingredients and ordered instructions used by the session.

Read [service.py](service.py) for orchestration, [browserbase_client.py](browserbase_client.py) for acquisition, [parser.py](parser.py) for parsing, [race.py](race.py) for competing sources, and [cache.py](cache.py) for saved/demo results.

Live search needs Browserbase configuration. The bundled recipe is a labeled development fallback, not evidence of live retrieval. Offline tests cover parsing, search response handling, racing, and caching. Run `python -m pytest backend/tests/test_parser.py backend/tests/test_browserbase_search.py backend/tests/test_cache_and_service.py backend/tests/test_race.py -q` from the root.

[Backend overview](../README.md).
