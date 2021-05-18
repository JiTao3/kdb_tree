## KDB TREE

### KDB TREE

In-memory kdb tree impletemention. [JS implementation](https://github.com/peermaps/kdb-tree)

### API

```python
kdb_tree = KDBTree(dim=3)
kdb_tree.insert([i, j, k], 'num')
# point query
result = kdb_tree.query([1, 1, 1])
# range query
result = kdb_tree.query([[il, ih], [jl, jh], [kl, kh]])
```
