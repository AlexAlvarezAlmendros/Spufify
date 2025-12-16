import os
import threading
import subprocess
import logging
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, APIC, TYER
import requests
from io import BytesIO
from spufify.config import Config
from mutagen.flac import FLAC, Picture
import time

logger = logging.getLogger(__name__)

class Processor:
    """
    Module C: Audio Processor
    Handles encoding (WAV -> MP3/FLAC) and Tagging.
    Output is saved to the configured output directory.
    """
    def __init__(self):
        self.queue = []
        self.max_retries = 3
        # In a real app we might use a dedicated worker thread checking the queue
    
    def _download_cover_with_retry(self, url):
        """Download cover art with retry logic"""
        for attempt in range(self.max_retries):
            try:
                resp = requests.get(url, timeout=10)
                if resp.status_code == 200:
                    return resp.content
                else:
                    logger.warning(f"Cover download returned status {resp.status_code} (attempt {attempt + 1})")
            except requests.exceptions.RequestException as e:
                logger.warning(f"Cover download error (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(1 * (attempt + 1))
        logger.error(f"Failed to download cover after {self.max_retries} attempts")
        return None
        
    def process_track(self, wav_path, metadata, source_sample_rate=None):
        """
        Starts processing in a background thread to avoid blocking UI/Recorder.
        
        Args:
            wav_path: Path to the source WAV file
            metadata: Track metadata dict
            source_sample_rate: Actual sample rate used during recording (auto-detected)
        """
        if source_sample_rate is None:
            source_sample_rate = Config.SAMPLE_RATE
        t = threading.Thread(target=self._process_task, args=(wav_path, metadata, source_sample_rate))
        t.start()
        
    def _process_task(self, wav_path, metadata, source_sample_rate):
        try:
            logger.info(f"Processing: {metadata['title']} - {metadata['artist']}")
            
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
            
            # Build ffmpeg command with high-quality settings using detected sample rate
            cmd = ['ffmpeg', '-y', '-i', wav_path]
            
            logger.debug(f"Source sample rate: {source_sample_rate} Hz")
            
            if ext == 'mp3':
                # Use CBR 320kbps with high-quality encoding
                cmd.extend([
                    '-codec:a', 'libmp3lame',
                    '-b:a', '320k',
                    '-q:a', '0',  # Highest quality (0-9, lower is better)
                    '-ar', str(source_sample_rate),  # Preserve source sample rate
                    output_path
                ])
            elif ext == 'flac':
                # Use compression level 8 (best compression, lossless)
                cmd.extend([
                    '-compression_level', '8',
                    '-ar', str(source_sample_rate),  # Preserve source sample rate
                    output_path
                ])
            else: # wav
                # PCM 16-bit (standard CD quality)
                cmd.extend([
                    '-codec:a', 'pcm_s16le',
                    '-ar', str(source_sample_rate),  # Preserve source sample rate
                    output_path
                ])

            
            # Run FFmpeg with better error handling
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"FFmpeg conversion failed: {result.stderr}")
                return
            
            logger.info(f"Conversion complete: {filename}")
            
            # 3. Tagging
            if ext == 'mp3':
                self._apply_tags_mp3(output_path, metadata)
            elif ext == 'flac':
                self._apply_tags_flac(output_path, metadata)
                
            logger.info(f"Successfully saved: {filename}")
            
            # 4. Clean up WAV
            try:
                os.remove(wav_path)
                logger.debug(f"Cleaned up temporary WAV: {wav_path}")
            except Exception as e:
                logger.warning(f"Failed to delete temporary WAV: {e}")
            
        except Exception as e:
            logger.error(f"Error processing {wav_path}: {e}", exc_info=True)

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
                cover_data = self._download_cover_with_retry(metadata['cover_url'])
                if cover_data:
                    try:
                        audio.tags.add(
                            APIC(
                                encoding=3, # 3 is for utf-8
                                mime='image/jpeg', # or image/png
                                type=3, # 3 is for the cover image
                                desc=u'Cover',
                                data=cover_data
                            )
                        )
                    except Exception as e:
                        logger.error(f"Error adding cover to MP3: {e}")

            audio.save()
            logger.debug(f"MP3 tags applied successfully")
            
        except Exception as e:
            logger.error(f"Error tagging MP3: {e}", exc_info=True)

    def _apply_tags_flac(self, file_path, metadata):
        try:
            audio = FLAC(file_path)
            
            # Basic Tags (Vorbis Comments)
            audio['title'] = metadata['title']
            audio['artist'] = metadata['artist']
            audio['album'] = metadata['album']
            
            # Cover Art
            if metadata.get('cover_url'):
                cover_data = self._download_cover_with_retry(metadata['cover_url'])
                if cover_data:
                    try:
                        image = Picture()
                        image.type = 3
                        image.mime = "image/jpeg"
                        image.desc = "Cover"
                        image.data = cover_data
                        audio.add_picture(image)
                    except Exception as e:
                        logger.error(f"Error adding cover to FLAC: {e}")

            audio.save()
            logger.debug(f"FLAC tags applied successfully")
            
        except Exception as e:
            logger.error(f"Error tagging FLAC: {e}", exc_info=True)

    def _sanitize(self, text):
        return "".join(x for x in text if x.isalnum() or x in " -_")
