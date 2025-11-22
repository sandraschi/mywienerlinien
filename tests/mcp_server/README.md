# MCP Server Test Suite

Comprehensive test suite for the Vienna Transit MCP Server, including unit tests and integration tests.

## Test Structure

```
tests/mcp_server/
├── conftest.py              # Shared fixtures and test configuration
├── unit/                    # Unit tests
│   ├── test_tools_*.py     # Tool function tests
│   ├── test_models.py      # Pydantic model validation tests
│   ├── test_utils.py       # Utility function tests
│   ├── test_prompts.py     # Prompt registration and content tests
│   └── test_resources.py   # Resource registration and content tests
└── integration/            # Integration tests
    ├── test_server_integration.py  # Server initialization and tool registration
    ├── test_end_to_end.py          # Complete workflow tests
    └── test_api_integration.py     # API integration and error handling
```

## Running Tests

### Run All Tests
```bash
pytest tests/mcp_server/
```

### Run Unit Tests Only
```bash
pytest tests/mcp_server/unit/
```

### Run Integration Tests Only
```bash
pytest tests/mcp_server/integration/
```

### Run Specific Test File
```bash
pytest tests/mcp_server/unit/test_tools_departures.py
```

### Run with Coverage
```bash
pytest tests/mcp_server/ --cov=frontend/mcp_server --cov-report=html
```

## Test Categories

### Unit Tests

- **Tool Tests**: Test individual tool functions with mocked dependencies
  - `test_tools_departures.py`: Next departures tool
  - `test_tools_stations.py`: Station search tool
  - `test_tools_status.py`: Line status tool
  - `test_tools_journey.py`: Journey planner tool

- **Model Tests**: Validate Pydantic model schemas and validation
  - `test_models.py`: All response models

- **Utility Tests**: Test helper functions
  - `test_utils.py`: Station search utilities

- **Prompt/Resource Tests**: Test MCP prompts and resources
  - `test_prompts.py`: Prompt registration and content
  - `test_resources.py`: Resource registration and content

### Integration Tests

- **Server Integration**: Test server initialization and tool registration
  - `test_server_integration.py`: Server setup, tool/prompt/resource registration

- **End-to-End**: Test complete workflows
  - `test_end_to_end.py`: Full user workflows (search → departures, journey planning)

- **API Integration**: Test external API interactions
  - `test_api_integration.py`: Error handling, timeouts, rate limiting

## Test Fixtures

Key fixtures available in `conftest.py`:

- `mock_mcp_server`: FastMCP server instance for testing
- `mock_data_loader`: Mocked data loader with sample stations
- `mock_vehicle_service`: Mocked vehicle service
- `mock_wiener_linien_api`: Mock API response generator
- `sample_departure_response`: Sample DepartureResponse object
- `sample_station_search_response`: Sample StationSearchResponse object
- `sample_journey_plan`: Sample JourneyPlan object
- `sample_line_status_response`: Sample LineStatusResponse object
- `mock_requests_get`: Mock for requests.get calls

## Writing New Tests

### Unit Test Example

```python
@pytest.mark.asyncio
async def test_my_tool_success(mock_data_loader):
    """Test successful tool execution."""
    with patch("mcp_server.tools.my_tool.data_loader", mock_data_loader):
        # Test implementation
        result = await my_tool_function(param="value")
        assert result is not None
```

### Integration Test Example

```python
@pytest.mark.asyncio
async def test_workflow():
    """Test complete workflow."""
    from mcp_server.server import mcp
    
    # Step 1: Search station
    station_search = mcp._tools["station_search"]
    result = await station_search(query="Stephans", limit=5)
    
    # Step 2: Use result
    assert result.count > 0
```

## Notes

- All tests use `pytest.mark.asyncio` for async functions
- Tests mock external dependencies (API calls, database)
- Integration tests may require actual server initialization
- FastMCP tool access may vary by version - tests use registration verification

