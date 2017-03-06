import os
import math
import json
import subprocess
from glob import glob
from time import time


class FFmpegException(Exception):
    pass


class Transcoder(object):

    BASE_FFMPEG_OPTIONS = [
        "-v", "error",
        "-stats",
    ]
    CHUNK_LIST_FILENAME = "chunks.txt"
    CHUNK_FILENAME_BASE = "chunk"
    CHUNK_FILENAME_SEGMENT_FORMAT = "%d"
    CHUNK_FILENAME_GLOB_FORMAT = "*"

    def __init__(self, input_file, width=None, height=None, is_chunk=False):
        if not os.path.isfile(input_file):
            raise FileNotFoundError(input_file)

        self.__input = input_file
        self.__dir = os.path.dirname(input_file)
        self.__name, self.__ext = os.path.splitext(input_file)

        # .../chunks.txt
        self.__chunk_list_filepath = os.path.join(
            self.__dir, self.CHUNK_LIST_FILENAME
        )
        # .../chunk
        self.__chunk_base_path = os.path.join(
            self.__dir, self.CHUNK_FILENAME_BASE
        )
        # .../chunk%d.ext
        self.__chunk_filepath = ''.join((
            self.__chunk_base_path,
            self.CHUNK_FILENAME_SEGMENT_FORMAT,
            self.__ext
        ))
        # .../chunk*.ext
        self.__chunk_globpath = ''.join((
            self.__chunk_base_path,
            self.CHUNK_FILENAME_GLOB_FORMAT,
            self.__ext
        ))

        if is_chunk:
            assert width and height
            self.__width = width
            self.__height = height
        else:
            self.__info = self.__get_file_info_json()
            self.__width = self.__info["streams"][0]["width"]
            self.__height = self.__info["streams"][0]["height"]
            self.__duration = float(self.__info["format"]["duration"])

    def __get_file_info_json(self):
        options = [
            '-v', 'error',
            '-print_format', 'json',
            '-show_format',
            '-show_streams'
        ]
        return json.loads(subprocess.check_output(
            ['ffprobe'] + options + [self.__input]
        ).decode())

    @property
    def dimensions(self):
        return self.__width, self.__height

    @property
    def chunk_files(self):
        if os.path.isfile(self.__chunk_list_filepath):
            files = []
            with open(self.__chunk_list_filepath, "r") as chunk_list:
                for line in chunk_list:
                    if line.startswith("file "):
                        files.append(
                            os.path.join(
                                self.__dir,
                                line.lstrip("file ").rstrip()
                            )
                        )
            return files
        print("No chunk list file present.")
        return None

    def transsize(self, height, aspect_ratio, chunk_file=''):
        """
        Change picture size of input file or given chunk file.
        Chunk files will be overwritten.
        """
        if height < self.__height:
            if chunk_file and not os.path.isfile(chunk_file):
                raise FileNotFoundError(chunk_file)
            width = int(height * aspect_ratio)
            input = chunk_file or self.__input
            name = os.path.splitext(chunk_file)[0] or self.__name
            options = self.BASE_FFMPEG_OPTIONS + [
                '-i', input,
                '-vf', 'scale={}:{}'.format(width, height)
            ]
            output = "{name}_{w}_{h}{ext}".format(
                name=name, w=width, h=height, ext=self.__ext
            )
            info = "{} {}x{} -> {}x{}".format(
                os.path.basename(input),
                self.__width, self.__height,
                width, height
            )
            print(info)
            print("-" * len(info))
            subprocess.call(['ffmpeg'] + options + [output])
            print()
            if chunk_file:
                # cannot overwrite file while transcoding so replace now
                os.rename(output, chunk_file)
        else:
            print("Cannot transsize. Height ({}) is greater than input "
                  "file height ({}).".format(height, self.__height))

    def transcode(self):
        """
        Convert encoding of input file to given encoding.
        """
        pass

    def transrate(self):
        """
        Decrease bitrate of input file.
        """
        pass

    def split(self, num_chunks):
        print("Splitting into {} chunks.".format(num_chunks))
        chunk_time = math.ceil(self.__duration / num_chunks)
        try:
            self.__split_with_segment(chunk_time)
        except FFmpegException:
            print("Failed to split using FFmpeg segment option, falling back to manual splitting.")
            self.__split_manually(num_chunks, chunk_time)

    def __split_with_segment(self, chunk_time):
        options = self.BASE_FFMPEG_OPTIONS + [
            '-i', self.__input,
            '-c', 'copy',
            '-f', 'segment',
            '-segment_time', str(chunk_time),
            '-segment_list', self.__chunk_list_filepath,
            '-segment_list_type', 'ffconcat',
            '-reset_timestamps', '1',
            '-map', '0'
        ]
        try:
            subprocess.check_call(['ffmpeg'] + options + [self.__chunk_filepath])
        except subprocess.CalledProcessError as e:
            self.__remove_chunk_files()
            raise FFmpegException(e)

    def __split_manually(self, num_chunks, chunk_time):
        for i in range(num_chunks):
            options = self.BASE_FFMPEG_OPTIONS + [
                '-ss', str(i * chunk_time),
                '-t', str(chunk_time),
                '-i', self.__input,
                '-c', 'copy'
            ]
            output = ''.join((self.__chunk_base_path, str(i), self.__ext))
            subprocess.call(['ffmpeg'] + options + [output])
            # append to chunk list file
            with open(self.__chunk_list_filepath, "a") as chunk_list_file:
                chunk_list_file.write("file {}\n".format(
                    ''.join((self.CHUNK_FILENAME_BASE, str(i), self.__ext))
                ))

    def stitch(self, suffix=None):
        print("Stitching...")
        options = self.BASE_FFMPEG_OPTIONS + [
            '-f', 'concat',
            '-safe', '0',
            '-i', self.__chunk_list_filepath,
            '-c', 'copy'
        ]
        suffix = suffix or time()
        output = "{name}_{suffix}{ext}".format(
            name=self.__name, suffix=suffix, ext=self.__ext
        )
        subprocess.call(['ffmpeg'] + options + [output])
        self.__remove_chunk_files()

    def __remove_chunk_files(self):
        os.remove(self.__chunk_list_filepath)
        for chunk_file in glob(self.__chunk_globpath):
            os.remove(chunk_file)
