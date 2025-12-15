import os
import threading
import subprocess
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, APIC, TYER
import requests
from io import BytesIO
from spufify.config import Config


from mutagen.flac import FLAC, Picture

class Processor:
    """
    Module C: Audio Processor
    Handles encoding (WAV -> MP3/FLAC) and Tagging.
    Output is saved to the configured output directory.
    """
    def __init__(self):
        self.queue = []
        # In a real app we might use a dedicated worker thread checking the queue
        
    def process_track(self, wav_path, metadata):
        """
        Starts processing in a background thread to avoid blocking UI/Recorder.
        """
        t = threading.Thread(target=self._process_task, args=(wav_path, metadata))
        t.start()
        
    def _process_task(self, wav_path, metadata):
        try:
            print(f"[Processor] Processing: {metadata['title']}")
            
            # 1. Conversion logic using FFmpeg directly
            artist = metadata.get('artist', 'Unknown')
            title = metadata.get('title', 'Untitled')
            
            safe_artist = self._sanitize(artist)
            safe_title = self._sanitize(title)
            
            ext = Config.OUTPUT_FORMAT.lower()
            if ext not in ['mp3', 'flac', 'wav']:
                ext = 'flac' # Default to lossless if unknown
                
            filename = f"{safe_artist} - {safe_title}.{ext}"
            output_path = os.path.join(Config.OUTPUT_DIR, filename)
            
            # Build ffmpeg command
            cmd = ['ffmpeg', '-y', '-i', wav_path]
            
            if ext == 'mp3':
                cmd.extend(['-b:a', '320k', output_path])
            elif ext == 'flac':
                cmd.extend(['-compression_level', '5', output_path])
            else: # wav
                # Just copy (pcm_s16le is default for wav)
                cmd.extend([output_path])

            
            # Suppress output unless error
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            
            # 3. Tagging
            if ext == 'mp3':
                self._apply_tags_mp3(output_path, metadata)
            elif ext == 'flac':
                self._apply_tags_flac(output_path, metadata)
                
            print(f"[Processor] Finished: {filename}")
            
            # 4. Clean up WAV
            os.remove(wav_path)
            
        except Exception as e:
            print(f"[Processor] Error processing {wav_path}: {e}")

    def _apply_tags_mp3(self, file_path, metadata):
        try:
            audio = MP3(file_path, ID3=ID3)
            # Add ID3 tag if it doesn't exist
            try:
                audio.add_tags()
            except Exception:
                pass
            
            # Basic Tags
            audio.tags.add(TIT2(encoding=3, text=metadata['title']))
            audio.tags.add(TPE1(encoding=3, text=metadata['artist']))
            audio.tags.add(TALB(encoding=3, text=metadata['album']))
            
            # Cover Art
            if metadata.get('cover_url'):
                try:
                    resp = requests.get(metadata['cover_url'])
                    if resp.status_code == 200:
                        audio.tags.add(
                            APIC(
                                encoding=3, # 3 is for utf-8
                                mime='image/jpeg', # or image/png
                                type=3, # 3 is for the cover image
                                desc=u'Cover',
                                data=resp.content
                            )
                        )
                except Exception as e:
                    print(f"[Processor] Error downloading cover: {e}")

            audio.save()
            
        except Exception as e:
            print(f"[Processor] Error tagging MP3: {e}")

    def _apply_tags_flac(self, file_path, metadata):
        try:
            audio = FLAC(file_path)
            
            # Basic Tags (Vorbis Comments)
            audio['title'] = metadata['title']
            audio['artist'] = metadata['artist']
            audio['album'] = metadata['album']
            
            # Cover Art
            if metadata.get('cover_url'):
                try:
                    resp = requests.get(metadata['cover_url'])
                    if resp.status_code == 200:
                        image = Picture()
                        image.type = 3
                        image.mime = "image/jpeg"
                        image.desc = "Cover"
                        image.data = resp.content
                        audio.add_picture(image)
                except Exception as e:
                    print(f"[Processor] Error downloading cover (FLAC): {e}")

            audio.save()
            
        except Exception as e:
            print(f"[Processor] Error tagging FLAC: {e}")

    def _sanitize(self, text):
        return "".join(x for x in text if x.isalnum() or x in " -_")
