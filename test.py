from heapq import heappush, heappop
from math import inf


def build_graph() -> dict:

    graph = {
        "Санкт-Петербург": {
            "Великий Новгород": 151,
            "Вологда": 545,
        },
        "Великий Новгород": {
            "Санкт-Петербург": 151,
            "Тверь": 323,
        },
        "Вологда": {
            "Санкт-Петербург": 545,
            "Ярославль": 174,
        },
        "Тверь": {
            "Великий Новгород": 323,
            "Москва": 156,
        },
        "Москва": {
            "Тверь": 156,
            "Ярославль": 246,
            "Владимир": 184,
        },
        "Ярославль": {
            "Вологда": 174,
            "Москва": 246,
            "Иваново": 100,
        },
        "Иваново": {
            "Ярославль": 100,
            "Владимир": 83,
        },
        "Владимир": {
            "Москва": 184,
            "Иваново": 83,
        },
    }
    return graph


def update_road(graph: dict, city_a: str, city_b: str,
                new_length: float, bidirectional: bool = True) -> None:

    graph.setdefault(city_a, {})
    graph[city_a][city_b] = new_length

    if bidirectional:
        graph.setdefault(city_b, {})
        graph[city_b][city_a] = new_length


def dijkstra(graph: dict, start: str, target: str):

    dist = {v: inf for v in graph}
    dist[start] = 0
    prev = {v: None for v in graph}

    heap = []
    heappush(heap, (0, start))

    while heap:
        current_dist, u = heappop(heap)
        if current_dist > dist[u]:
            continue

        if u == target:
            break

        for v, weight in graph[u].items():
            cand = current_dist + weight
            if cand < dist[v]:
                dist[v] = cand
                prev[v] = u
                heappush(heap, (cand, v))

    if dist[target] == inf:
        return inf, []

    path = []
    cur = target
    while cur is not None:
        path.append(cur)
        cur = prev[cur]
    path.reverse()
    return dist[target], path


def main():
    graph = build_graph()

    start_city = "Санкт-Петербург"
    target_city = "Владимир"

    distance, path = dijkstra(graph, start_city, target_city)

    if distance == inf:
        print(f"Маршрута из {start_city} в {target_city} нет.")
    else:
        print(f"Кратчайшее расстояние: {distance}")
        print("Маршрут:", " -> ".join(path))


if __name__ == "__main__":
    main()
