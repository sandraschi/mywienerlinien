# Advanced Plex API Key Usage and Management

## API Authentication Methods

Plex offers multiple authentication methods for its API:

### 1. X-Plex-Token Authentication

This is the most common method, using the token we obtained in the previous section:

```
GET https://your-server:32400/library/sections?X-Plex-Token=YOUR_TOKEN_HERE
```

### 2. HTTP Basic Authentication

You can also use your Plex username and password with HTTP Basic Authentication:

```python
import requests
from base64 import b64encode

username = "your_plex_username"
password = "your_plex_password"
auth_string = b64encode(f"{username}:{password}".encode()).decode()

headers = {
    "Authorization": f"Basic {auth_string}",
    "X-Plex-Client-Identifier": "my-application"
}

response = requests.get("https://plex.tv/api/v2/resources", headers=headers)
```

### 3. OAuth Authentication Flow

For more secure applications, especially those distributed to other users, Plex supports OAuth:

1. Register your app at [https://plex.tv/api/v2](https://plex.tv/api/v2)
2. Implement the OAuth flow to obtain tokens
3. Use the tokens for API requests

## Token Management

### Regenerating Your Token

If you need to regenerate your Plex token for security reasons:

1. Log out of all Plex sessions:
   - Go to [https://app.plex.tv/desktop/#!/settings/account](https://app.plex.tv/desktop/#!/settings/account)
   - Scroll down to "Authorized Devices"
   - Click "Sign Out All Devices"

2. Change your Plex account password:
   - This will invalidate all existing tokens
   - You'll need to obtain a new token after this

### Token Expiration

Plex tokens generally don't expire unless:
- You sign out of all devices
- You change your password
- Plex invalidates the token for security reasons

## Using Your Token in Applications

### Environment Variables

Store your token in environment variables to keep it out of your code:

```python
import os

plex_token = os.environ.get("PLEX_TOKEN")
```

### Configuration Files

Store your token in a configuration file that's excluded from version control:

```python
import json

with open("config.json", "r") as f:
    config = json.load(f)
    plex_token = config["plex_token"]
```

### Secure Storage

For desktop applications, use secure storage mechanisms:

- Windows: Windows Credential Manager
- macOS: Keychain
- Linux: Secret Service API

## Common API Endpoints

With your Plex token, you can access various endpoints:

### Server Information

```
GET https://your-server:32400/?X-Plex-Token=YOUR_TOKEN_HERE
```

### Libraries

```
GET https://your-server:32400/library/sections?X-Plex-Token=YOUR_TOKEN_HERE
```

### Recently Added Media

```
GET https://your-server:32400/library/recentlyAdded?X-Plex-Token=YOUR_TOKEN_HERE
```

### Search

```
GET https://your-server:32400/search?query=your_search_term&X-Plex-Token=YOUR_TOKEN_HERE
```

## Plex API Clients

Several libraries make working with the Plex API easier:

### Python

- [PlexAPI](https://github.com/pkkid/python-plexapi): Comprehensive Python client
  ```python
  from plexapi.server import PlexServer
  
  baseurl = 'http://your-server:32400'
  token = 'YOUR_TOKEN_HERE'
  plex = PlexServer(baseurl, token)
  
  # Get all movies
  movies = plex.library.section('Movies').all()
  ```

### JavaScript/Node.js

- [plex-api](https://github.com/phillipj/node-plex-api): Node.js client
  ```javascript
  const PlexAPI = require('plex-api');
  
  const client = new PlexAPI({
    hostname: 'your-server',
    port: 32400,
    token: 'YOUR_TOKEN_HERE'
  });
  
  client.query('/library/sections')
    .then(result => console.log(result), err => console.error(err));
  ```

### Other Languages

- [Plex-Ruby](https://github.com/jessedoyle/plex-ruby) for Ruby
- [Plex-Rust](https://github.com/andrey-yantsen/plex-api.rs) for Rust
- [SwiftyPlex](https://github.com/manuel-koch/SwiftyPlex) for Swift

## Rate Limiting and Best Practices

To avoid issues with the Plex API:

1. **Implement caching** to reduce the number of API calls
2. **Add delays between requests** for operations that query large libraries
3. **Use batch operations** when available instead of multiple single requests
4. **Include proper headers** with your requests:
   ```
   X-Plex-Client-Identifier: unique_identifier_for_your_app
   X-Plex-Product: Your_App_Name
   X-Plex-Version: Your_App_Version
   ```

## Conclusion

With your Plex API token and the information in this guide, you can build powerful applications that interact with your Plex Media Server. Remember to keep your token secure and follow best practices when making API requests.

For more detailed information, refer to the [unofficial Plex API documentation](https://github.com/Arcanemagus/plex-api/wiki) and the [Plex Media Server URL commands](https://support.plex.tv/articles/201638786-plex-media-server-url-commands/).
