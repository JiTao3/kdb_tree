import numpy as np
import copy
from copy import deepcopy

from numpy.lib.polynomial import roots


class Node(object):
    def __init__(self, node_type="region") -> None:
        super().__init__()
        self.node_type = node_type
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
        self.root.regions.append(Node(node_type="points"))
        for _ in range(self.dim):
            self.root.regions[0].range_bound.append(
                [-float("inf"), float("inf")])

    def insert(self, point, value):
        q_point = [[p, p] for p in point]
        rec = {"point": point, "value": value}

        def __insert__(node: Node, depth):
            if node.node_type == "region":
                for reg_idx, reg in enumerate(node.regions):
                    if overlapping_range(q_point=q_point, range_bound=reg.range_bound):
                        reg.parent["node"] = node
                        reg.parent["index"] = reg_idx
                        return __insert__(reg, depth + 1)
            elif node.node_type == "points":
                if len(node.points) < self.point_thread:
                    node.points.append({"point": point, "value": value})
                    return
                axis = (depth + 1) % self.dim
                corrds = [p["point"][axis] for p in node.points]
                pivot = np.median(corrds)
                assert node.parent, "node is root!"
                if len(node.parent["node"].regions) >= self.num_region - 1:
                    # region node overflow, split parent node
                    node_parent = node.parent["node"]
                    while len(node_parent.regions) >= self.num_region - 1:
                        right = split_region_node(
                            node_parent, pivot, axis, self.dim)
                        if node_parent == self.root:
                            node_parent.range_bound = region_range(
                                self.dim, node_parent.regions
                            )
                            self.root = Node(node_type="region")
                            self.root.regions.append(node_parent)
                            self.root.regions.append(right)
                            return __insert__(self.root, 0)
                        else:
                            node_parent.regions.append(right)
                            node_parent = node_parent.parent["node"]
                    __insert__(node_parent, depth + 1)
                else:
                    # split point node
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
                    node_parent.regions[parent_index] = node
                    node_parent.regions.append(right)
                    __insert__(node_parent, depth + 1)

        __insert__(self.root, 0)

    def query(self, query):
        if not isinstance(query[0], list):
            query = [[x, x] for x in query]
        result = []

        def __query__(node: Node):
            nonlocal result
            if node.node_type == "region":
                for re in node.regions:
                    if overlapping_range(query, re.range_bound):
                        __query__(re)
            elif node.node_type == "points":
                for pt in node.points:
                    if overlapping_point(query, pt["point"]):
                        result.append(pt)

        __query__(self.root)
        return result


def overlapping_range(q_point, range_bound):
    def overlaping(qp, rb):
        return (
            (rb[0] <= qp[0] <= rb[1])
            or (rb[0] <= qp[1] <= rb[1])
            or (qp[0] < rb[0] and qp[1] > rb[1])
        )

    for qp, rb in zip(q_point, range_bound):
        if not overlaping(qp, rb):
            return False
    return True


def split_region_node(node, pivot, axis, dim):
    rrange = region_range(dim, node.regions)
    rrange[axis][0] = pivot
    right = Node(node_type="region")
    right.range_bound = rrange

    left = node
    i = 0

    while i < len(node.regions):
        le_r = node.regions[i]
        if le_r.range_bound[axis][1] < pivot:
            i += 1
            continue
        elif le_r.range_bound[axis][0] >= pivot:
            right.regions.append(le_r)
            left.regions.remove(le_r)
            # i -= 1
        else:
            i += 1
            r_node = Node()
            rright = deepcopy(le_r.range_bound)
            rright[axis][0] = pivot
            r_node.range_bound = rright
            right.regions.append(r_node)

            rleft = le_r
            rleft.range_bound[axis][1] = pivot
            if le_r.node_type == "points":
                r_reg = split_point_node(le_r, pivot, axis)
                r_node.points = r_reg.points
                r_node.node_type = "points"
            elif le_r.node_type == "region":
                r_node.regions = [split_region_node(le_r, pivot, axis, dim)]
    return right


def split_point_node(node, pivot, axis):
    right = Node(node_type="points")
    right_points = [pt for pt in node.points if pt["point"][axis] >= pivot]
    node_points = [pt for pt in node.points if pt["point"][axis] < pivot]
    right.points = right_points
    node.points = node_points
    return right


def region_range(dim, regions):
    _range = [None for _ in range(dim)]
    for dim_idx in range(dim):
        if not regions:
            r0 = [-float("inf"), float("inf")]
        else:
            r0 = regions[0].range_bound[dim_idx]
        _range[dim_idx] = [r0[0], r0[1]]
        for re in regions[1:]:
            r = re.range_bound
            if r[dim_idx][0] < _range[dim_idx][0]:
                _range[dim_idx][0] = r[dim_idx][0]
            if r[dim_idx][1] > _range[dim_idx][1]:
                _range[dim_idx][1] = r[dim_idx][1]
    return _range


def overlapping_point(query, point):
    def overlaping_mm(amin, amax, bmin, bmax):
        return (
            (bmin <= amin <= bmax)
            or (bmin <= amax <= bmax)
            or (amin < bmin and amax > bmax)
        )

    for q, pt in zip(query, point):
        if not overlaping_mm(q[0], q[1], pt, pt):
            return False
    return True


def _test_query_():
    kdb_tree = KDBTree(dim=3)
    # kdb_tree.insert([0, 0, 0], 'a')
    # kdb_tree.insert([1, 0, 0], 'b')
    # kdb_tree.insert([0, 1, 0], 'c')
    # kdb_tree.insert([0, 0, 1], 'd')
    # kdb_tree.insert([1, 0, 1], 'e')
    # kdb_tree.insert([0, 1, 1], 'f')
    # kdb_tree.insert([1, 1, 0], 'g')
    # kdb_tree.insert([1, 1, 1], 'h')
    # kdb_tree.insert([2, 1, 0], 'i')
    num = 0
    for i in range(10):
        for j in range(10):
            for k in range(10):
                # print("insert:{},{}".format([i, j, k], num))
                kdb_tree.insert([i, j, k], str(num))
                num += 1
    return kdb_tree


if __name__ == "__main__":
    kdb_tree = _test_query_()
    result = kdb_tree.query([1, 1, 1])
    print(result)
