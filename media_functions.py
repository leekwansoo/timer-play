# functions to handle media files
def is_valid_media_file(file):
    valid_extensions = ['mp4', 'avi', 'mov', 'mkv', 'webm', 'jpg', 'png', 'jpeg']
    file_extension = file.name.split('.')[-1].lower()
    return file_extension in valid_extensions