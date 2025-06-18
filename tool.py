# coding: utf-8
from PIL import Image
import os
import sys
import json
from datetime import datetime
from ImageProcess import Graphics

# 定义压缩比，数值越大，压缩越小
SIZE_normal = 1.0
SIZE_small = 1.5
SIZE_more_small = 2.0
SIZE_more_small_small = 3.0


def make_directory(directory):
    """创建目录"""
    os.makedirs(directory)


def directory_exists(directory):
    """判断目录是否存在"""
    if os.path.exists(directory):
        return True
    else:
        return False


def list_img_file(directory):
    """列出目录下所有文件，并筛选出图片文件列表返回"""
    old_list = os.listdir(directory)
    # print old_list
    new_list = []
    for filename in old_list:
        try:
            name, fileformat = filename.split(".")
            if fileformat.lower() in ["jpg", "png", "gif", "jpeg"]:
                new_list.append(filename)
        except ValueError:
            # Handles files without extensions, like .DS_Store
            continue
    # print new_list
    return new_list


def print_help():
    print("""
    This program helps compress many image files
    you can choose which scale you want to compress your img(jpg/png/etc)
    1) normal compress(4M to 1M around)
    2) small compress(4M to 500K around)
    3) smaller compress(4M to 300K around)
    4) smallest compress (4M to 150K around)
    """)


def compress(choose, des_dir, src_dir, file_list):
    """
    Crops the original image to a square from the center, then resizes it to create a thumbnail.
    The original image in src_dir remains unmodified.

    参数
    -----------
    choose: str
            选择压缩的比例，有4个选项，越大压缩后的图片越小
    """
    if choose == '1':
        scale = SIZE_normal
    elif choose == '2':
        scale = SIZE_small
    elif choose == '3':
        scale = SIZE_more_small
    elif choose == '4':
        scale = SIZE_more_small_small
    else:
        # Default to normal size if input is invalid
        scale = SIZE_normal

    for infile in file_list:
        try:
            # Open the original image
            img = Image.open(os.path.join(src_dir, infile))

            # --- Cropping Logic ---
            (x, y) = img.size
            if x > y:
                # Crop the center of the image (landscape)
                left = (x - y) / 2
                top = 0
                right = left + y
                bottom = y
            elif y > x:
                # Crop the center of the image (portrait)
                left = 0
                top = (y - x) / 2
                right = x
                bottom = top + x
            else:
                # Image is already square
                left, top, right, bottom = 0, 0, x, y

            # Crop the image in memory
            crop_img = img.crop((left, top, right, bottom))

            # --- Resizing Logic (Thumbnail) ---
            # Calculate the target size for the thumbnail based on the scale
            base_size = min(x, y)
            thumb_size = (int(base_size / scale), int(base_size / scale))

            # Resize the cropped image using LANCZOS for better quality (replaces ANTIALIAS)
            crop_img = crop_img.resize(thumb_size, Image.Resampling.LANCZOS)

            # Save the final cropped and resized thumbnail
            crop_img.save(os.path.join(des_dir, infile))
        except Exception as e:
            print(f"Could not process {infile}. Error: {e}")


def compress_photo():
    '''调用压缩图片的函数
    '''
    src_dir, des_dir = "photos/", "min_photos/"

    if not directory_exists(src_dir):
        print(f"Source directory '{src_dir}' not found.")
        make_directory(src_dir)
        print(f"Created directory '{src_dir}'. Please add photos and run again.")
        return

    if not directory_exists(des_dir):
        make_directory(des_dir)

    file_list_src = list_img_file(src_dir)
    file_list_des = list_img_file(des_dir)

    '''如果已经压缩了，就不再压缩'''
    files_to_compress = [f for f in file_list_src if f not in file_list_des]

    if not files_to_compress:
        print("No new photos to compress.")
        return

    print(f"Found {len(files_to_compress)} new photos to compress.")
    compress('4', des_dir, src_dir, files_to_compress)


def handle_photo():
    '''根据图片的文件名处理成需要的json格式的数据

    -----------
    最后将data.json文件存到博客的source/photos文件夹下
    '''
    src_dir = "photos/"
    if not directory_exists(src_dir):
        print(f"Source directory '{src_dir}' not found for JSON handling.")
        return

    file_list = list_img_file(src_dir)
    list_info = []

    # Group photos by month
    photos_by_month = {}
    for filename in file_list:
        try:
            date_str, info_part = filename.split("_", 1)
            info, _ = os.path.splitext(info_part)

            # Create a datetime object to handle dates
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            year_month = date_obj.strftime("%Y-%m")

            if year_month not in photos_by_month:
                photos_by_month[year_month] = {
                    'year': date_obj.year,
                    'month': date_obj.month,
                    'photos': []
                }

            photos_by_month[year_month]['photos'].append({
                'link': filename,
                'text': info,
                'type': 'image'
            })
        except ValueError:
            print(f"Skipping '{filename}'. Filename must be in 'YYYY-MM-DD_text.ext' format.")
            continue

    # Convert grouped photos to the final list format
    for key, value in photos_by_month.items():
        photo_arr = {
            'year': value['year'],
            'month': value['month'],
            'link': [p['link'] for p in value['photos']],
            'text': [p['text'] for p in value['photos']],
            'type': [p['type'] for p in value['photos']],
        }
        list_info.append({"date": key, "arr": photo_arr})

    # Sort the list by date in descending order
    list_info = SortDict(list_info)

    final_dict = {"list": list_info}
    json_path = os.path.join("../Blog/source/album/data.json")

    # Ensure the directory for the JSON file exists
    os.makedirs(os.path.dirname(json_path), exist_ok=True)

    with open(json_path, "w") as fp:
        json.dump(final_dict, fp, indent=4)
    print(f"JSON data successfully written to {json_path}")


# 冒泡排序
def SortDict(list_info):
    n = len(list_info)
    for i in range(n):
        for j in range(0, n - i - 1):
            date1 = datetime.strptime(list_info[j]['date'], "%Y-%m")
            date2 = datetime.strptime(list_info[j + 1]['date'], "%Y-%m")
            if date1 < date2:
                list_info[j], list_info[j + 1] = list_info[j + 1], list_info[j]
    return list_info


def git_operation():
    '''
    git 命令行函数，将仓库提交

    ----------
    需要安装git命令行工具，并且添加到环境变量中
    '''
    os.system('git add --all')
    os.system('git commit -m "add photos"')
    os.system('git push origin master')


if __name__ == "__main__":
    compress_photo()  # Compresses new photos into thumbnails (cropped to square)
    handle_photo()  # Processes photo metadata into JSON for the blog
    # To enable git operations, uncomment the line below
    # git_operation()    # Commits changes to the git repository