"""Point-in-polygon + sensor placement suggestion for drawn farm shapes."""
import math

SENSORS_PER_HECTARE = 5
MIN_SENSORS = 1
MAX_SENSORS = 30


def sensor_count_for(hectares: float) -> int:
    return min(MAX_SENSORS, max(MIN_SENSORS, round(hectares * SENSORS_PER_HECTARE)))


def _point_in_polygon(lat: float, lng: float, polygon: list[list[float]]) -> bool:
    # ray-casting, treating lng as x and lat as y — fine at farm-plot scale
    n = len(polygon)
    inside = False
    x, y = lng, lat
    j = n - 1
    for i in range(n):
        yi, xi = polygon[i]
        yj, xj = polygon[j]
        if (yi > y) != (yj > y):
            x_intersect = (xj - xi) * (y - yi) / (yj - yi) + xi
            if x < x_intersect:
                inside = not inside
        j = i
    return inside


def suggest_sensor_points(polygon: list[list[float]], n: int) -> list[list[float]]:
    """Pick n points spread inside the polygon. Falls back to the centroid if the
    polygon is too thin/small to fit a grid of n points (e.g. a sliver shape)."""
    lats = [p[0] for p in polygon]
    lngs = [p[1] for p in polygon]
    lat_min, lat_max = min(lats), max(lats)
    lng_min, lng_max = min(lngs), max(lngs)
    centroid = [sum(lats) / len(lats), sum(lngs) / len(lngs)]

    points = []
    grid_dim = max(2, math.ceil(math.sqrt(n)) + 2)
    for _ in range(6):  # widen the grid a few times if too few points land inside
        points = []
        for i in range(grid_dim):
            for j in range(grid_dim):
                lat = lat_min + (lat_max - lat_min) * (i + 0.5) / grid_dim
                lng = lng_min + (lng_max - lng_min) * (j + 0.5) / grid_dim
                if _point_in_polygon(lat, lng, polygon):
                    points.append([lat, lng])
        if len(points) >= n:
            break
        grid_dim += 2

    if not points:
        return [centroid] * n

    if len(points) > n:
        step = len(points) / n
        points = [points[int(i * step)] for i in range(n)]
    while len(points) < n:
        points.append(centroid)
    return points[:n]


if __name__ == "__main__":
    square = [[14.0, 121.0], [14.0, 121.01], [14.01, 121.01], [14.01, 121.0]]
    for n in (1, 4, 10):
        pts = suggest_sensor_points(square, n)
        assert len(pts) == n
        print(f"n={n}: {pts}")
