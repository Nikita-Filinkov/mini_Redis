import threading
import time
from collections import OrderedDict
from concurrent import futures

import grpc

# Импортируем сгенерированные модули
import kvstore_pb2
import kvstore_pb2_grpc


class KeyValueStoreServicer(kvstore_pb2_grpc.KeyValueStoreServicer):
    def __init__(self):
        self._store = OrderedDict()
        self._lock = threading.Lock()
        self._max_size = 10

    @staticmethod
    def _is_expired(expires_at):
        """Проверяет, истек ли TTL"""
        if expires_at is None:
            return False
        return time.time() > expires_at

    def _evict_if_needed(self):
        """Если превышен лимит, удаляет самый старый ключ"""
        self._clear_all_expired_keys()
        if len(self._store) > self._max_size:
            self._store.popitem(last=False)

    def _remove_expired(self, key):
        """Удаляет ключ, если он истек, и возвращает True"""
        if key not in self._store:
            return False
        _, expires_at = self._store[key]
        if self._is_expired(expires_at):
            del self._store[key]
            return True
        return False

    def _clear_all_expired_keys(self):
        """Удаляет все истекшие ключи"""
        for key in list(self._store.keys()):
            self._remove_expired(key=key)

    def Put(self, request, context):
        with self._lock:
            key = request.key
            value = request.value
            ttl = request.ttl_seconds

            expires_at = None
            if ttl > 0:
                expires_at = time.time() + ttl

            if key in self._store:
                del self._store[key]

            self._store[key] = (value, expires_at)

            self._evict_if_needed()

        return kvstore_pb2.PutResponse()

    def Get(self, request, context):
        with self._lock:
            key = request.key

            if key not in self._store:
                context.abort(grpc.StatusCode.NOT_FOUND, "Key not found")

            value, expires_at = self._store[key]

            if self._is_expired(expires_at):
                del self._store[key]
                context.abort(grpc.StatusCode.NOT_FOUND, "Key expired")

            self._store.move_to_end(key)

        return kvstore_pb2.GetResponse(value=value)

    def Delete(self, request, context):
        with self._lock:
            key = request.key
            if key in self._store:
                del self._store[key]
        return kvstore_pb2.DeleteResponse()

    def List(self, request, context):
        prefix = request.prefix
        items = []
        with self._lock:
            self._clear_all_expired_keys()
            for key, (value, expires_at) in list(self._store.items()):
                if key.startswith(prefix):
                    items.append(kvstore_pb2.KeyValue(key=key, value=value))

        return kvstore_pb2.ListResponse(items=items)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    kvstore_pb2_grpc.add_KeyValueStoreServicer_to_server(
        KeyValueStoreServicer(), server
    )
    server.add_insecure_port("[::]:50051")
    print("Server started on port 50051")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
