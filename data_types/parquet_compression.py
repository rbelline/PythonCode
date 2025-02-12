import os

import pyarrow.parquet as pq
import pandas as pd
import pyarrow as pa

from encoding import encode_image, read_text_file

FOLDER_PATH = "./random_files"
OUTPUT = "output.parquet"

# File extension definition
images_extensions = ["jpg", "jpeg", "png", "bmp", "gif",]
text_extensions = ["txt",]

all_files = []
# File iteration in the folder
for filename in os.listdir(FOLDER_PATH):
    # print(filename)
    file_path = os.path.join(FOLDER_PATH, filename)
    # print(file_path)
    if os.path.isfile(file_path):
        file_extension = filename.split(".")[-1].lower()
        # print(file_extension)
        if file_extension in images_extensions:
            image_content = encode_image(file_path)
            file_type = "image"
            content = image_content
        elif file_extension in text_extensions:
            text_content = read_text_file(file_path)
            file_type = "text"
            content = text_content
        else:
            continue
    
    # Append data
    all_files.append({"filename": filename, "file_type": file_type, "content": content})

# Convert data into a Panda data frame
data_frame = pd.DataFrame(all_files)
# Convert Panda data frame to PyArrow table
table = pa.Table.from_pandas(data_frame)
pq.write_table(table, OUTPUT, compression="snappy")

print(f"Paqruet file {OUTPUT} created successfully!")
        