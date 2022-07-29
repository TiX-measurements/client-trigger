# TiX Client Trigger

Mobile apps can run background processes but they don't have much control on the intervals they can execute code. If we want to measure every second using a mobile app, we need some way to wake it up. This is why we created this service: it will ping registered clients every 1 second with an UDP packet so the OS gives control to the background task.

## Configuration

This service is a simple Python script that accepts some configurations as environment variables (see [`main.py`](main.py)):

* `HOST`: the host address where the server listens for clients.
* `PORT`: the host port where to listen.
* `LOG_LEVEL`: Logging level.
* `WORKER_POOL_SIZE`: Number of threads to run and server clients.
* `CLIENT_EXPIRATION_SECONDS`: Number of seconds that need to elapse _without receiving any heartbeat_ from the client until it is removed from the "ping list".

## How to run

You can execute `python main.py` natively or use docker:

```shell
docker build . -t tix-client-trigger
# optionally pass environment variables through Docker
docker run tix-client-trigger
```

## Protocol

This service is very simple:

Server:
 1. The server receives UDP packages from clients (any 2 bytes, content does not matter) and registers them in an internal map.
 2. The clients are sharded between the worker threads.
 3. Each thread will send a 2-byte UDP package (ping) to all the registered clients every second.
 4. If enough time (as defined by `CLIENT_EXPIRATION_SECONDS`) passes without the client sending a package to the server (a heartbeat), the server will stop sending pings.

Client:
 1. Clients that want to be "pinged" register in the server by sending a 2 byte (content does not matter) UDP packet to the server.

### Client example

A very simple illustration on how to implement a client can be the following:

```python
import time
import socket


# this will depend on the server configuration
CLIENT_EXPIRATION_SECONDS = 120

# host and port of the trigger service
TRIGGER_ADDRESS = ('localhost', 7561)
# open UDP socket
sock_trigger_service = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

while True:
    # sending heartbeat with 2 random bytes
    sock_trigger_service.sendto(b'\x75\x61', TRIGGER_ADDRESS)

    time.sleep(CLIENT_EXPIRATION_SECONDS / 3)
```

The client will then receive the "pings" from the server every second through the socket.
