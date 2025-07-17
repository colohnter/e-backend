from dataclasses import dataclass
import os
import subprocess

@dataclass
class PGInstance:
    """Information about a PostgreSQL instance."""
    data_dir: str
    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"

class ClusterSetupError(Exception):
    pass

class ClusterManager:
    """Simple manager to convert standalone instances into master/slave."""

    def __init__(self, master: PGInstance, slave: PGInstance,
                 repl_user: str = "replicator", repl_pass: str = "replica"):
        self.master = master
        self.slave = slave
        self.repl_user = repl_user
        self.repl_pass = repl_pass

    def _run(self, cmd: str):
        subprocess.run(cmd, shell=True, check=True)

    def init_master(self):
        """Configure master instance for replication."""
        config = os.path.join(self.master.data_dir, "postgresql.conf")
        with open(config, "a", encoding="utf-8") as f:
            f.write("\nwal_level = replica\n")
            f.write("max_wal_senders = 10\n")
            f.write("wal_keep_size = 64\n")
        hba = os.path.join(self.master.data_dir, "pg_hba.conf")
        with open(hba, "a", encoding="utf-8") as f:
            f.write(f"host replication {self.repl_user} {self.slave.host}/32 md5\n")
        create_user = (
            f"psql -h {self.master.host} -p {self.master.port} -U {self.master.user} "
            f"-c \"CREATE ROLE {self.repl_user} WITH REPLICATION LOGIN ENCRYPTED PASSWORD '{self.repl_pass}';\""
        )
        self._run(create_user)

    def init_slave(self):
        """Bootstrap slave using pg_basebackup and set standby signal."""
        self._run(f"pg_ctl -D {self.slave.data_dir} stop")
        self._run(f"rm -rf {self.slave.data_dir}/*")
        basebackup = (
            f"pg_basebackup -h {self.master.host} -p {self.master.port} "
            f"-U {self.repl_user} -D {self.slave.data_dir} -Fp -Xs -P -R"
        )
        env = os.environ.copy()
        env["PGPASSWORD"] = self.repl_pass
        subprocess.run(basebackup, shell=True, check=True, env=env)
        standby = os.path.join(self.slave.data_dir, "postgresql.auto.conf")
        with open(standby, "a", encoding="utf-8") as f:
            f.write(f"primary_conninfo = 'host={self.master.host} port={self.master.port} user={self.repl_user} password={self.repl_pass}'\n")

    def start_instances(self):
        self._run(f"pg_ctl -D {self.master.data_dir} restart")
        self._run(f"pg_ctl -D {self.slave.data_dir} start")
