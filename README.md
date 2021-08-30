### About
This is (currently) a CLI script to function as a prototype client for proxy.obs-websocket.io. Use `--help` on the file to see usage info.

### Setup
- You will need python3.8 or later
- Install the dependencies with `pip install -r requirements.txt` (the file provided in the base directory of this repo)

### Usage
- For all available flags, run `python3.8 src/main.py --help`
- We need to get some required script startup flags squared away
  - We currently have two proxy regions available. Select one to use as `--proxy-host`. Keep your chosen domain in mind for later.
    - `us-west1-a.proxy.obs-websocket.io`
    - `us-west2-a.proxy.obs-websocket.io`
  - Think of a session key to use. It is only used as a way to keep connections unique right now. Anything works. Specify it as `--proxy-session-key`
  - All other flags are optional. The script defaults to connecting to OBS via localhost:4444
- Start the script with `python3.8 src/main.py --proxy-host=(yourhost) --proxy-session-key=(yourkey) (any other flags)`
- The script should load and provide you with a `Connect Port` and `Connect Password`.
- On your obs-websocket client, use your previously selected region domain as the host to connect to, along with the provided connect port and password.
  - Example connect URL: `wss://us-west1-a.proxy.obs-websocket.io:40955`
  - The connect password is used as the websocket authentication password on the client
- You should be all set!

### Notes
- The `ignoreInvalidMessages` and `ignoreNonFatalRequestChecks` are Identify parameters are ignored. This is a limitation of how we proxy requests/events.
- If the connection between the client (this script) and the cloud drops, the assigned endpoint will shut down and all associated obs-websocket clients will be dropped.

### Todo
- Implement batch requests
- Session key management system
- Reserved port/password functionality for opencollective contributors
- If obs-websocket connection drops, drop the connection with the cloud and terminate the application
- (eventually) Switch to C++/Qt and make this into an actual GUI application with binary releases
