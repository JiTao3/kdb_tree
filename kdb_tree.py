import numpy as np
from numpy.lib.function_base import insert

from utils import overlapping_range, split_region_node, region_range, split_point_node
import copy


class Node(object):
    def __init__(self, node_type="region") -> None:
        super().__init__()
        self.type = node_type
        self.dim_range = []
        self.regions = []
        self.range_bound = []
        self.parent = {}
        self.points = []


class KDBTree(object):
    def __init__(self, dim, point_thread=4, num_region=3) -> None:
        super().__init__()
        self.dim = dim
        self.point_thread = point_thread
        self.num_region = num_region
        self.root = Node(node_type="region")

    def insert(self, point, value):
        q_point = [[p, p] for p in point]
        rec = {"point": point, "value": value}

        def __insert__(node: Node, depth):
            if node.type == "region":
                for reg_idx, reg in enumerate(node.regions):
                    if overlapping_range(q_point=q_point, range_bound=reg.range_bound):
                        reg.parent["node"] = node
                        reg.parent["index"] = reg_idx
                        return __insert__(reg, depth + 1)
            elif node.type == "points":
                if len(node.points) < self.point_thread:
                    node.points.append({"point": point, "value": value})
                    return
                axis = (depth + 1) % self.dim
                corrds = [p[axis] for p in node.points]
                pivot = np.median(corrds)
                assert node.parent, "node is root!"
                if len(node.parent.regions) >= self.num_region - 1:
                    node_parent = node.parent["node"]
                    while len(node_parent.regions) >= self.num_region - 1:
                        right = split_region_node(node_parent, pivot, axis)
                        if node_parent == self.root:
                            node_parent.range_bound = region_range(
                                self.dim, node_parent.regions
                            )
                            self.root = Node(type="region")
                            self.root.regions.append(node_parent)
                            self.root.regions.append(right)
                            return __insert__(self.root, 0)
                        else:
                            node_parent.regions.append(right)
                            node_parent = node_parent.parent
                        __insert__(node_parent, depth + 1)
                else:
                    right = split_point_node(node, pivot, axis)
                    node_parent = node.parent["node"]
                    parent_index = node.parent["index"]
                    lrange = copy.deepcopy(
                        node_parent.regions[parent_index].range_bound
                    )
                    rrange = copy.deepcopy(
                        node_parent.regions[parent_index].range_bound
                    )
                    lrange[axis][1] = pivot
                    rrange[axis][0] = pivot
                    node.range_bound = lrange
                    right.range_bound = rrange
                    node_parent.regions[parent_index] = right
                    node_parent.regions.append(right)
                    insert(node_parent, depth + 1)
