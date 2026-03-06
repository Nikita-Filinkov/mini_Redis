import time
import grpc
import kvstore_pb2
import kvstore_pb2_grpc


def run():
    channel = grpc.insecure_channel("localhost:50051")
    stub = kvstore_pb2_grpc.KeyValueStoreStub(channel)

    # Put
    stub.Put(kvstore_pb2.PutRequest(key="a", value="1", ttl_seconds=0))
    stub.Put(kvstore_pb2.PutRequest(key="b", value="2", ttl_seconds=5))
    stub.Put(kvstore_pb2.PutRequest(key="c", value="3", ttl_seconds=0))

    stub.Delete(kvstore_pb2.DeleteRequest(key="b"))
    try:
        stub.Get(kvstore_pb2.GetRequest(key="b"))
    except grpc.RpcError as e:
        print("Get b after delete:", e.code(), e.details())

    # Put ключа с TTL 2 секунды
    stub.Put(kvstore_pb2.PutRequest(key="temp", value="42", ttl_seconds=2))
    print("Put temp with TTL=2")

    # Сразу получаем — должно быть доступно
    resp = stub.Get(kvstore_pb2.GetRequest(key="temp"))
    print(f"Get temp immediately: {resp.value}")

    # Ждём 3 секунды (больше TTL)
    print("Waiting 3 seconds...")
    time.sleep(3)

    # Пытаемся получить — должна быть NOT_FOUND
    try:
        stub.Get(kvstore_pb2.GetRequest(key="temp"))
    except grpc.RpcError as e:
        print(f"Get temp after TTL: {e.code()} - {e.details()}")

    # Проверяем List — ключ не должен появиться
    resp_list = stub.List(kvstore_pb2.ListRequest(prefix=""))
    keys = [item.key for item in resp_list.items]
    print(f"Keys after TTL: {keys}")
    assert "temp" not in keys


if __name__ == "__main__":
    run()
