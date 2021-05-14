from numpy.core.numeric import normalize_axis_tuple
from kdb_tree import Node
from copy import deepcopy


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


def split_region_node(node_parent, pivot, axis, dim):
    rrange = region_range(dim, node_parent.regions)
    rrange[axis][0] = pivot
    right = Node(node_type="region")
    right.dim_range = rrange

    left = node_parent
    i = 0

    while i < len(node_parent.regions):
        le_r = node_parent.regions[i]
        if le_r.range_bound[axis][1] < pivot:
            i += 1
            continue
        elif le_r.range_bound[axis][0] >= pivot:
            right.regions.append(le_r)
            left.regions.remove(le_r)
            i -= 1
        else:
            r_node = Node()
            rright = deepcopy(le_r.range_bound)
            rright[axis][0] = pivot
            r_node.range_bound = rright
            right.regions.append(rright)

            rleft = le_r
            rleft.range_bound[axis][1] = pivot
            if le_r.node_type == "points":
                r_node = split_point_node(r_node, pivot, axis)
            elif le_r.node_type == "region":
                r_node.regions = [split_region_node(le_r, pivot, axis, dim)]

    return right


def split_point_node(node, pivot, axis):
    right = Node(node_type="points")
    for pt in node.points:
        if pt[axis] >= pivot:
            right.points.append(pt)
            node.points.remove(pt)


def region_range(dim, regions):
    _range = [None for _ in range(dim)]
    for dim_idx in range(dim):
        if regions:
            r0 = [-float("inf"), float("inf")]
        else:
            regions[0].range_bound[dim_idx]
        _range[dim_idx] = [r0[0], r0[1]]
        for re in regions:
            r = re.range_bound
            if r[dim_idx][0] < _range[dim_idx][0]:
                _range[dim_idx][0] = r[dim_idx][0]
            if r[dim_idx][1] < _range[dim_idx][1]:
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
        if not overlaping_mm(q[0], q[1], pt[0], pt[1]):
            return False
    return True
