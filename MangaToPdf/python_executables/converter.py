import os
from os import listdir
from os.path import isfile, join
import sys
import img2pdf
import functools
import zipfile
from PIL import Image
from PyPDF2 import PdfMerger

from bs4 import BeautifulSoup
import requests as req
import urllib.request
from urllib.request import Request, urlopen
from socket import timeout
import re

# Add option of "favourite/base" folder
#
#


# TODO: check volume and chapter order correctness #DONE
# TODO: make option to combine chapters into volumes (maybe without making of a big all-in-one file) #DONE
# TODO: optimize memory usage, delete image folders immediately after convertion
#       new algo:   foreach zip
#                       unpack zip -> remove exif -> pdf -> delete folder with unpacked zip
#                   pdfs -> volumes
#                   pdfs -> final_pdf
# TODO: make a normal human-usable menu, idk #DONE with WPF
# TODO: refactor code
# TODO: webp format of image (wepb -> jpg, or else it reaaly fucks with disk available space, 30Mb+ size pdfs...) #DONE

REMOVE_EXIF = True
MAKE_VOLUMES = True
MAKE_ALL_IN_ONE = False

def print_with_flush(a):
    print(a, end='\n', flush=True)

def load_img_mangakakalot(img_url, img_path):
    reqq = Request(url=img_url, headers={
                    'User-Agent': 'Mozilla/5.0',
                    'referer': 'https://mangakakalot.com/',
                    })
    f = open(img_path,'wb')
    f.write(urlopen(reqq).read())
    f.close()

def load_img_chapmanganato(img_url, img_path):
    reqq = Request(url=img_url, headers={
                    'User-Agent': 'Mozilla/5.0',
                    'referer': 'https://chapmanganato.com/',
                    })
    f = open(img_path,'wb')
    f.write(urlopen(reqq).read())
    f.close()

def load_img_manga_raw(img_url, img_path):
    try:
        reqq = Request(url=img_url, headers={'User-Agent': 'Mozilla/5.0'})
        f = open(img_path,'wb')
        f.write(urlopen(reqq, timeout=10).read())
        f.close()
    except timeout:
        raise Exception(f"timeout, no response from {img_url}")

def trim_image_name(name):
    if name.endswith(".jpeg" or ".webp"):
        return float(name[0:-5])
    return float(name[0:-4])

def simple_name_compare(name1, name2):
    chapter1 = float(name1.split()[-1])
    chapter2 = float(name2.split()[-1])
    if chapter1 - chapter2 > 0:
        return 1
    if chapter1 - chapter2 < 0:
        return -1
    return 0

def name_compare(name1, name2):
    name_as_args_arr = name1.split()
    start_index1 = name_as_args_arr.index("Том")
    volume1 = float(name_as_args_arr[start_index1 + 1])
    chapter1 = float(name_as_args_arr[start_index1 + 3])
    name_as_args_arr = name2.split()
    start_index2 = name_as_args_arr.index("Том")
    volume2 = float(name_as_args_arr[start_index2 + 1])
    chapter2 = float(name_as_args_arr[start_index2 + 3])
    if volume1 != volume2:
        return int(volume1 - volume2)
    return int(chapter1 - chapter2)

def remove_exif(img_path):
    try:
        image = Image.open(img_path)
        data = list(image.getdata())
        image_without_exif = Image.new(image.mode, image.size)
        image_without_exif.putdata(data)
        image_without_exif.save(img_path)
    except:
        print_with_flush("Could not remove exif data from image:", img_path)

def url_to_pdf():
    image_folder_name = "raw images"
    downloads_folder_name = "downloads"

    output_folder_path = input("Enter output folder path: ")

    manga_base_url = input("Enter base url: ")
    if "mangakakalot.com" in manga_base_url:
        manga_name = input("Enter manga name: ")
    elif "chapmanganato.com" in manga_base_url:
        manga_name = input("Enter manga name: ")
    else:
        manga_name = " ".join([s.capitalize() for s in manga_base_url.split('/')[-1].split('-')[0:-2]])

    begin_idx, end_idx = map(int, input("Enter interval a to b (both included) [a; b]: ").split(' '))
    for idx in range(begin_idx, end_idx + 1):
    #idxs = input("Enter chapter indexes (example: 1 2 2.1 2.2 3 4): ").split(' ')
    #for idx in idxs:
        manga_url = manga_base_url + str(idx)

        print_with_flush(f"\nReading from url: {manga_url}")
        resp = req.get(manga_url)
        chapter = idx

        soup = BeautifulSoup(resp.text, 'lxml')
        if "mangakakalot.com" in manga_base_url:
            # TODO
            pass
        elif "chapmanganato.com" in manga_base_url:
            image_urls_as_text = soup.find("div", {"class": "container-chapter-reader"}).find_all("img")
            image_urls = [tag['src'] for tag in image_urls_as_text]
            print_with_flush(image_urls)
        else:
            image_urls_as_text = soup.find("p", id="arraydata").text
            image_urls = image_urls_as_text.split(',')
        print_with_flush(f"\nEnd reading from url: {manga_url}")

        print_with_flush("\nDownloading images: ------------------------------")
        image_folder_path = join(output_folder_path, downloads_folder_name, f"{manga_name} Глава {chapter}")
        if not os.path.exists(image_folder_path):
            os.makedirs(image_folder_path)
        for img_url in image_urls:
            img_name = img_url.split('/')[-1]
            img_name = re.search(r'\d+', img_name).group() + "." + img_name.split('.')[-1]
            img_path = join(image_folder_path, img_name)
            loaded = False
            try:
                print_with_flush(f"\n<---loading {img_url}--->")
                if "mangakakalot.com" in manga_base_url:
                    load_img_mangakakalot(img_url, img_path)
                elif "chapmanganato.com" in manga_base_url:
                    load_img_chapmanganato(img_url, img_path)
                else:
                    load_img_manga_raw(img_url, img_path)
                print_with_flush(f"\n<---loaded {img_url}--->")
                loaded = True
            except Exception as e:
                print_with_flush(f"\n<---could not load {img_url}--->")
                print_with_flush(e)

            if REMOVE_EXIF and loaded:
                remove_exif(img_path)
        print_with_flush("\nEnd downloading images: --------------------------")

        print_with_flush("\nSorting images: ----------------------------------")
        correct_image_names = [i for i in listdir(image_folder_path) if i.endswith(".jpeg") or i.endswith(".png") or i.endswith(".jpg")]
        sorted_image_names = sorted(correct_image_names, key=trim_image_name)
        sorted_image_paths = [join(image_folder_path, i) for i in sorted_image_names]
        print_with_flush("\nEnd sorting images: ------------------------------")

        print_with_flush("\nImage to pdf conversion: -----------------------")
        pdf_chapter_path = join(output_folder_path, f"{manga_name} Глава {chapter}.pdf")
        with open(pdf_chapter_path, "wb") as f:
            f.write(img2pdf.convert(sorted_image_paths))
        print_with_flush("\nEnd image to pdf conversion: -------------------\n")

    # join chapters into volumes
    # TODO
    """print_with_flush("\nCollecting chapters into volumes: ----------")
    output_volume_folder_name = "volumes"
    output_volume_folder_path = join(output_folder_path, output_volume_folder_name)
    if not os.path.exists(output_volume_folder_path):
        os.makedirs(output_volume_folder_path)
    pdf_chapter_paths = sorted([name[:-4] for name in listdir(output_folder_path)
        if isfile(join(output_folder_path, name)) and name.endswith(".pdf")],
        key=functools.cmp_to_key(simple_name_compare))
    if not pdf_chapter_paths:
        print_with_flush("There are no pdf files")
        print_with_flush(f"<-- end of volume merge -->\n")
        return

    merger = PdfMerger()
    for pdf in pdf_chapter_paths:
        merger.append(join(output_folder_path, pdf) + ".pdf")

    merger.write(join(output_folder_path, f"{manga_name}.pdf"))
    merger.close()
    for chapter_path in pdf_chapter_paths:
        print_with_flush(f"<-- making volume {volume_idx} -->")
        merger = PdfMerger()

        for pdf in chapter_paths:
            print_with_flush(pdf)
            merger.append(pdf)

        merger.write(join(output_volume_folder_path, f"{manga_name} Том {volume_idx}.pdf"))
        merger.close()
        print_with_flush(f"<-- volume {volume_idx} done -->\n")"""
    if MAKE_ALL_IN_ONE:
        # join all chapters into one pdf file
        print_with_flush("\nCollecting chapters into one pdf file: -----")
        print_with_flush(f"<-- merging chapters -->")
        pdf_chapter_paths = sorted([name[:-4] for name in listdir(output_folder_path) if isfile(join(output_folder_path, name)) and name.endswith(".pdf")], key=functools.cmp_to_key(simple_name_compare))
        if not pdf_chapter_paths:
            print_with_flush("There are no pdf files")
            print_with_flush(f"<-- end of merge -->\n")
            return

        merger = PdfMerger()
        for pdf in pdf_chapter_paths:
            merger.append(join(output_folder_path, pdf) + ".pdf")

        merger.write(join(output_folder_path, f"{manga_name}.pdf"))
        merger.close()
        print_with_flush(f"<-- chapters are merged -->\n")


def zip_to_pdf(zip_folder_path):
    if zip_folder_path == "":
        print_with_flush("path is empty")
        return

    output_folder_name = 'output'
    output_folder_path = join(zip_folder_path, output_folder_name)

    # filter zips from all contents of the directory
    zip_archive_names = [i for i in listdir(zip_folder_path) if zipfile.is_zipfile(join(zip_folder_path, i))]

    print_with_flush("\nZIP archives: ------------------------------")
    for s in sorted(zip_archive_names, key=functools.cmp_to_key(name_compare)):
        print_with_flush(s)

    # extract each zip archive as a folder into /output
    print_with_flush("\nExtraction: --------------------------------")
    unzipped_folder_name = "unzipped"
    output_unzip_folder_path = join(zip_folder_path, output_folder_name, unzipped_folder_name)
    for filename in sorted(zip_archive_names, key=functools.cmp_to_key(name_compare)):
        print_with_flush(f"<-- extracting {filename} -->")
        with zipfile.ZipFile(join(zip_folder_path, filename), 'r') as zip_ref:
            zip_ref.extractall(join(output_unzip_folder_path, filename[0:-18]))
        print_with_flush(f"<-- extracted  {filename} -->\n")
    print_with_flush("[PROGRESS] 10")
    
    # go through each extracted folder and collect all jpeg into a pdf file, which goes to /output
    print_with_flush("\nImage to pdf conversion: -------------------")
    manga_name = ""
    volume_dict = {}
    if os.path.exists(output_unzip_folder_path):
        image_directories = sorted([i for i in listdir(output_unzip_folder_path) if not isfile(join(output_unzip_folder_path, i)) and len(i.split()) > 4], key=functools.cmp_to_key(name_compare))
        count = 0
        for directory_name in image_directories:
            count += 1
            image_directory_path = join(output_unzip_folder_path, directory_name)
            print_with_flush(f"<-- converting {image_directory_path} -->")

            name_as_args_arr = directory_name.split()
            start_index = name_as_args_arr.index("Том")
            manga_name = " ".join(name_as_args_arr[0:start_index])
            volume = name_as_args_arr[start_index + 1]
            if not volume in volume_dict.keys():
                volume_dict[volume] = []
            chapter = name_as_args_arr[start_index + 3]

            correct_image_names = [i for i in listdir(image_directory_path) if i.endswith(".jpeg") or i.endswith(".jpg") or i.endswith(".png") or i.endswith(".webp")]
            # convert all to jpg
            for image_path in [join(image_directory_path, i) for i in correct_image_names]:
                try:
                    if (image_path.endswith(".webp")):
                        image = Image.open(image_path).convert("RGB")
                        data = list(image.getdata())
                        image_without_exif = Image.new(image.mode, image.size)
                        image_without_exif.putdata(data)
                        image_without_exif.save(f"{image_path[:-5]}.jpeg", "jpeg")
                    elif (image_path.endswith(".png")):
                        image = Image.open(image_path).convert("RGB")
                        data = list(image.getdata())
                        image_without_exif = Image.new(image.mode, image.size)
                        image_without_exif.putdata(data)
                        image_without_exif.save(f"{image_path[:-4]}.jpeg", "jpeg")
                    elif (image_path.endswith(".jpg")):
                        image = Image.open(image_path).convert("RGB")
                        data = list(image.getdata())
                        image_without_exif = Image.new(image.mode, image.size)
                        image_without_exif.putdata(data)
                        image_without_exif.save(f"{image_path[:-4]}.jpeg", "jpeg")
                except:
                    print_with_flush("Could not convert to jpeg or remove exif data from", image_path)

            correct_image_names = [i for i in listdir(image_directory_path) if i.endswith(".jpeg")]
            sorted_image_names = sorted(correct_image_names, key=trim_image_name)
            sorted_image_paths = [join(image_directory_path, i) for i in sorted_image_names]
            pdf_chapter_path = join(output_folder_path, f"{manga_name} Том {volume} Глава {chapter}.pdf")
            with open(pdf_chapter_path, "wb") as f:
                f.write(img2pdf.convert(sorted_image_paths))
            volume_dict[volume].append(pdf_chapter_path)

            print_with_flush(f"<-- converted {image_directory_path} -->\n")
            print_with_flush(f"[PROGRESS] {int(10 + 70 / len(image_directories) * count)}")
    print_with_flush("[PROGRESS] 80")

    # join chapters into volumes
    if (MAKE_VOLUMES):
        print_with_flush("\nCollecting chapters into volumes: ----------")
        output_volume_folder_name = "volumes"
        output_volume_folder_path = join(output_folder_path, output_volume_folder_name)
        if not os.path.exists(output_volume_folder_path):
            os.makedirs(output_volume_folder_path)
        for volume_idx, chapter_paths in volume_dict.items():
            print_with_flush(f"<-- making volume {volume_idx} -->")
            merger = PdfMerger()

            for pdf in chapter_paths:
                print_with_flush(pdf)
                merger.append(pdf)

            merger.write(join(output_volume_folder_path, f"{manga_name} Том {volume_idx}.pdf"))
            merger.close()
            print_with_flush(f"<-- volume {volume_idx} done -->\n")
    print_with_flush("[PROGRESS] 90")

    if MAKE_ALL_IN_ONE:
        # join all chapters into one pdf file
        print_with_flush("\nCollecting chapters into one pdf file: -----")
        print_with_flush(f"<-- merging chapters -->")
        pdf_chapter_paths = sorted([name[:-4] for name in listdir(output_folder_path) if isfile(join(output_folder_path, name)) and "Том" in name and name.endswith(".pdf")], key=functools.cmp_to_key(name_compare))
        if not pdf_chapter_paths:
            print_with_flush("There are no pdf files")
            print_with_flush(f"<-- end of merge -->\n")
            return

        if manga_name == "":
            start_index = pdf_chapter_paths[0].split().index("Том")
            manga_name = " ".join(pdf_chapter_paths[0].split()[0:start_index])

        merger = PdfMerger()
        for pdf in pdf_chapter_paths:
            merger.append(join(output_folder_path, pdf) + ".pdf")

        merger.write(join(output_folder_path, f"{manga_name}.pdf"))
        merger.close()
        print_with_flush(f"<-- chapters are merged -->\n")
    print_with_flush("[PROGRESS] 100")


def main():
    args = sys.argv[1:]
    if (len(args) < 2):
        print_with_flush("Not enough arguments")
        return
    if (len(args) == 2):
        use_url_or_zip = args[0]
        if use_url_or_zip.lower()[0] == 'u':
            print_with_flush("Not enough arguments for downloading from url")
            return
        if use_url_or_zip.lower()[0] == 'z':
            # mangalib folder with zips
            zip_to_pdf(args[1])
            return
    if (len(args) == 4):
        use_url_or_zip = args[0]
        if use_url_or_zip.lower()[0] == 'u':
            # manga-raw load from url
            url_to_pdf(args[1], args[2], args[3])
            return
        if use_url_or_zip.lower()[0] == 'z':
            print_with_flush("Too many arguments for downloading from zips")
            return
    else:
        print_with_flush("Wrong number of arguments")
        return


if __name__ == "__main__":
    main()


