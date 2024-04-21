from typing import List, Tuple, Iterable, Set, Dict

import argparse
from tqdm import tqdm

import geopandas as gpd
import pandas as pd
from geopandas.geodataframe import GeoDataFrame
from geopandas.geoseries import GeoSeries
from shapely.geometry.multilinestring import MultiLineString
from pyproj import Transformer

import rtree

import geom_dist


def point2segment(point: Tuple[float, float], rtree: Dict) -> float:
    point1, point2 = map(
        lambda index: rtree['points'][index], rtree['tree'].nearest(point, 2))

    return geom_dist.point2vector(point1, point2, point)


def extract_point(geom: MultiLineString, transformer: Transformer, trans: bool = False) -> List[Tuple[float, float]]:
    points = []
    for line in geom.geoms:
        for point in line.coords:
            x, y = point
            if trans:
                x, y = transformer.transform(x, y)
            points.append((x, y))

    return points


def bin_search(a: Iterable, x: int, i: int) -> int:
    l = 0
    r = len(a)
    while r - l > 1:
        mid = l + (r - l) // 2
        if a[mid][i] <= x:
            l = mid
        else:
            r = mid

    return l


def get_possible_line(eps: float, point: Tuple[float, float], all_points_x: List[Tuple[float, float]]) -> Set:
    mb_blue_line = set()

    for delta in range(10, int(eps + 1), 10):
        min_x = bin_search(
            all_points_x, geom_dist.add_lat(point[0], -delta), 0)
        max_x = bin_search(
            all_points_x, geom_dist.add_lat(point[0], delta), 0)

        for i in range(min_x, max_x + 1):
            if geom_dist.dist_points(point, all_points_x[i]) <= eps:
                mb_blue_line.add(all_points_x[i][2])
        if len(mb_blue_line) > 0:
            break

    return mb_blue_line


def set_group_point(point: Tuple[float, float], lines: Iterable, rtrees: Dict, group_line: Dict) -> None:
    link_id = 0
    min_dist = float('+inf')
    for line in lines:
        try:
            dist = point2segment(
                point, rtrees[line])
        except:
            continue

        if dist < min_dist:
            min_dist = dist
            link_id = line

    if link_id not in group_line:
        group_line[link_id] = []
    group_line[link_id].append(point)


def set_attribute(attributes: GeoDataFrame, graph: GeoDataFrame, road) -> None:
    graph.loc[len(graph.index)] = [road, attributes['id'], attributes['road_id'],
                                   attributes['road_part_id'], attributes['start_m'], attributes['finish_m'], attributes['road_name']]


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument("--red_graph", type=str,
                        help="имя файла атрибутированного набора данных (красный)")
    parser.add_argument("--blue_graph", type=str,
                        help="имя файла референтного набора данных (синий)")
    parser.add_argument("--green_graph", type=str,
                        help="имя файла целевого набора данных (зеленый)")
    parser.add_argument("--eps", type=float,
                        help="точность сопоставления (в метрах)")

    args = parser.parse_args()

    red_graph = args.red_graph
    blue_graph = args.blue_graph
    green_graph = args.green_graph
    eps = args.eps

    print("Read file...")

    graph_blue = gpd.read_file(blue_graph)
    graph_red = gpd.read_file(red_graph)

    graph_green = graph_blue
    graph_green = graph_green.iloc[0:0]
    graph_green = graph_green.drop(columns=['link_id'])
    graph_green['id'] = graph_green.index.astype('int64')
    graph_green['id'] = None
    graph_green['road_id'] = graph_green.index.astype('int64')
    graph_green['road_id'] = None
    graph_green['road_part_id'] = graph_green.index.astype('int64')
    graph_green['road_part_id'] = None
    graph_green['start_m'] = graph_green.index.astype('int64')
    graph_green['start_m'] = None
    graph_green['finish_m'] = graph_green.index.astype('int64')
    graph_green['finish_m'] = None
    graph_green['road_name'] = graph_green.index.astype('object')
    graph_green['road_name'] = None
    data = {'geometry': []}

    print("Extract Point...")

    transformer = Transformer.from_crs(
        graph_red.crs, graph_blue.crs, always_xy=True)

    all_points_x = []
    rtrees = {}
    for index, region in tqdm(graph_blue.iterrows(), total=graph_blue.shape[0], desc="Loading..."):
        row_points = extract_point(region['geometry'], transformer)
        rtrees[region['link_id']] = {
            'tree': rtree.index.Index(),
            'points': []
        }
        for i, point in enumerate(row_points):
            x, y = point
            all_points_x.append((x, y, region['link_id']))
            rtrees[region['link_id']]['tree'].insert(i, point)
            rtrees[region['link_id']]['points'].append(point)
    all_points_x.sort(key=lambda x: x[0])

    print("Group point by line...")
    for index, region in tqdm(graph_red.iterrows(), total=graph_red.shape[0], desc="Loading..."):
        # if region['id'] != 1144086:
        #     continue

        row_points = extract_point(region['geometry'], transformer, True)

        point_group_by_line = {}
        no_used = []
        for point in row_points:
            mb_blue_line = get_possible_line(eps, point, all_points_x)

            if len(mb_blue_line) == 0:
                no_used.append(point)
                continue

            set_group_point(point, mb_blue_line, rtrees, point_group_by_line)

        for point in no_used:
            set_group_point(point, point_group_by_line,
                            rtrees, point_group_by_line)

        cnt_point = 0
        for line in point_group_by_line:
            cnt_point += len(point_group_by_line[line])

        road = MultiLineString()
        for line in point_group_by_line:
            if len(point_group_by_line[line]) >= 0.1 * cnt_point:
                try:
                    road = road.union(
                        graph_blue[graph_blue['link_id'] == line]['geometry'].iloc[0])
                except:
                    continue

        data['geometry'].append(road)
        set_attribute(region, graph_green, road)

    print("Saving...")

    graph_green['geometry'] = GeoDataFrame(data)
    graph_green.to_file(green_graph, driver='GeoJSON')
    print("Finish")


if __name__ == "__main__":
    main()
