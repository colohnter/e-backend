# e-backend

This repository provides a small Python library to bootstrap two standalone
PostgreSQL instances into a simple master/slave cluster.

The `pg_cluster` package exposes `PGInstance` and `ClusterManager` classes. The
manager modifies configuration files and uses `pg_basebackup` to create a standby.

Example:

```python
from pg_cluster import PGInstance, ClusterManager

master = PGInstance(data_dir="/var/lib/postgresql/15/main")
slave = PGInstance(data_dir="/var/lib/postgresql/15/slave")

cluster = ClusterManager(master, slave)
cluster.init_master()
cluster.init_slave()
cluster.start_instances()
```

**Note:** This code was not executed in this environment. You may need to adapt
paths and parameters for your setup.

