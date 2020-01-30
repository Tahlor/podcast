
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
from server import PORT, USER

# taylorarchibald.com/podcasts => "/media/taylor/Flash128/Podcasts"
# taylorarchibald.com/podcasts/data/this_podcast => "/media/taylor/Flash128/Downloads/this_podcasts"

# PREFIX = "/media/taylor/Flash128/"
# HOME_FOLDER = "" # the public datastructure; URL mirrors directory
# DATA = PREFIX + "Downloads" # different prefix

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
    html_audio_sub = f"{html_root}/data/{url_quote(audio_files_path.relative_to(audio_root).as_posix())}"
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
            link = f'{d["Link"]}/{clean_quote(f.name)}'
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
                   category="Literature", description="N/A", alphabetize=True, image_link=None, google_drive=True, reverse_order=True):
    # With reverse order, we make "Chapter 1" be the most recent entry
    # Open CSV
    if not podcast_folder:
        podcast_folder = Path(podcast_root) / title
    if not toc_path:
        toc_path = Path(podcast_folder) / "TOC.csv"

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
    fg.rss_file(os.path.join(podcast_folder, 'podcast.xml'))

    if google_drive:
        link1 = input("Upload your podcast XML to Google drive. What is the download link for the podcast.xml? (it should have id= somewhere in the link)")
        print(convert_link2(link1))
    else:
        relative_path = Path(podcast_folder).relative_to(podcast_root) / "podcast.xml"
        print("Link: " , Path(html_root) / url_quote(relative_path.as_posix()))

def main(title, podcast_root, podcast_folder, audio_root, audio_files_path, html_root, image, csv_file_destination=None):
    if not csv_file_destination:
        csv_file_destination = Path(podcast_folder) / "TOC.csv"

    create_toc(title, podcast_root=podcast_root, podcast_xml_location=podcast_folder, audio_root=audio_root, audio_files_path=audio_files_path, image=image, html_root=html_root)
    create_podcast(title, podcast_root=podcast_root, podcast_folder=podcast_folder, toc_path=csv_file_destination,
                   html_root=html_root, google_drive=False, reverse_order=True)

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

def do_entire_folder(audio_root, destination_root, html_root):
    def already_done(finished_dirs, dir):
        for f in finished_dirs:
            if f in dir.parents:
                logger.warning(f"Skipping {dir}, already did {f}")
                return True
        return False

    audio_root = Path(audio_root)
    finished_dirs = []
    for dir in audio_root.rglob('*/**/'):
        if already_done(finished_dirs, dir):
            continue
        # If it has no audio files and just one subdirectory, skip it
        if len(list(dir.glob('*/'))) <= 1 and not path_has_audio_file(dir):  # fewer than one subdirectory, then skip:
            logger.warning(f"Skipping {dir}, 1 subfolder and no audio files"); continue
        if audio_root == destination_root:
            podcast_folder = dir
        else:
            title = clean(dir.name.replace("  ", " "))
            podcast_folder = Path(destination_root) / title
            podcast_folder.mkdir(exist_ok=True, parents=True)

        main(title, podcast_root=destination_root, podcast_folder=podcast_folder, audio_root=audio_root, audio_files_path=dir, html_root=html_root, image=None)
        finished_dirs.append(dir)
    update_index(destination_root, html_root)

def update_index(podcast_folder, html_root):
    podcasts = Path(podcast_folder).rglob("podcast.xml")
    html_file = Path(podcast_folder) / "index.html"

    with html_file.open("w") as f:
        f.write("<pre>")
        ## Make this write HTML links
        for p in podcasts:
            rel_path = p.relative_to(podcast_folder)
            text = p.parent.name
            url = html_root + "/" + url_quote(rel_path.as_posix().encode())
            line = hyperlink.format(url, text) + "\n"
            f.write(line + "\n")
        f.write("</pre>")

def do_one():
    title = "CS472_Lectures"  # Should mirror the foldername!!! Also the image!
    image = title + ".png"
    podcast_root = Path(r"/media/BYUCS/public_html")
    podcast_folder = podcast_root / title
    audio_root = podcast_root
    csv_file = Path(podcast_folder / "TOC.csv")
    html_root = "http://fife.entrydns.org/podcasts"
    main(title=title, podcast_root=podcast_root, podcast_folder=podcast_folder, audio_root=audio_root, html_root=html_root, image=image, csv_file_destination=csv_file)

if __name__=="__main__":
    """ image should be the same name as the podcast title + image extension
    """
    # PODCASTS => PODCAST DIRECTORY
    # PODCASTS/DATA => DATA DIRECTORY

    # audio_root, destination_root, html_root
    # THESE SHOULD MATCH THE REDIRECTS
    # /podcasts/data -> LOCAL_DATA_PATH (where the audio files are)
    # /podcasts ->      LOCAL_PODCAST_ROOT (where to store the podcast xml files etc.)
    # URL_PATH = r"taylorarchibald.com/podcasts" <- this should map to c; also map taylorarchibald.com/podcasts/data to r"taylorarchibald.com/podcasts/data"

    LOCAL_DATA_PATH = rf"/home/{USER}/public_html_data/podcasts"
    LOCAL_PODCAST_ROOT = rf"/home/{USER}/public_html/podcasts"
    URL_PATH = r"taylorarchibald.com/podcasts"
    URL_ROOT = f"http://127.0.0.1:{PORT}/podcasts" # for testing
    URL_ROOT = f"http://www.fife.entrydns.com/podcasts"
    URL_ROOT = f"http://www.taylorarchibald.com/podcasts"


    do_entire_folder(LOCAL_DATA_PATH, LOCAL_PODCAST_ROOT, URL_ROOT)