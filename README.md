# FFperf(ormance)

## TODO:
- [ ] Find a large video file (with audio) that can be **both** segmented and seek-split.
  - Small file tested already and split-time difference was negligible.
- [x] Compare the time it takes to segment to the time it takes to seek-split (with and without multiprocessing).
- [x] Look into **threading** to increase FFmpeg performance: see [this](http://superuser.com/questions/538164/how-many-instances-of-ffmpeg-commands-can-i-run-in-parallel/547340#547340).
  - By default, ffmpeg uses the optimal thread setting but effectiveness varies depending on the codec used.
- [ ] Test more file types and multiple files of the same type.
   - Table of files/filetypes tested.
- [ ] Find which chunking methods work / work best for different file formats.
   - The **.mov** files tested so far cannot be segmented, but the are from the same source (harmonic).
   - If no segmented **.mov** file can be found, it is safe to assume video files of this type cannot be split in 
   this way and the error check should be bypassed.
- [ ] Find a threshold for chunking; get enough data to graph chunked transcoding vs singleton transcoding
for different file sizes.

## Notes
- [`yuv420p`](http://superuser.com/questions/820134/why-cant-quicktime-play-a-movie-file-encoded-by-ffmpeg) 
is required for video player compatibility.
- Sequential seek-splitting takes longer than segmenting.
- It is probably a bad idea to have each worker seek-split a file for its chunk. 
While the workers would have their respective chunks immediately after splitting,
the entire file will have to be sent to each worker!
- Using a manifest file might come in handy: https://github.com/c0decracker/video-splitter

## Links
#### Guidance
- [FFprobe Tips](https://trac.ffmpeg.org/wiki/FFprobeTips)
- [Concatenating media files](https://trac.ffmpeg.org/wiki/Concatenate#no1)
- [Creating multiple outputs](https://trac.ffmpeg.org/wiki/Creating%20multiple%20outputs)
- [Understanding screen resolution and aspect ratio](http://www.digitalcitizen.life/what-screen-resolution-or-aspect-ratio-what-do-720p-1080i-1080p-mean)
#### Assets
 - [harmonic 4k demo footage](https://www.harmonicinc.com/4k-demo-footage-download/)
 - [demo-world hd trailers](http://www.demo-world.eu/2d-demo-trailers-hd/)

## Glossary
**segmenting**

Using the [stream segmenter](https://www.ffmpeg.org/ffmpeg-all.html#segment_002c-stream_005fsegment_002c-ssegment) 
to chunk a file. This can be performed with one command:

```bash
ffmpeg -i input.ext -c copy -f segment -reset_timestamps 1 -map 0
```

**seek-splitting**

Chunking a file by seeking a start position and setting a read duration. 
This is performed with multiple commands:

```bash
ffmpeg -ss 0 -t 30 -i input.ext -c copy
ffmpeg -ss 30 -t 30 -i input.ext -c copy
ffmpeg -ss 60 -t 30 -i input.ext -c copy
...
```
