import os
import pyaudio
import time
import tkinter as tk
from tkinter import filedialog
import numpy as np
import threading
import pygame
import datetime

# Initialize Pygame for visualization
pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 512, 512  # GUI window size
WATERFALL_SIZE = 128  # Waterfall visualization size
SIDEBAR_WIDTH = 200  # Sidebar width
BOTTOM_BAR_HEIGHT = 50  # Bottom bar height

screen = pygame.display.set_mode((SCREEN_WIDTH + SIDEBAR_WIDTH, SCREEN_HEIGHT + BOTTOM_BAR_HEIGHT))
pygame.display.set_caption("Binary Waterfall Audio Player")
font = pygame.font.Font(None, 24)

def read_files_as_binary(directory):
    files = []
    for root, _, filenames in os.walk(directory):
        for filename in sorted(filenames):
            filepath = os.path.join(root, filename)
            try:
                with open(filepath, "rb") as f:
                    files.append((filepath, f.read()))
            except (PermissionError, IOError) as e:
                print(f"⚠️ Skipping {filepath}: {e}")
    return files

def get_file_info(filepath):
    try:
        file_type = os.path.splitext(filepath)[1][1:] or "Unknown"
        file_size = os.path.getsize(filepath)
        creation_time = datetime.datetime.fromtimestamp(os.path.getctime(filepath)).strftime('%Y-%m-%d %H:%M:%S')
        return file_type, file_size, creation_time
    except Exception as e:
        return "Unknown", 0, "Unknown"

def play_binary_audio(files, bytes_per_second):
    p = pyaudio.PyAudio()
    try:
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=bytes_per_second, output=True)
    except Exception as e:
        print(f"❌ Failed to open audio stream: {e}")
        return

    for index, (filepath, binary_data) in enumerate(files):
        file_size = len(binary_data)
        duration = file_size / bytes_per_second
        start_time = time.time()
        print(f"\n🎵 Now playing: {filepath}")
        chunk_size = bytes_per_second // 10  # 0.1 sec per chunk

        for i in range(0, file_size, chunk_size):
            try:
                chunk = binary_data[i:i+chunk_size]
                stream.write(chunk)
                elapsed_time = time.time() - start_time
                time_remaining = max(0, duration - elapsed_time)
                update_visualization(chunk, files, index, file_size, bytes_per_second, time_remaining, filepath)
            except Exception as e:
                print(f"⚠️ Playback error: {e}")
                break

        print("\n✅ Finished playing.")

    stream.stop_stream()
    stream.close()
    p.terminate()

def update_visualization(data_chunk, files, current_index, file_size, bytes_per_second, time_remaining, filepath):
    binary_array = np.unpackbits(np.frombuffer(data_chunk, dtype=np.uint8))[:WATERFALL_SIZE**2]
    binary_array = binary_array.reshape((WATERFALL_SIZE, WATERFALL_SIZE)) * 255

    # Convert to a 3-channel (RGB) image
    binary_surface = pygame.surfarray.make_surface(np.tile(binary_array[..., None], (1, 1, 3)))
    binary_surface = pygame.transform.scale(binary_surface, (SCREEN_WIDTH, SCREEN_HEIGHT))
    screen.fill((50, 50, 50))
    screen.blit(binary_surface, (SIDEBAR_WIDTH, 0))
    
    # Sidebar (Previous, Current, Next Files)
    sidebar = pygame.Surface((SIDEBAR_WIDTH, SCREEN_HEIGHT))
    sidebar.fill((30, 30, 30))
    
    for i, (file, _) in enumerate(files[max(0, current_index - 2): current_index + 3]):
        text_color = (255, 255, 255) if i == 2 else (150, 150, 150)
        text = font.render(os.path.basename(file), True, text_color)
        sidebar.blit(text, (10, 100 + i * 30))
    screen.blit(sidebar, (0, 0))
    
    # Bottom bar
    bottom_bar = pygame.Surface((SCREEN_WIDTH + SIDEBAR_WIDTH, BOTTOM_BAR_HEIGHT))
    bottom_bar.fill((20, 20, 20))
    file_type, file_size_bytes, creation_time = get_file_info(filepath)
    info_text = f"Type: {file_type} | Size: {file_size_bytes}B | Created: {creation_time} | Time left: {time_remaining:.1f}s"
    text_surface = font.render(info_text, True, (255, 255, 255))
    bottom_bar.blit(text_surface, (10, 15))
    screen.blit(bottom_bar, (0, SCREEN_HEIGHT))
    
    pygame.display.flip()

def choose_directory():
    directory = filedialog.askdirectory()
    if directory:
        files_data = read_files_as_binary(directory)
        if files_data:
            threading.Thread(target=play_binary_audio, args=(files_data, 44100), daemon=True).start()

def main():
    root = tk.Tk()
    root.withdraw()
    choose_directory()
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
    pygame.quit()

if __name__ == "__main__":
    main()
