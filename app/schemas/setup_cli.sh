export PGUSER=${PGUSER:-postgres}
export PGPASSWORD=${PGPASSWORD:-postgres}
export PGHOST=${PGHOST:-localhost}
export PGPORT=${PGPORT:-5432}
export PGDATABASE=${PGDATABASE:-perpustakaan_digital}
export MONGO_URI=${MONGO_URI:-"mongodb://localhost:27017/perpustakaan_digital"}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -f "$SCRIPT_DIR/postgresql_schema.sql"

mongosh "$MONGO_URI" "$SCRIPT_DIR/mongodb_schema.js"
