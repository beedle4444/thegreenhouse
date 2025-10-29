import os
from PIL import Image
from flask import url_for, current_app

def add_profile_pic(pic_upload, username, crop_data=None):

    # Handle both file upload objects and file paths
    if hasattr(pic_upload, 'filename'):
        # It's a file upload object
        filename = pic_upload.filename
        image_source = pic_upload
    else:
        # It's a file path string
        filename = os.path.basename(pic_upload)
        image_source = pic_upload
    
    ext_type = filename.split('.')[-1].lower()
    
    # Support GIF, but convert to PNG for consistency
    if ext_type == 'gif':
        ext_type = 'png'
    
    storage_filename = str(username) + '.' + ext_type
    filepath = os.path.join(current_app.root_path, 'static/profile_pics', storage_filename)

    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    output_size = (300, 300)

    pic = Image.open(image_source)
    
    # Convert to RGB if necessary (for GIFs, etc.)
    if pic.mode in ('RGBA', 'LA', 'P'):
        pic = pic.convert('RGB')
    
    # Apply cropping if crop data is provided
    if crop_data:
        x, y, width, height = crop_data
        pic = pic.crop((x, y, x + width, y + height))
    
    # Resize to square aspect ratio
    pic.thumbnail(output_size, Image.Resampling.LANCZOS)
    
    # Create a square image with white background
    square_pic = Image.new('RGB', output_size, (255, 255, 255))
    
    # Calculate position to center the image
    x_offset = (output_size[0] - pic.size[0]) // 2
    y_offset = (output_size[1] - pic.size[1]) // 2
    square_pic.paste(pic, (x_offset, y_offset))
    
    square_pic.save(filepath, 'PNG', quality=95)

    return storage_filename