import os

import pyarrow.parquet as pq
import pandas as pd
import pyarrow as pa

def upload_folder_async(folder_path: str):
    all_files = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            with open(file_path, 'rb') as f:
                data = f.read()
                all_files.append({'file_name': file, 'file_path': file_path, 'content': data})

    df = pd.DataFrame(all_files)
    table = pa.Table.from_pandas(df=df)
    tmp_file=open(file="./tmp.file", mode="wb")
    pq.write_table(table, tmp_file, compression='snappy')