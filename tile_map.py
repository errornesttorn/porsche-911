#!/usr/bin/env python3
"""
Tile a traffic simulation map into a grid.

Usage:
    python3 tile_map.py <input.json> <output.json> [--cols 3] [--rows 3] [--spacing 800]

Clones all splines, routes, cars, traffic lights, and traffic cycles
with proper ID remapping and position offsets.
"""

import argparse
import copy
import json
import sys


def tile_map(data, cols, rows, spacing):
    max_spline_id = max(s["id"] for s in data["splines"])
    max_route_id = max(r["id"] for r in data["routes"])
    max_tl_id = max(t["id"] for t in data["traffic_lights"])
    max_tc_id = max(t["id"] for t in data["traffic_cycles"])

    # Use generous offsets to avoid collisions
    spline_id_step = max_spline_id + 1
    route_id_step = max_route_id + 1
    tl_id_step = max_tl_id + 1
    tc_id_step = max_tc_id + 1

    result = {"splines": [], "routes": [], "cars": [], "traffic_lights": [], "traffic_cycles": []}

    for row in range(rows):
        for col in range(cols):
            cell = row * cols + col
            dx = col * spacing
            dy = row * spacing

            sid_off = cell * spline_id_step
            rid_off = cell * route_id_step
            tlid_off = cell * tl_id_step
            tcid_off = cell * tc_id_step

            def remap_spline_id(old):
                return old + sid_off

            def remap_spline_ids(ids):
                if not ids:
                    return ids
                return [i + sid_off for i in ids]

            # Splines
            for s in data["splines"]:
                ns = copy.deepcopy(s)
                ns["id"] = remap_spline_id(s["id"])
                for p in ("p0", "p1", "p2", "p3"):
                    ns[p]["x"] += dx
                    ns[p]["y"] += dy
                if "hard_coupled_ids" in ns:
                    ns["hard_coupled_ids"] = remap_spline_ids(ns["hard_coupled_ids"])
                if "soft_coupled_ids" in ns:
                    ns["soft_coupled_ids"] = remap_spline_ids(ns["soft_coupled_ids"])
                result["splines"].append(ns)

            # Routes
            for r in data["routes"]:
                nr = copy.deepcopy(r)
                nr["id"] = r["id"] + rid_off
                nr["start_spline_id"] = remap_spline_id(r["start_spline_id"])
                nr["end_spline_id"] = remap_spline_id(r["end_spline_id"])
                nr["path_ids"] = remap_spline_ids(r["path_ids"])
                if "bus_stops" in nr and nr["bus_stops"]:
                    for bs in nr["bus_stops"]:
                        bs["spline_id"] = remap_spline_id(bs["spline_id"])
                        bs["world_pos_x"] += dx
                        bs["world_pos_y"] += dy
                result["routes"].append(nr)

            # Cars
            for c in data["cars"]:
                nc = copy.deepcopy(c)
                nc["route_id"] = c["route_id"] + rid_off
                nc["current_spline_id"] = remap_spline_id(c["current_spline_id"])
                nc["destination_spline_id"] = remap_spline_id(c["destination_spline_id"])
                result["cars"].append(nc)

            # Traffic lights
            for tl in data["traffic_lights"]:
                ntl = copy.deepcopy(tl)
                ntl["id"] = tl["id"] + tlid_off
                ntl["spline_id"] = remap_spline_id(tl["spline_id"])
                ntl["world_pos_x"] += dx
                ntl["world_pos_y"] += dy
                ntl["cycle_id"] = tl["cycle_id"] + tcid_off
                result["traffic_lights"].append(ntl)

            # Traffic cycles
            for tc in data["traffic_cycles"]:
                ntc = copy.deepcopy(tc)
                ntc["id"] = tc["id"] + tcid_off
                for phase in ntc["phases"]:
                    phase["green_light_ids"] = [gid + tlid_off for gid in phase["green_light_ids"]]
                result["traffic_cycles"].append(ntc)

    return result


def main():
    parser = argparse.ArgumentParser(description="Tile a traffic sim map into a grid")
    parser.add_argument("input", help="Input JSON file")
    parser.add_argument("output", help="Output JSON file")
    parser.add_argument("--cols", type=int, default=3, help="Number of columns (default: 3)")
    parser.add_argument("--rows", type=int, default=3, help="Number of rows (default: 3)")
    parser.add_argument("--spacing", type=float, default=800, help="Distance between clones in meters (default: 800)")
    args = parser.parse_args()

    with open(args.input) as f:
        data = json.load(f)

    result = tile_map(data, args.cols, args.rows, args.spacing)

    with open(args.output, "w") as f:
        json.dump(result, f, indent=2)

    print(f"Tiled {args.cols}x{args.rows} grid with {args.spacing}m spacing")
    print(f"  Splines: {len(data['splines'])} -> {len(result['splines'])}")
    print(f"  Routes:  {len(data['routes'])} -> {len(result['routes'])}")
    print(f"  Cars:    {len(data['cars'])} -> {len(result['cars'])}")
    print(f"  Lights:  {len(data['traffic_lights'])} -> {len(result['traffic_lights'])}")
    print(f"  Cycles:  {len(data['traffic_cycles'])} -> {len(result['traffic_cycles'])}")


if __name__ == "__main__":
    main()
