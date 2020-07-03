
## DOWNLOAD ALL VIDEOS
import requests
import re
from urllib.parse import quote as url_quote # unquote
import shutil
from pathlib import Path
import csv
import os
import time
from feedgen.feed import FeedGenerator
import re
import logging
import yaml
from easydict import EasyDict as edict

# taylorarchibald.com/podcasts => "/media/taylor/Flash128/Podcasts"
# taylorarchibald.com/podcasts/data/this_podcast => "/media/taylor/Flash128/Downloads/this_podcasts"

"""
sudo apt-get install exfat-fuse
sudo apt-get install exfat-utils

mkdir /media/Flash128
sudo mount /dev/sda5 /media/Flash128

"""

# PREFIX = "/media/taylor/Flash128/"
# HOME_FOLDER = "" # the public datastructure; URL mirrors directory
# DATA = PREFIX + "Downloads" # different prefix

## LOCAL_DRIVE_STORAGE_PATH_PREFIX = /home/html/podcasts...
## URL_PATH_PREFIX = WEBSITE/podcasts...

logger = logging.getLogger("root")
hyperlink='<a href="{}">{}</a>'

def clean_quote(string):
    return url_quote(clean(string))

def clean(string):
    new = re.sub(r'- .\W+', '', string) # .replace(" - ","_")
    return new

def download_videos(root = Path(r"/home/taylor/Desktop/Naturally Slim")):
    root = Path(root)
    input("Are you sure you want to download all videos?")

    for week in range(0):
        output_folder = root / f"Week {week}"
        output_folder.mkdir(parents=True, exist_ok=True)
        for video in range(1, 20):
            possible_formats = []
            possible_formats.append(
                f"https://acap.vo.llnwd.net/v1/ns4videos/foundations/week{week}_4.5/v4.5_week_{week:02d}_{video:02d}.mp4")
            possible_formats.append(
                f"https://acap.vo.llnwd.net/v1/ns4videos/foundations/week{week}/V4_WEEK_{week:02d}_{video:02d}.mp4")
            video_path = output_folder / f"{week}-{video}.mp4"

            if video_path.exists():
                continue

            for i, url in enumerate(possible_formats):
                r = requests.get(url)
                if r.ok:
                    video_path.open("wb").write(r.content)
                    break

                if i + 1 == len(possible_formats):
                    print(f"Video {week, video} didn't work")
            time.sleep(10)


def rename_videos(root = Path(r"/media/BYUCS/public_html/books/NaturallySlim/audio")):
    root = Path(root)
    input("Are you sure you want to rename all videos?")

    for f in root.rglob("*.mp3"):
        try:
            # week = f.parent.name.split()[1]
            # video = f.name.split()[1]
            week, video = [int(x) for x in f.stem.split("-")]
            print(week, video)
            shutil.move(f, root / f"{week:02d}-{video:02d}.mp3")
        except Exception as e:
            print(e)
            continue

def create_toc(title, podcast_root, podcast_xml_location, audio_root=None, audio_files_path=None, image=None, html_root="http://fife.entrydns.org/podcasts"):
    """

    Args:
        title:
        podcast_xml_location:
        audio_files_path:
        image_extension: extension for image; should be same name as title
        html_root:

    Returns:

    """
    podcast_xml_location = Path(podcast_xml_location)
    audio_files_path = Path(audio_files_path) if audio_files_path else podcast_xml_location
    csv_file = Path(podcast_xml_location / "TOC.csv")
    html_sub = f"{html_root}/{clean_quote(podcast_xml_location.relative_to(podcast_root).as_posix())}"
    html_audio_sub = f"{html_root}/podcasts/data/{url_quote(audio_files_path.relative_to(audio_root).as_posix())}"
    title_url = clean_quote(title)

    if not image:
        image = find_image(audio_files_path)
        if image:
            image = html_audio_sub + image.relative_to(audio_files_path).as_posix()
        else:
            image = find_image(podcast_xml_location);
            if image:
                image = html_sub + image.relative_to(podcast_xml_location).as_posix()
            else:
                image = html_sub + title_url + ".png"

    d = {"Series": title, "Title": title, "Link": f"{html_audio_sub}", "Image": f"{html_sub}/{clean_quote(image)}"}
    i = 0
    with csv_file.open("w") as f:
        writer = csv.writer(f)
        writer.writerow(d.keys())

        fs = []
        for f in (audio_files_path).rglob("*"):
            if is_audio_file(f):
                fs.append(f)
        fs.sort()

        for i, f in enumerate(fs):
            f_relative_path = str(f.relative_to(audio_files_path)) # f.name
            link = f'{d["Link"]}/{clean_quote(f_relative_path)}'
            title = f"{d['Title']} {f.stem}"
            line = d["Series"], title, link, d["Image"]
            writer.writerow(line)

    print(f"Found {i + 1} files.")
    return d

def add_episode(fg, episode_link, name, series, image_url=None):
    fe = fg.add_entry()
    fe.id(name)
    fe.title(name)
    fe.description(series)
    fe.enclosure(episode_link, 0, 'audio/mpeg')
    fe.link(href=episode_link, rel='alternate')

def open_csv(file_path, encoding="utf-8-sig"):
    # global file_list
    file_list = []
    with open(file_path, 'r', encoding=encoding) as csvfile:
        spamreader = csv.reader(csvfile)
        for row in spamreader:
            file_list.append(row)
    if file_list[0][0] == "Series":
        file_list = file_list[1:]  # remove header
    return file_list

def open_csv_as_dict(file_path, encoding="utf-8-sig"):
    output = []
    with open(file_path, "r", encoding=encoding) as f:
        records = csv.DictReader(f)
        for row in records:
            output.append(row)
    return output


def convert_link2(link):
    print(link)
    id = re.search("\?id=([0-9A-Za-z_]+)", link).group(1)
    print(id)
    link = "https://drive.google.com/uc?export=download&id=" + id
    return link

def create_podcast(title, podcast_root, podcast_folder=None, toc_path=None, html_root = r"https://students.cs.byu.edu/~tarch",
                   category="Literature", description="N/A", alphabetize=True, image_link=None, google_drive=True, 
                   reverse_order=True, name="podcast.xml", output_folder_root=None):
    
    """
    Creates a .XML file of the podcast

    podcast_root: /home/pi/public_html/podcasts - needed to calculate podcast folder relative to root so URLs are correct
    podcast_folder: /home/pi/public_html/podcasts/Brandon Sanderson - Infinity Blade Redemption (Unabridged)


    output_folder_root: usually podcast folder, could be somewhere else though;
    """
    print(podcast_root)
    print(podcast_folder)
    # With reverse order, we make "Chapter 1" be the most recent entry
    # Open CSV
    if not podcast_folder:
        podcast_folder = Path(podcast_root) / title
    if not toc_path:
        toc_path = Path(podcast_folder) / "TOC.csv"
    if not output_folder_root:
        output_folder_root = podcast_root

    episode_list = open_csv_as_dict(toc_path)

    #Create RSS feed
    fg = FeedGenerator()
    fg.load_extension('podcast')
    fg.podcast.itunes_category(category)
    fg.id(title.replace(" ", ""))
    fg.title(title)
    fg.author( {'name':'TheFrostyBoss','email':'TheFrostyBoss@gmail.com'} )
    fg.link( href="taylorarchibald.com", rel='alternate' )
    #fg.subtitle('This is a cool feed!')
    fg.description(description)

    # Sort the list
    if alphabetize:
        episode_list = sorted(episode_list, key = lambda x: x["Title"])
        #print(episode_list)
    if reverse_order:
        episode_list = episode_list[::-1]

    for episode in episode_list:
        add_episode(fg, episode["Link"], episode["Title"], episode["Series"], episode["Image"])
    image_url = image_link if not image_link is None else episode["Image"]
    fg.image(url=image_url, title=None, link=None, width=None, height=None, description=None)

    fg.rss_str(pretty=True)

    # Add podcast name to path, create if needed
    relative_path = Path(podcast_folder).relative_to(podcast_root) / name

    output = Path(output_folder_root) / relative_path
    output.parent.mkdir(exist_ok=True, parents=True)
    fg.rss_file(str(output))

    if google_drive:
        link1 = input("Upload your podcast XML to Google drive. What is the download link for the podcast.xml? (it should have id= somewhere in the link)")
        print(convert_link2(link1))
    else:
        print("Link: " , Path(html_root) / url_quote(relative_path.as_posix()))
    
    return output

def main(title, podcast_root, podcast_folder, audio_root, audio_files_path, html_root, image, csv_file_destination=None):
    if not csv_file_destination:
        csv_file_destination = Path(podcast_folder) / "TOC.csv"

    create_toc(title, podcast_root=podcast_root, podcast_xml_location=podcast_folder, audio_root=audio_root, audio_files_path=audio_files_path, image=image, html_root=html_root)
    xml_path = create_podcast(title, podcast_root=podcast_root, podcast_folder=podcast_folder, toc_path=csv_file_destination,
                   html_root=html_root, google_drive=False, reverse_order=True, name="podcast.xml")
    return xml_path

def is_audio_file(filename):
    for ext in [".ogg", ".m4a", ".mp3", ".m4b"]:
        if str(filename)[-len(ext):] == ext:
            return True
    return False

def is_image(filename):
    for ext in [".png", ".jpg", ".gif", ".bmp"]:
        if str(filename)[-len(ext):] == ext:
            return True
    return False

def find_image(path):
    for f in Path(path).rglob("*"):
        if is_image(f):
            return f
    return False

def path_has_audio_file(path):
    for p in path.glob("*"):
        if is_audio_file(p):
            return True
    return False

def do_entire_folder(audio_root,
                     destination_root,
                     html_root,
                     destination_root_lan=None,
                     html_root_lan=None,
                     rel_url="/podcasts"):
    """

    Args:
        audio_root: e.g. /media/data/MP3_FILES
        destination_root: where to put the podcast files, e.g. /home/pi/public_html/podcasts
        html_root: web address, 192.168.187.103:58372/podcasts
        rel_url: /podcasts

    Returns:

    """
    def already_done(finished_dirs, dir):
        for f in finished_dirs:
            if f in dir.parents:
                logger.warning(f"Skipping {dir}, already did {f}")
                return True
        return False

    def create_podcast(dir):
        category = dir.parent.relative_to(audio_root) if dir.parent in categories else ""
        title = clean(dir.name.replace("  ", " "))
        podcast_folder = Path(destination_root) / category / title
        podcast_folder.mkdir(exist_ok=True, parents=True)
        return podcast_folder, title

    audio_root = Path(audio_root)
    finished_dirs = []

    categories = []
    for dir in audio_root.rglob('*/**/'):
        # Process the highest level directory first
        if already_done(finished_dirs, dir):
            continue

        # If it has no audio files and just one subdirectory, skip it
            # This is usually a book with one too many root directories -- use the lowest possible folder as the root
        # if len(list(dir.glob('*/'))) <= 1 and not path_has_audio_file(dir):  # fewer than one subdirectory, then skip:
        #     logger.warning(f"Skipping {dir}, 1 subfolder and no audio files"); continue

        # If it has folders like "DISC", these should be grouped together
        if len(list(dir.glob('*/'))) > 1 and "disc" in str(next(dir.glob('*/'))).lower():
            podcast_folder, title = create_podcast(dir)

        # If it has audio files, it is a title
        elif path_has_audio_file(dir):
            if audio_root == destination_root:
                podcast_folder = dir
            else:
                podcast_folder, title = create_podcast(dir)
        else: # doesn't have audio files, but does have folders -- it's a category!

            categories.append(dir)
            continue

        # What if it is a category and has audio files (each is a complete book) and subfolders
        # Not allowed -- all files must be in a folder

        csv_file_destination = Path(podcast_folder) / "TOC.csv"

        # Whole process
        xml_path = main(title, podcast_root=destination_root, podcast_folder=podcast_folder, 
                           audio_root=audio_root, audio_files_path=dir, html_root=html_root, 
                           image=None, csv_file_destination=csv_file_destination)

        # Save podcast.xml with new URL
        lan_mirror = destination_root_lan / xml_path.parent.relative_to(destination_root)
        copy_and_change(xml_path, dest=lan_mirror /  "podcastl.xml", old_url=html_root, new_url=html_root_lan)
        print(xml_path)
        finished_dirs.append(dir)

    # Normal HTML index of podcasts
    update_index(destination_root, destination_root, rel_url)

    # Make a local network version
    if html_root_lan is not None:
        if destination_root_lan is None:
            destination_root_lan = destination_root + "l"
        Path(destination_root_lan).mkdir(exist_ok=True, parents=True)
        update_index(destination_root_lan, destination_root_lan, "/podcastsl", name="podcastl.xml")

    # WHAT DOES THIS DO?
    #update_index(audio_root, audio_root, rel_url)

def copy_and_change(xml_file, dest, old_url, new_url):
    """ Open a XML file, find and replace a URL, save to dest

    Args:
        xml_file:
        dest:
        old_url:
        new_url:

    Returns:

    """
    print(xml_file,dest, old_url)
    xml_file, dest = Path(xml_file), Path(dest)
    dest.parent.mkdir(exist_ok=True, parents=True)
    shutil.copy(xml_file, dest)
    with dest.open("rb") as f:
        x = f.read()
    x = x.replace(old_url.encode(), new_url.encode())
    with dest.open("wb") as f:
        f.write(x)

def update_index(scan_folder, index_dst_folder, html_path, name="podcast.xml"):
    """ Loop through directory, create index.html's of folders

    Args:
        scan_folder:
        index_dst_folder:
        html_path:
        name:

    Returns:

    """
    _update_index(Path(scan_folder), Path(index_dst_folder), Path(html_path), name=name)

    for folder in Path(scan_folder).rglob("*"):
        if folder.is_dir():
            rel = folder.relative_to(scan_folder)
            _update_index(folder, index_dst_folder / rel, Path(html_path) / rel, name=name)

def _update_index(scan_folder, index_dst_folder, html_path, name="podcast.xml"):
    """ Create index.html files for Podcast files

        This puts all Podcasts on one index, recursively

        scan_folder - local folder to scan for xml files AND put index file
                    "/home/pi/public_html/podcasts"
        index_dst_folder - where to put the new index
                    "/home/pi/public_html/podcasts_backup_index/"
        html_path - this will precede whatever is found in the scan folder
                    "/podcasts"
        name - podcast.xml files to match
    """
    folders = Path(scan_folder).glob("*")
    index_dst_folder.mkdir(exist_ok=True, parents=True)
    html_file = Path(index_dst_folder) / "index.html"

    with html_file.open("w") as f:
        f.write("<pre>")
        ## Make this write HTML links
        for subfolder in folders:
            # Write out podcast link
            for p in subfolder.glob(name):
                if p.name == name:
                    rel_path = p.relative_to(scan_folder)
                    text = p.parent.name
                    url = html_path / url_quote(rel_path.as_posix().encode())
                    line = hyperlink.format(url, text) + "\n"
                    f.write(line + "\n")
            if (subfolder.is_dir() and has_children_folders(subfolder)):
                rel_path = subfolder.relative_to(scan_folder)
                text = subfolder.name
                url = html_path / url_quote(rel_path.as_posix().encode())
                line = hyperlink.format(url, text) + "\n"
                f.write(line + "\n")

        f.write("</pre>")


def update_index_old(scan_folder, index_dst_folder, html_path, name="podcast.xml"):
    """ Create index.html files for Podcast files for each folder
        This recursively scans the directory and puts them all on one page
        scan_folder - local folder to scan for xml files AND put index file
                    "/home/pi/public_html/podcasts"
        index_dst_folder - where to put the new index
                    "/home/pi/public_html/podcasts_backup_index/"
        html_path - this will precede whatever is found in the scan folder
                    "/podcasts"
        name - podcast.xml files to match
    """
    podcasts = Path(scan_folder).rglob(name)
    html_file = Path(index_dst_folder) / "index.html"

    with html_file.open("w") as f:
        f.write("<pre>")
        ## Make this write HTML links
        for p in scan_folder:
            rel_path = p.relative_to(scan_folder)
            text = p.parent.name
            url = html_path + "/" + url_quote(rel_path.as_posix().encode())
            line = hyperlink.format(url, text) + "\n"
            f.write(line + "\n")
        f.write("</pre>")

def has_children_folders(dir, minimum=0):
    return len([x for x in dir.glob('*/') if x.is_dir()]) > minimum

def do_one():
    title = "CS472_Lectures"  # Should mirror the foldername!!! Also the image!
    image = title + ".png"
    podcast_root = Path(r"/media/BYUCS/public_html")
    podcast_folder = podcast_root / title
    audio_root = podcast_root
    csv_file = Path(podcast_folder / "TOC.csv")
    html_root = "http://fife.entrydns.org/podcasts"
    main(title=title, podcast_root=podcast_root, podcast_folder=podcast_folder, audio_root=audio_root, html_root=html_root, image=image, csv_file_destination=csv_file)

def delete_folder(folder):
    try:
        shutil.rmtree(folder)
    except:
        pass

def run():
    # PODCASTS => PODCAST DIRECTORY
    # PODCASTS/DATA => DATA DIRECTORY

    # audio_root, destination_root, html_root
    # THESE SHOULD MATCH THE REDIRECTS
    # /podcasts/data -> LOCAL_DATA_PATH (where the audio files are)
    # /podcasts ->      LOCAL_PODCAST_ROOT (where to store the podcast xml files etc.)
    # URL_PATH = r"taylorarchibald.com/podcasts" <- this should map to c; also map taylorarchibald.com/podcasts/data to r"taylorarchibald.com/podcasts/data"

    LOCAL_DATA_PATH = rf"/home/{USER}/public_html_data/podcasts"
    LOCAL_PODCAST_ROOT = rf"/home/{USER}/public_html/podcasts"
    URL_PATH = r"taylorarchibald.com/"
    URL_ROOT = f"http://127.0.0.1:{PORT}/podcasts" # for testing
    #URL_ROOT = f"http://www.fife.entrydns.org/podcasts"
    #URL_ROOT = f"http://www.taylorarchibald.com/"
    #URL_ROOT = "/podcasts"
    REL_URL = "/podcasts"
    do_entire_folder(LOCAL_DATA_PATH, LOCAL_PODCAST_ROOT, URL_ROOT, rel_url=REL_URL)

if __name__=="__main__":
    """ image should be the same name as the podcast title + image extension
    """
    with open("config.yaml") as f:
        c = edict(yaml.load(f.read(), Loader=yaml.SafeLoader))

    delete_folder(c.LAN_PODCAST_LOCAL_PATH)
    delete_folder(c.WAN_PODCAST_LOCAL_PATH)
    do_entire_folder(audio_root=c.LOCAL_DATA_PATH,
                     destination_root=c.WAN_PODCAST_LOCAL_PATH,
                     html_root=f"{c.WAN_URL_ROOT}:{c.PORT}",
                     destination_root_lan=c.LAN_PODCAST_LOCAL_PATH,
                     html_root_lan=f"{c.LAN_URL_ROOT}:{c.PORT}",
                     )

"""
audio_root,
                     destination_root,
                     html_root,
                     destination_root_lan=None,
                     html_root_lan=None,
                     rel_url="/podcast")"""