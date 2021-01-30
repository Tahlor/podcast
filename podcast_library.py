
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
import socket

CONFIG = "config_test2.yaml" if "raspberry" not in socket.gethostname() else "config.yaml"
print("Using {}".format(CONFIG))

#### USAGE
"""
* ALL PODCASTS NEED TO HAVE THEIR OWN FOLDER!!

# Web Permissions: chgrp -R pi * && chown -R pi * && chmod -R 777 *
"""


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
    html_rel_podcast_xml = clean_quote(podcast_xml_location.relative_to(podcast_root).as_posix())
    html_sub = f"{html_root}/{html_rel_podcast_xml}"
    html_rel_audio = url_quote(audio_files_path.relative_to(audio_root).as_posix())
    html_audio_sub = f"{html_root}/podcasts/data/{html_rel_audio}"
    title_url = clean_quote(title)

    if not image:
        image = find_image(audio_files_path)
        # Look in audio folder
        if image:
            image = "podcasts/data/" + html_rel_audio + "/" + image.relative_to(audio_files_path).as_posix()
        else: # look in podcast.xml folder
            image = find_image(podcast_xml_location);
            if image:
                image = html_rel_podcast_xml + "/" + image.relative_to(podcast_xml_location).as_posix()
            else:
                image =  html_rel_podcast_xml + "/" + title_url + ".png"

    d = {"Series": title, "Title": title, "Link": f"{html_audio_sub}", "Image": f"{html_root}/{clean_quote(image)}"}
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
            #title = f"{d['Title']} {f.stem}"
            title =  f"{d['Title']} {' - '.join(f_relative_path.split('/'))}"
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
        if Path(filename).suffix == ext:
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

def path_has_no_subs(path):
    for p in path.glob("*"):
        try:
            if p.is_dir():
                if path_has_audio_file(p): # see if subfolders have audio files
                    return False
        except Exception as e:
            print(e)
            print("Problem parsing {p}, check filesystem using sudo fsck -cfk /dev/sdaX")
    return True

def do_entire_folder(audio_root,
                     destination_root,
                     html_root,
                     destination_root_lan=None,
                     html_root_lan=None,
                     rel_url="/podcasts",
                     testing=False):
    """

    Args:
        audio_root: e.g. /media/data/MP3_FILES
        destination_root: where to put the podcast files, e.g. /home/pi/public_html/podcasts
        html_root: web address, 192.168.187.103:58372/podcasts
        rel_url: /podcasts

    Returns:

    """
    def already_done(finished_dirs, dir, verbose=True):
        for f in finished_dirs:
            if f in dir.parents:
                if verbose:
                    logger.warning(f"Skipping {dir}, already did {f}")
                return True
        return False
   
    def already_done2(finished_dirs, dir, verbose=True):
        return dir.parent in finished_dirs
     
    def create_podcast(dir):
        category = dir.parent.relative_to(audio_root) if dir.parent in categories else ""
        title = clean(dir.name.replace("  ", " "))
        podcast_folder = Path(destination_root) / category / title
        podcast_folder.mkdir(exist_ok=True, parents=True)
        return podcast_folder, title

    audio_root = Path(audio_root)
    finished_dirs = {}
    standalone = []
    categories = []
    for dir in audio_root.rglob('*'):
        #for dir in audio_root.rglob('*/**/'): # for scanning folders only
    
        # We Process the highest level directory first
        if already_done2(finished_dirs, dir, verbose=False):
            continue

        # If it has no audio files and just one subdirectory, skip it
            # This is usually a book with one too many root directories -- use the lowest possible folder as the root

        if dir.is_dir():
            # If it has folders like "DISC", these should be grouped together
            subfolders=list(dir.glob('*/'))
            if len(subfolders) > 1 and re.search("disc[0-9 ]+",str(next(dir.glob('*/'))).lower()):
                print(str(next(dir.glob('*/'))).lower())
                podcast_folder, title = create_podcast(dir)
                    
            # If it has audio files, it is a title
            elif path_has_audio_file(dir) and path_has_no_subs(dir):
                if audio_root == destination_root:
                    podcast_folder = dir
                else:
                    podcast_folder, title = create_podcast(dir)
            else: # doesn't have audio files, but does have folders -- it's a category!

                categories.append(dir)
                continue
        elif is_audio_file(dir.name) or dir.suffix.lower() in [".epub",".mobi",".pdf"]:
            #standalone.append(dir)
            #dir.name
            #podcast_folder, title = create_podcast(dir)
            #print(dir, destination_root, audio_root)
            #input()
            dst = destination_root / dir.relative_to(audio_root)
            dst.parent.mkdir(exist_ok=True,parents=True)
            os.symlink(dir, dst)
            continue
        else:
            continue

        for sub in subfolders:
            finished_dirs[sub]=0
        finished_dirs[dir] = 0
            
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
        
        if testing:
            print("TESTING")
            break
        
    # Normal HTML index of podcasts
    update_index(destination_root, destination_root, rel_url, find_other_files=True)

    # Make a local network version
    if html_root_lan is not None:
        if destination_root_lan is None:
            destination_root_lan = destination_root + "l"
        Path(destination_root_lan).mkdir(exist_ok=True, parents=True)
        update_index(destination_root_lan, destination_root_lan, "/podcastsl", name="podcastl.xml")
        # ADD OPTION FOR STANDALONES
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

def update_index(scan_folder, index_dst_folder, html_path, name="podcast.xml", find_other_files=True):
    """ Loop through directory, create index.html's of folders

    Args:
        scan_folder:
        index_dst_folder:
        html_path:
        name:

    Returns:

    """
    _update_index(Path(scan_folder), Path(index_dst_folder), Path(html_path), name=name, find_other_files=find_other_files)

    for folder in sorted(Path(scan_folder).rglob("*")):
        if folder.is_dir():
            rel = folder.relative_to(scan_folder)
            _update_index(folder, index_dst_folder / rel, Path(html_path) / rel, name=name, find_other_files=find_other_files)

def _update_index(scan_folder, index_dst_folder, html_path, name="podcast.xml", find_other_files=True):
    """ Create index.html files for Podcast files - recursive call from update_index
            This the main podcast index (not the file/all ones)
        This puts all Podcasts on one index, recursively -- it looks for the podcast.xml files in the web directory

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
        f.write("<pre>\n")
        f.write(f'<a href="{html_path}/files.html">ALL</a>\n\n')

        temp_html_path = re.sub(r"(podcasts[l]*/)",r"\1data/",str(html_path))
        f.write(f'<a href="{temp_html_path}">FILE_VIEW</a>\n\n')

        ## Make this write HTML links
        for subfolder in sorted(folders):
            # Write out podcast link
            for p in subfolder.glob(name):
                #input(find_other_files)
                if p.name == name:
                    rel_path = p.relative_to(scan_folder)
                    text = p.parent.name
                    url = html_path / url_quote(rel_path.as_posix().encode())
                    line = hyperlink.format(url, text) + "\n"
                    f.write(line + "\n")

            if ((subfolder.is_dir() and has_children_folders(subfolder)) or
                    (has_book(subfolder) and find_other_files)):
                rel_path = subfolder.relative_to(scan_folder)
                text = subfolder.name
                url = html_path / url_quote(rel_path.as_posix().encode())
                line = hyperlink.format(url, text) + "\n"
                f.write(line + "\n")

        if find_other_files:
            for p in Path(scan_folder).glob('*'):
                if is_audio_file(p.name) or p.suffix.lower() in [".epub",".mobi",".pdf"]:
                    rel_path = p.relative_to(scan_folder)
                    text = p.name
                    #input(text)
                    url = html_path / url_quote(rel_path.as_posix().encode())
                    line = hyperlink.format(url, text) + "\n"
                    f.write(line + "\n")

        f.write("</pre>")

def update_index_old(scan_folder, index_dst_path, html_path, name="podcast.xml", use_parent_name=True):
    """ Create ONE index.html files for Podcast files for each folder
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
    if Path(index_dst_path).suffix != ".html":
        Path(index_dst_path).mkdir(exist_ok=True, parents=True)
        html_file_path = Path(index_dst_path) / "index.html"
    else:
        html_file_path = index_dst_path
    lines = []

    ## Make this write HTML links
    for p in podcasts:
        rel_path = p.relative_to(scan_folder)
        if use_parent_name:
           text = p.parent.name
        else:
           text = "{}/{}".format(p.parent.name,p.name)

        url = html_path + "/" + url_quote(rel_path.as_posix().encode())
        #print(url)
        line = hyperlink.format(url, text) + "\n"
        lines.append(line)
    lines.sort()

    print("WRITING TO ", html_file_path)
    with html_file_path.open("w") as f:
        f.write("<pre>")
        for line in lines:
            f.write(line + "\n")
        f.write("</pre>")

def update_index_old2(scan_folder, index_dst_path, html_path, name="podcast.xml", use_parent_name=True, master_dict={}, root_scan_folder=None):
    """ Create recursive index.html files for Podcast files for each folder
        Recursively recursive: each folder contains a file with links to ALL subdirectories, sub-sub-dirs, etc.
    
        This recursively scans the directory and puts them all on one page
        scan_folder - local folder to scan for xml files AND put index file
                    "/home/pi/public_html/podcasts"
        index_dst_folder - where to put the new index
                    "/home/pi/public_html/podcasts_backup_index/"
        html_path - this will precede whatever is found in the scan folder
                    "/podcasts"
        name - podcast.xml files to match
        use_parent_name (bool) - for the URL link text, include the parent folder
        root_scan_folder - the "top" level scan folder; this is needed to compute the relative path for the HTML links
    """
    if root_scan_folder is None:
        root_scan_folder = scan_folder
    index_dst_path = Path(index_dst_path)
    if index_dst_path.suffix != ".html":
        index_dst_path.mkdir(exist_ok=True, parents=True)
        html_file_path = index_dst_path / "index.html"
    else:
        html_file_path = index_dst_path
        index_dst_path.parent.mkdir(exist_ok=True, parents=True)
    lines = []

    ## Make this write HTML links

    #master_dict[scan_folder] = master_dict = {}
    # Get all podcasts (files that match "name") in current folder
    #master_dict["~:podcasts:~"] = curr_folder_file_list = []
    curr_folder_file_list = []
    for podcast_xml in Path(scan_folder).glob(name):
        curr_folder_file_list.append(podcast_xml)
        rel_path = podcast_xml.relative_to(root_scan_folder)
        #print(rel_path, scan_folder, podcast_xml)
        #input()
        
        if use_parent_name:
           text = podcast_xml.parent.name
        else:
           text = "{}/{}".format(podcast_xml.parent.name,podcast_xml.name)
        
        if podcast_xml.is_file():
            url = html_path + "/" + url_quote(rel_path.as_posix().encode())
        else:
            url = str(Path(html_path).parent) + "/" + url_quote(rel_path.as_posix().encode()) + "/files.html"
            #print(url, text, rel_path)
            #input("HERE")

        #print(url)
        line = hyperlink.format(url, text) + "\n"
        lines.append(line)

        
    lines.sort()

    for p in Path(scan_folder).glob("*"): # recursive part, check all subfolders
        if p.is_dir(): # everything should be a directory
            new_index_dst_path = index_dst_path.parent / p.name / index_dst_path.name
            print(index_dst_path, new_index_dst_path)
            l = update_index_old2(p, new_index_dst_path, html_path, name=name, use_parent_name=False, master_dict=master_dict, root_scan_folder=root_scan_folder)
            #print(l)
            lines.extend(l)
            #STOP
    print("WRITING TO ", html_file_path)
    with html_file_path.open("w") as f:
        f.write("<pre>")
        for line in lines:
            f.write(line + "\n")
        f.write("</pre>")
    return lines

def has_children_folders(dir, minimum=0):
    return len([x for x in dir.glob('*/') if x.is_dir()]) > minimum

def has_book(dir):
    for ftype in ["*.pdf", "*.mobi", "*.epub", "*.mp3", "*.m4a", "*.m4b", "*.ogg"]:
        for i in Path(dir).rglob(ftype):
            return True
    return False

ALL_FILES = {".pdf":"", ".mobi":"", ".epub":"", ".mp3":"", ".m4a":"", ".m4b":"", ".ogg":""}

def has_book(dir):
    for i in Path(dir).rglob("*"):
        if i.suffix in ALL_FILES.keys():
            return True
    return False

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
    with open(CONFIG) as f:
        c = edict(yaml.load(f.read(), Loader=yaml.SafeLoader))

    if True:
        delete_folder(c.LAN_PODCAST_LOCAL_PATH)
        delete_folder(c.WAN_PODCAST_LOCAL_PATH)
        do_entire_folder(audio_root=c.LOCAL_DATA_PATH,
                     destination_root=c.WAN_PODCAST_LOCAL_PATH,
                     html_root=f"{c.WAN_URL_ROOT}",
                     destination_root_lan=c.LAN_PODCAST_LOCAL_PATH,
                     html_root_lan=f"{c.LAN_URL_ROOT}:{c.PORT}",
                     )

    # Make master file index for easy copying
    # These will be accessed in either the WAN/LAN_PODCAST_LOCAL_PATH (podcasts/podcastsl), so we need to go up a path ".."
    update_index_old2(c.LOCAL_DATA_PATH, Path(c.WAN_PODCAST_LOCAL_PATH)/"files.html", html_path='/podcasts/data', name="*", use_parent_name=False)
    update_index_old2(c.LOCAL_DATA_PATH, Path(c.LAN_PODCAST_LOCAL_PATH)/"files.html", html_path='/podcasts/data', name = "*", use_parent_name=False)
    
    
    # THESE ARE ACCESSIBLE AT fife.entrydns.org/podcasts/files.html


"""
audio_root,
                     destination_root,
                     html_root,
                     destination_root_lan=None,
                     html_root_lan=None,
                     rel_url="/podcast")"""
