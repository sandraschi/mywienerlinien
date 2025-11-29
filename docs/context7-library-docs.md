# Context-7 Library Documentation

This document contains library documentation retrieved via Context-7 MCP server.

**Last Updated:** 2025-01-15

---

## Table of Contents

- [FastMCP](#fastmcp)
- [FastAPI](#fastapi)
- [Swagger/OpenAPI](#swaggeropenapi)
- [Werkzeug](#werkzeug)
- [Tailscale](#tailscale)

---

## FastMCP

### Overview
FastMCP is a fast, Pythonic framework for building Model Context Protocol (MCP) servers and clients, simplifying the creation of LLM-integrated applications.

### Server Setup

**Initialize a FastMCP Server Instance:**
```python
from fastmcp import FastMCP

# Create a server instance
mcp = FastMCP(name="MyAssistantServer")
```

**Run Server:**
```python
# Default stdio transport
mcp.run()

# HTTP transport
mcp.run(transport="http", host="127.0.0.1", port=9000)
```

### Tools

**Define a FastMCP Tool with Python Decorator:**
```python
from fastmcp import FastMCP

mcp = FastMCP(name="CalculatorServer")

@mcp.tool
def add(a: int, b: int) -> int:
    """Adds two integer numbers together."""
    return a + b
```

### Resources

**Define Dynamic FastMCP Resources:**
```python
import json
from fastmcp import FastMCP

mcp = FastMCP(name="DataServer")

# Basic dynamic resource returning a string
@mcp.resource("resource://greeting")
def get_greeting() -> str:
    """Provides a simple greeting message."""
    return "Hello from FastMCP Resources!"

# Resource returning JSON data (dict is auto-serialized)
@mcp.resource("data://config")
def get_config() -> dict:
    """Provides application configuration as JSON."""
    return {
        "theme": "dark",
        "version": "1.2.0",
        "features": ["tools", "resources"]
    }
```

**Resource with Parameterized URIs:**
```python
@mcp.resource("resource://{city}/weather")
def get_weather(city: str) -> str:
    return f"Weather for {city}"

@mcp.resource("resource://{city}/weather")
async def get_weather_with_context(city: str, ctx: Context) -> str:
    await ctx.info(f"Fetching weather for {city}")
    return f"Weather for {city}"
```

### Prompts

**FastMCP 2.12+ Standards:**
- Prompts return `list[dict[str, Any]]` with message format `[{"role": "user", "content": "..."}]`
- Store prompt function references to prevent garbage collection

### Middleware

**Response Caching Middleware:**
```python
from fastmcp.server.middleware.caching import ResponseCachingMiddleware

mcp.add_middleware(ResponseCachingMiddleware())
```

**Resource Tool Middleware:**
```python
from fastmcp.server.middleware.tool_injection import ResourceToolMiddleware

mcp.add_middleware(ResourceToolMiddleware())
```

**Prompt Tool Middleware:**
```python
from fastmcp import FastMCP
from fastmcp.server.middleware.tool_injection import PromptToolMiddleware

mcp = FastMCP("MyServer")
mcp.add_middleware(PromptToolMiddleware())
```

**Custom Middleware:**
```python
from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.exceptions import ResourceError, PromptError

class ComponentAccessMiddleware(Middleware):
    async def on_read_resource(self, context: MiddlewareContext, call_next):
        if context.fastmcp_context:
            try:
                resource = await context.fastmcp_context.fastmcp.get_resource(context.message.uri)
                if "restricted" in resource.tags:
                    raise ResourceError("Access denied: restricted resource")
            except Exception:
                pass
        return await call_next(context)
```

### Server Composition

**Import Server Components:**
```python
from fastmcp import FastMCP
import asyncio

# Define subservers
weather_mcp = FastMCP(name="WeatherService")

@weather_mcp.tool
def get_forecast(city: str) -> dict:
    """Get weather forecast."""
    return {"city": city, "forecast": "Sunny"}

# Define main server
main_mcp = FastMCP(name="MainApp")

# Import subserver
async def setup():
    await main_mcp.import_server(weather_mcp, prefix="weather")

# Result: main_mcp now contains prefixed components:
# - Tool: "weather_get_forecast"
# - Resource: "data://weather/cities/supported"
```

### Complete Example

```python
from fastmcp import FastMCP

# 1. Create the server
mcp = FastMCP(name="My First MCP Server")

# 2. Add a tool
@mcp.tool
def add(a: int, b: int) -> int:
    """Adds two integer numbers together."""
    return a + b

# 3. Add a static resource
@mcp.resource("resource://config")
def get_config() -> dict:
    """Provides the application's configuration."""
    return {"version": "1.0", "author": "MyTeam"}

# 4. Add a resource template for dynamic content
@mcp.resource("greetings://{name}")
def personalized_greeting(name: str) -> str:
    """Generates a personalized greeting for the given name."""
    return f"Hello, {name}! Welcome to the MCP server."

# 5. Make the server runnable
if __name__ == "__main__":
    mcp.run()
```

---

## FastAPI

### Overview
FastAPI is a modern, fast web framework for building APIs with Python. It's known for its high performance, ease of use, and automatic interactive documentation.

### Basic Setup

**Initialize FastAPI:**
```python
from fastapi import FastAPI

app = FastAPI()
```

### Path Parameters

**Basic Path Parameter:**
```python
@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}
```

**Path Parameter with Validation:**
```python
from typing import Annotated
from fastapi import FastAPI, Path

@app.get("/items/{item_id}")
async def read_items(
    item_id: Annotated[int, Path(title="The ID of the item to get", ge=1)]
):
    return {"item_id": item_id}
```

### Query Parameters

**Basic Query Parameter:**
```python
from typing import Union

@app.get("/items/")
async def read_items(q: Union[str, None] = None):
    results = {"items": [{"item_id": "Foo"}, {"item_id": "Bar"}]}
    if q:
        results.update({"q": q})
    return results
```

**Query Parameter with Validation:**
```python
from typing import Annotated
from fastapi import FastAPI, Query

@app.get("/items/")
async def read_items(
    q: Annotated[
        Union[str, None],
        Query(
            description="Query string for the items to search",
            min_length=3,
        ),
    ] = None
):
    results = {"items": [{"item_id": "Foo"}, {"item_id": "Bar"}]}
    if q:
        results.update({"q": q})
    return results
```

**Query Parameters with Pydantic Model:**
```python
from typing import Annotated, Literal
from fastapi import FastAPI, Query
from pydantic import BaseModel, Field

app = FastAPI()

class FilterParams(BaseModel):
    limit: int = Field(100, gt=0, le=100)
    offset: int = Field(0, ge=0)
    order_by: Literal["created_at", "updated_at"] = "created_at"
    tags: list[str] = []

@app.get("/items/")
async def read_items(filter_query: Annotated[FilterParams, Query()]):
    return filter_query
```

### Request Body

**POST Endpoint with Pydantic Model:**
```python
from typing import Union
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    description: Union[str, None] = None
    price: float
    tax: Union[float, None] = None

@app.post("/items/")
async def create_item(item: Item):
    item_dict = item.dict()
    if item.tax:
        price_with_tax = item.price + item.tax
        item_dict["price_with_tax"] = price_with_tax
    return item_dict
```

**List of Models:**
```python
from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Image(BaseModel):
    url: str
    name: Optional[str] = None

@app.post("/images/")
async def create_images(images: list[Image]):
    return images
```

**Multiple Body Parameters:**
```python
from typing import Annotated, Union
from fastapi import FastAPI, Path, Body
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    description: Union[str, None] = None
    price: float

class User(BaseModel):
    username: str
    full_name: Union[str, None] = None

@app.put("/items/{item_id}")
async def update_item(
    item_id: Annotated[int, Path(ge=1)],
    item: Item,
    user: User,
    importance: Annotated[int, Body(ge=1, le=5)]
):
    return {
        "item_id": item_id,
        "item": item,
        "user": user,
        "importance": importance
    }
```

### Dependencies

**Function Dependency:**
```python
from fastapi import FastAPI, Depends

def common_parameters(q: str | None = None, skip: int = 0, limit: int = 100):
    return {"q": q, "skip": skip, "limit": limit}

@app.get("/items/")
async def read_items(commons: dict = Depends(common_parameters)):
    return commons
```

**Class Dependency:**
```python
from typing import Annotated
from fastapi import FastAPI, Depends
from pydantic import BaseModel

class CommonQueryParams(BaseModel):
    q: str | None = None
    skip: int = 0
    limit: int = 100

app = FastAPI()

@app.get("/items/")
async def read_items(commons: Annotated[CommonQueryParams, Depends()]):
    return commons
```

**Dependencies with Yield (Resource Cleanup):**
```python
from typing import Generator
from fastapi import Depends, FastAPI

app = FastAPI()

async def dependency_a() -> Generator[str, None, None]:
    print("Open dependency A")
    try:
        yield "A_value"
    finally:
        print("Close dependency A")

async def dependency_b(dep_a: str = Depends(dependency_a)) -> Generator[str, None, None]:
    print(f"Open dependency B, using {dep_a}")
    try:
        yield f"B_value (from {dep_a})"
    finally:
        print(f"Close dependency B, still has {dep_a}")

@app.get("/sub_deps/")
async def read_sub_deps(final_value: str = Depends(dependency_b)):
    return {"message": "Using sub-dependencies", "value": final_value}
```

**Disable Dependency Caching:**
```python
async def needy_dependency(fresh_value: Annotated[str, Depends(get_value, use_cache=False)]):
    return {"fresh_value": fresh_value}
```

**Router-Level Dependencies:**
```python
from fastapi import APIRouter, Depends

async def some_dependency():
    return

router = APIRouter(prefix="/users", dependencies=[Depends(some_dependency)])
```

### Headers and Cookies

**Header Parameters with Pydantic Model:**
```python
from typing import Annotated
from fastapi import FastAPI, Header
from pydantic import BaseModel

app = FastAPI()

class CommonHeaders(BaseModel):
    host: str
    save_data: bool
    if_modified_since: str | None = None
    traceparent: str | None = None
    x_tag: list[str] = []

@app.get("/items/")
async def read_items(headers: Annotated[CommonHeaders, Header()]):
    return headers
```

**Cookie Parameters:**
```python
from typing import Annotated
from fastapi import Cookie, FastAPI
from pydantic import BaseModel

app = FastAPI()

class Cookies(BaseModel):
    session_id: str
    fatebook_tracker: str | None = None
    googall_tracker: str | None = None

@app.get("/items/")
async def read_items(cookies: Annotated[Cookies, Cookie()]):
    return cookies
```

### Response Models

**Response Model:**
```python
from fastapi import FastAPI
from pydantic import BaseModel

class ItemV2(BaseModel):
    title: str
    summary: str | None = None

app = FastAPI()

@app.post("/items/", response_model=ItemV2)
def create_item(item: Item):
    return {"title": item.name, "summary": item.description}
```

---

## Swagger/OpenAPI

### Overview
Swagger is a set of open-source tools built around the OpenAPI Specification, designed to help developers design, build, document, and consume REST APIs.

### OpenAPI Specification

**Key Features:**
- **Endpoints and Operations**: Defines available paths (e.g., `/users`) and HTTP methods (e.g., `GET`, `POST`)
- **Parameters**: Describes input and output for each operation
- **Authentication**: Specifies authentication methods
- **Metadata**: Includes contact information, license, terms of use, etc.

**Format:** API specifications can be written in YAML or JSON

### Swagger Tools

**Major Swagger Tools:**
- **Swagger Editor**: Browser-based editor for writing OpenAPI definitions
- **Swagger UI**: Renders OpenAPI definitions into interactive API documentation
- **Swagger Codegen**: Generates server stubs and client libraries in various languages
- **Swagger Core**: Java libraries for creating, consuming, and working with OpenAPI definitions
- **Swagger Parser**: Standalone library for parsing OpenAPI definitions

### Swagger UI Configuration

**Basic Setup:**
```javascript
window.onload = function() {
  window["SwaggerUIBundle"] = window["swagger-ui-bundle"]
  window["SwaggerUIStandalonePreset"] = window["swagger-ui-standalone-preset"]
  
  const ui = SwaggerUIBundle({
    url: "https://petstore.swagger.io/v2/swagger.json",
    dom_id: '#swagger-ui',
    presets: [
      SwaggerUIBundle.presets.apis,
      SwaggerUIStandalonePreset
    ],
    plugins: [
      SwaggerUIBundle.plugins.DownloadUrl
    ],
    layout: "StandaloneLayout",
    docExpansion: "full",
    defaultModelExpandDepth: 100,
    defaultModelRendering: "model"
  })
  window.ui = ui
}
```

**Configuration Options:**
- `deepLinking`: Enable deep linking for tags and operations
- `displayOperationId`: Controls display of operationId
- `docExpansion`: Controls default expansion ("list", "full", "none")
- `filter`: Enable filtering of operations
- `displayRequestDuration`: Show request duration for "Try it out" requests
- `supportedSubmitMethods`: HTTP methods with "Try it out" enabled

**OAuth Configuration:**
```javascript
ui.initOAuth({
  clientId: "your-client-id",
  clientSecret: "your-client-secret-if-required",
  realm: "your-realms",
  appName: "your-app-name",
  scopeSeparator: " ",
  scopes: "read:pets profile openid",
  additionalQueryStringParams: {}
})
```

### OpenAPI Authentication

**API Key Security Scheme:**
```yaml
components:
  securitySchemes:
    ApiKeyAuth:
      type: apiKey
      in: header
      name: X-API-Key
```

**Applying Security:**
```yaml
# Global security
security:
  - ApiKeyAuth: []

# Operation-specific security
paths:
  /items:
    get:
      summary: Get a list of items
      security:
        - ApiKeyAuth: []
      responses:
        '200':
          description: A list of items
```

### Parameter Serialization

**Serialization Styles:**
- `simple`: No prefix
- `label`: `.` prefix
- `matrix`: `;` prefix
- `form`: `?` or `&` prefix (default for query)
- `pipeDelimited`: `?` or `&` prefix using `|` to join values
- `spaceDelimited`: `?` or `&` prefix using spaces to join values

**Explode:**
- `explode: false`: No modifier
- `explode: true`: `*` suffix

---

## Werkzeug

### Overview
Werkzeug is a comprehensive WSGI web application library. It provides utilities for WSGI applications and is the foundation for Flask and other WSGI frameworks.

### Basic WSGI Application

**Simple Response:**
```python
from werkzeug.wrappers import Response

def application(environ, start_response):
    response = Response('Hello World!', mimetype='text/plain')
    return response(environ, start_response)
```

**Even Simpler:**
```python
from werkzeug.wrappers import Response
application = Response('Hello World!')
```

### Request Handling

**Wrapping WSGI Environment:**
```python
from werkzeug.wrappers import Request

def application(environ, start_response):
    request = Request(environ)
    text = f"Hello {request.args.get('name', 'World')}!"
    response = Response(text, mimetype='text/plain')
    return response(environ, start_response)
```

**Using Request Decorator:**
```python
from werkzeug.wrappers import Request, Response

@Request.application
def application(request):
    return Response(f"Hello {request.args.get('name', 'World!')}!")
```

**Accessing Form Data:**
```python
from markupsafe import escape
from werkzeug.wrappers import Request, Response

@Request.application
def hello_world(request):
    result = ['<title>Greeter</title>']
    if request.method == 'POST':
        result.append(f"<h1>Hello {escape(request.form['name'])}!</h1>")
    result.append('''
            <form action="" method="post">
                <p>Name: <input type="text" name="name" size="20">
                <input type="submit" value="Greet me">
            </form>
        ''')
    return Response(''.join(result), mimetype='text/html')
```

### URL Routing

**Define URL Rules:**
```python
from werkzeug.routing import Map, Rule, NotFound, RequestRedirect
from werkzeug.exceptions import HTTPException

url_map = Map([
    Rule('/', endpoint='blog/index'),
    Rule('/<int:year>/', endpoint='blog/archive'),
    Rule('/<int:year>/<int:month>/', endpoint='blog/archive'),
    Rule('/<int:year>/<int:month>/<int:day>/', endpoint='blog/archive'),
    Rule('/<int:year>/<int:month>/<int:day>/<slug>',
         endpoint='blog/show_post'),
    Rule('/about', endpoint='blog/about_me'),
    Rule('/feeds/', endpoint='blog/feeds'),
    Rule('/feeds/<feed_name>.rss', endpoint='blog/show_feed')
])

def application(environ, start_response):
    urls = url_map.bind_to_environ(environ)
    try:
        endpoint, args = urls.match()
    except HTTPException as e:
        return e(environ, start_response)
    start_response('200 OK', [('Content-Type', 'text/plain')])
    return [f'Rule points to {endpoint!r} with arguments {args!r}'.encode()]
```

**Type Converters:**
- `<int:year>`: Integer parameter
- `<slug>`: Slug parameter
- `<string:name>`: String parameter

### Testing

**Test Client:**
```python
from werkzeug.test import Client
from werkzeug.testapp import test_app

c = Client(test_app)
response = c.get("/")
print(response.status_code)  # 200
print(response.headers)
print(response.get_data(as_text=True))
```

### Common Patterns

**Redirect:**
```python
from werkzeug.utils import redirect

def on_follow_short_link(self, request, short_id):
    link_target = self.redis.get(f'url-target:{short_id}')
    if link_target is None:
        raise NotFound()
    self.redis.incr(f'click-count:{short_id}')
    return redirect(link_target)
```

**Error Handling:**
```python
from werkzeug.exceptions import NotFound

if resource is None:
    raise NotFound()
```

---

## Tailscale

### Overview
Tailscale is a VPN service that simplifies secure network connections between devices, creating a private network anywhere using WireGuard technology.

### Installation

**CentOS/RHEL:**
```bash
sudo dnf config-manager --add-repo https://pkgs.tailscale.com/stable/centos/10/tailscale.repo
sudo dnf install tailscale
sudo systemctl enable --now tailscaled
sudo tailscale up
tailscale ip -4
```

**Windows (with Auth Key):**
```bash
tailscale up --accept-dns=false --auth-key=tskey-0123456789abcdef
```

**PiKVM:**
```bash
rw
pacman -Sy tailscale-pikvm
systemctl enable --now tailscaled
tailscale up
tailscale set --ssh
ro
```

### CLI Commands

**Basic Connection:**
```bash
# Interactive login
tailscale up

# With auth key
tailscale up --auth-key=tskey-...

# Get IP address
tailscale ip -4
```

**Configuration:**
```bash
# Configure Kubernetes
tailscale configure kubeconfig <hostname-or-fqdn>

# Configure Synology
tailscale configure synology

# Configure macOS system extension
tailscale configure sysext activate
tailscale configure sysext deactivate
tailscale configure sysext status

# Configure Linux systray
tailscale configure systray --enable-startup=systemd
```

**App Connector:**
```bash
tailscale up --advertise-connector --advertise-tags=tag:<connector-tag-name>
```

**Enable Tailscale SSH:**
```bash
tailscale set --ssh
```

### Tailscale API v2

**Base URL:** `https://api.tailscale.com/api/v2/`

**Authentication:**
```bash
# Basic Auth
curl -u "tskey-api-xxxxx:" https://api.tailscale.com/api/v2/...

# Bearer Token
curl -H "Authorization: Bearer tskey-api-xxxxx" https://api.tailscale.com/api/v2/...
```

**API Token Types:**
- **API Access Tokens** (`tskey-api-...`): Personal tokens with user permissions, expire in 1-90 days
- **OAuth Clients** (`tskey-client-...`): Long-lived clients for creating scoped access tokens

### API Endpoints

**Get Device:**
```bash
curl -X GET "https://api.tailscale.com/api/v2/device/{deviceId}?fields=all"
```

**Authorize Device:**
```bash
curl -X POST "https://api.tailscale.com/api/v2/device/{deviceId}/authorized" \
  -H "Content-Type: application/json" \
  -d '{"authorized": true}'
```

**Expire Device Key:**
```bash
curl -X POST "https://api.tailscale.com/api/v2/device/{deviceId}/expire"
```

**Disable Key Expiry:**
```bash
curl -X POST "https://api.tailscale.com/api/v2/device/{deviceId}/key" \
  -H "Content-Type: application/json" \
  -d '{"keyExpiryDisabled": true}'
```

**Create Device Invite:**
```bash
curl -X POST "https://api.tailscale.com/api/v2/device/{deviceId}/device-invites" \
  -H "Content-Type: application/json" \
  -d '[{
    "multiUse": false,
    "allowExitNode": false,
    "email": "user@example.com"
  }]'
```

**Posture Attributes:**
```bash
# Create/Update
curl -X POST "https://api.tailscale.com/api/v2/device/{deviceId}/attributes/{attributeKey}" \
  -H "Content-Type: application/json" \
  -d '{
    "value": "string",
    "expiry": "2022-12-01T05:23:30Z",
    "comment": "string"
  }'

# Delete
curl -X DELETE "https://api.tailscale.com/api/v2/device/{deviceId}/attributes/{attributeKey}"
```

### Device Properties

**Key Fields:**
- `nodeId`: Preferred device identifier
- `addresses`: List of Tailscale IP addresses (IPv4 and IPv6)
- `hostname`: Machine name
- `name`: MagicDNS name (e.g., `hostname.tailnet.ts.net`)
- `tags`: Device tags for ACL-based access
- `authorized`: Whether device is authorized
- `expires`: Key expiration date
- `keyExpiryDisabled`: Whether key expiry is disabled
- `isEphemeral`: Whether device is ephemeral
- `sshEnabled`: Whether Tailscale SSH is enabled
- `enabledRoutes`: Approved subnet routes
- `advertisedRoutes`: Requested subnet routes

### Features

**MagicDNS:**
- Automatic DNS names: `hostname.tailnet.ts.net`
- No manual DNS configuration needed

**Tailscale SSH:**
- Secure SSH access via Tailscale network
- Enable with: `tailscale set --ssh`

**Subnet Routes:**
- Expose local subnets to tailnet
- Use `advertisedRoutes` and `enabledRoutes` fields

**Exit Nodes:**
- Route traffic through specific devices
- Configure via device settings

**ACLs:**
- Access control lists for fine-grained permissions
- Use tags for device-based access control

### Best Practices

1. **Use Auth Keys** for automated deployments
2. **Configure Tags** for device-based access control
3. **Use API Tokens** for programmatic management
4. **Enable Tailscale SSH** for secure remote access
5. **Use Subnet Routes** to expose local networks
6. **Monitor Key Expiry** to prevent connection issues
7. **Use Ephemeral Devices** for short-lived connections

---

## Notes

- This documentation is retrieved on-demand via Context-7 MCP server
- Documentation may be updated or expanded as needed
- For the latest information, refer to official library documentation
- Context-7 provides access to up-to-date documentation from various sources

