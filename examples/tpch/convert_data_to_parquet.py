# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""
This is a utility function that will consumer the data generated by dbgen from TPC-H and convert
it into a parquet file with the column names as expected by the TPC-H specification. It assumes
the data generated resides in a path ../../benchmarks/tpch/data relative to the current file,
as will be generated by the script provided in this repository.
"""

import os
import pyarrow
import datafusion

ctx = datafusion.SessionContext()

all_schemas = {}

all_schemas["customer"] = [
    ("C_CUSTKEY", pyarrow.int64()),
    ("C_NAME", pyarrow.string()),
    ("C_ADDRESS", pyarrow.string()),
    ("C_NATIONKEY", pyarrow.int64()),
    ("C_PHONE", pyarrow.string()),
    ("C_ACCTBAL", pyarrow.decimal128(15, 2)),
    ("C_MKTSEGMENT", pyarrow.string()),
    ("C_COMMENT", pyarrow.string()),
]

all_schemas["lineitem"] = [
    ("L_ORDERKEY", pyarrow.int64()),
    ("L_PARTKEY", pyarrow.int64()),
    ("L_SUPPKEY", pyarrow.int64()),
    ("L_LINENUMBER", pyarrow.int32()),
    ("L_QUANTITY", pyarrow.decimal128(15, 2)),
    ("L_EXTENDEDPRICE", pyarrow.decimal128(15, 2)),
    ("L_DISCOUNT", pyarrow.decimal128(15, 2)),
    ("L_TAX", pyarrow.decimal128(15, 2)),
    ("L_RETURNFLAG", pyarrow.string()),
    ("L_LINESTATUS", pyarrow.string()),
    ("L_SHIPDATE", pyarrow.date32()),
    ("L_COMMITDATE", pyarrow.date32()),
    ("L_RECEIPTDATE", pyarrow.date32()),
    ("L_SHIPINSTRUCT", pyarrow.string()),
    ("L_SHIPMODE", pyarrow.string()),
    ("L_COMMENT", pyarrow.string()),
]

all_schemas["nation"] = [
    ("N_NATIONKEY", pyarrow.int64()),
    ("N_NAME", pyarrow.string()),
    ("N_REGIONKEY", pyarrow.int64()),
    ("N_COMMENT", pyarrow.string()),
]

all_schemas["orders"] = [
    ("O_ORDERKEY", pyarrow.int64()),
    ("O_CUSTKEY", pyarrow.int64()),
    ("O_ORDERSTATUS", pyarrow.string()),
    ("O_TOTALPRICE", pyarrow.decimal128(15, 2)),
    ("O_ORDERDATE", pyarrow.date32()),
    ("O_ORDERPRIORITY", pyarrow.string()),
    ("O_CLERK", pyarrow.string()),
    ("O_SHIPPRIORITY", pyarrow.int32()),
    ("O_COMMENT", pyarrow.string()),
]

all_schemas["part"] = [
    ("P_PARTKEY", pyarrow.int64()),
    ("P_NAME", pyarrow.string()),
    ("P_MFGR", pyarrow.string()),
    ("P_BRAND", pyarrow.string()),
    ("P_TYPE", pyarrow.string()),
    ("P_SIZE", pyarrow.int32()),
    ("P_CONTAINER", pyarrow.string()),
    ("P_RETAILPRICE", pyarrow.decimal128(15, 2)),
    ("P_COMMENT", pyarrow.string()),
]

all_schemas["partsupp"] = [
    ("PS_PARTKEY", pyarrow.int64()),
    ("PS_SUPPKEY", pyarrow.int64()),
    ("PS_AVAILQTY", pyarrow.int32()),
    ("PS_SUPPLYCOST", pyarrow.decimal128(15, 2)),
    ("PS_COMMENT", pyarrow.string()),
]

all_schemas["region"] = [
    ("r_REGIONKEY", pyarrow.int64()),
    ("r_NAME", pyarrow.string()),
    ("r_COMMENT", pyarrow.string()),
]

all_schemas["supplier"] = [
    ("S_SUPPKEY", pyarrow.int64()),
    ("S_NAME", pyarrow.string()),
    ("S_ADDRESS", pyarrow.string()),
    ("S_NATIONKEY", pyarrow.int32()),
    ("S_PHONE", pyarrow.string()),
    ("S_ACCTBAL", pyarrow.decimal128(15, 2)),
    ("S_COMMENT", pyarrow.string()),
]

curr_dir = os.path.dirname(os.path.abspath(__file__))
for filename, curr_schema in all_schemas.items():

    # For convenience, go ahead and convert the schema column names to lowercase
    curr_schema = [(s[0].lower(), s[1]) for s in curr_schema]

    # Pre-collect the output columns so we can ignore the null field we add
    # in to handle the trailing | in the file
    output_cols = [r[0] for r in curr_schema]

    curr_schema = [ pyarrow.field(r[0], r[1], nullable=False) for r in curr_schema]

    # Trailing | requires extra field for in processing
    curr_schema.append(("some_null", pyarrow.null()))

    schema = pyarrow.schema(curr_schema)

    source_file = os.path.abspath(
        os.path.join(curr_dir, f"../../benchmarks/tpch/data/{filename}.csv")
    )
    dest_file = os.path.abspath(os.path.join(curr_dir, f"./data/{filename}.parquet"))

    df = ctx.read_csv(source_file, schema=schema, has_header=False, delimiter="|")

    df = df.select_columns(*output_cols)

    df.write_parquet(dest_file, compression="snappy")
