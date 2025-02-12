import base64

# Function to encode images
def encode_image(image_file_path):
    with open(image_file_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")
    
# Function to read text files
def read_text_file(txt_file_path):
    with open(txt_file_path, "r", encoding="utf-8") as txt_file:
        return txt_file.read()