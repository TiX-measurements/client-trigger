import logging
import socket
from typing import Tuple

from worker import Worker


class Server:
    """
    Main server that listens for client packets and delegates to the worker threads.
    The main thread will shard the work among the different workers by hashing their
    addresses.
    """

    def __init__(
            self,
            listen_address:Tuple[str, int],
            pool_size:int,
            client_expiration_seconds:int) -> None:
        self._listen_address = listen_address
        self._stop = False

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

        self._pool = [
            Worker(id=i, client_expiration=client_expiration_seconds, socket=self._socket)
            for i in range(pool_size)
        ]

        self.log = logging.getLogger(f'Server')

    def start(self) -> None:
        """Starts the server. Note that this function will block until an exit
        signal is received."""

        self.log.info('Listening on %s:%d', *self._listen_address)
        self._socket.bind(self._listen_address)

        # start workers in their own threads
        for worker in self._pool:
            worker.start()

        while not self._stop:
            _, client_address = self._socket.recvfrom(2)
            self.notify_worker(client_address)

        self.log.info('Stopped')

    def stop(self) -> None:
        """Gracefully stop the server and all the workers."""

        self.log.info('Stopping...')
        self._stop = True

        for worker in self._pool:
            worker.stop = True

        for worker in self._pool:
            worker.join()

    def notify_worker(self, address) -> None:
        """Notify a worker about a new client. `address` must the the client's
        address. The worker will register the client or update the TTL."""

        # shard the clients among the workers by hashing the address
        worker_id = hash(address) % len(self._pool)
        self._pool[worker_id].add_client(address=address)
