
import argparse
import socket
import struct
import time
import tkinter as tk

import mss
import numpy as np
from PIL import Image


WIDTH = 128
HEIGHT = 64
FRAME_BYTES = WIDTH * HEIGHT // 8
HEADER_BYTES = 4
UDP_PORT = 4210


def select_region(monitor):
    """Let the user drag a rectangle over the first monitor."""
    root = tk.Tk()
    root.title("Select video region")
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.attributes("-alpha", 0.35)

    root.geometry(
        f"{monitor['width']}x{monitor['height']}"
        f"{monitor['left']:+d}{monitor['top']:+d}"
    )

    canvas = tk.Canvas(
        root,
        bg="black",
        cursor="crosshair",
        highlightthickness=0,
    )
    canvas.pack(fill="both", expand=True)

    canvas.create_text(
        20, 20,
        anchor="nw",
        fill="white",
        text="Drag to select the video area | ESC to cancel",
        font=("Sans", 14, "bold"),
    )

    start = None
    rectangle = None
    result = {"region": None}

    def on_press(event):
        nonlocal start, rectangle
        start = (event.x, event.y)

        if rectangle is not None:
            canvas.delete(rectangle)

        rectangle = canvas.create_rectangle(
            event.x, event.y, event.x, event.y,
            outline="white",
            width=2,
        )

    def on_drag(event):
        if start is not None and rectangle is not None:
            canvas.coords(
                rectangle,
                start[0], start[1], event.x, event.y,
            )

    def on_release(event):
        if start is None:
            return

        x1, y1 = start
        x2, y2 = event.x, event.y

        left = min(x1, x2) + monitor["left"]
        top = min(y1, y2) + monitor["top"]
        width = abs(x2 - x1)
        height = abs(y2 - y1)

        if width >= 2 and height >= 2:
            result["region"] = {
                "left": left,
                "top": top,
                "width": width,
                "height": height,
            }
            root.destroy()

    canvas.bind("<ButtonPress-1>", on_press)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", on_release)
    root.bind("<Escape>", lambda event: root.destroy())

    root.mainloop()

    if result["region"] is None:
        raise SystemExit("Region selection cancelled.")

    return result["region"]


def make_frame(sct, region):
    """Capture, resize and pack one frame as XBM-compatible bits."""
    shot = sct.grab(region)

    image = Image.frombytes("RGB", shot.size, shot.rgb)
    image = image.resize(
        (WIDTH, HEIGHT),
        Image.Resampling.LANCZOS,
    )

    # Convert to 1-bit black and white with dithering.
    image = image.convert("L").convert(
        "1",
        dither=Image.Dither.FLOYDSTEINBERG,
    )

    # XBM format: each row is 16 bytes, least-significant
    # bit first. This matches U8g2 drawXBMP().
    pixels = np.asarray(image, dtype=np.uint8) > 0
    packed = np.packbits(
        pixels,
        axis=1,
        bitorder="little",
    )

    frame = packed.tobytes()

    if len(frame) != FRAME_BYTES:
        raise RuntimeError(f"Unexpected frame size: {len(frame)}")

    return frame


def main():
    parser = argparse.ArgumentParser(
        description="Stream a desktop region to an ESP32 OLED."
    )
    parser.add_argument(
        "esp_ip",
        help="ESP32 IP address from Arduino Serial Monitor",
    )
    parser.add_argument("--port", type=int, default=UDP_PORT)
    parser.add_argument("--fps", type=float, default=30.0)
    args = parser.parse_args()

    if args.fps <= 0:
        parser.error("--fps must be greater than zero")

    interval = 1.0 / args.fps
    destination = (args.esp_ip, args.port)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        with mss.mss() as sct:
            # Select a region on the first monitor.
            monitor = sct.monitors[1]
            print("Drag over the video area to select it.")
            region = select_region(monitor)

            print(f"Capture region: {region}")
            print(f"Streaming to {destination} at {args.fps:g} FPS")
            print("Press Ctrl+C to stop.")

            sequence = 0
            count = 0
            report_time = time.perf_counter()

            while True:
                frame_start = time.perf_counter()

                frame = make_frame(sct, region)
                header = struct.pack("!I", sequence)
                packet = header + frame

                # One complete frame per UDP datagram.
                sock.sendto(packet, destination)

                sequence = (sequence + 1) & 0xFFFFFFFF
                count += 1

                elapsed = time.perf_counter() - frame_start
                time.sleep(max(0.0, interval - elapsed))

                now = time.perf_counter()
                if now - report_time >= 1.0:
                    actual_fps = count / (now - report_time)
                    print(
                        f"Send FPS: {actual_fps:.1f} | "
                        f"Frame: {FRAME_BYTES} bytes"
                    )
                    count = 0
                    report_time = now

    except KeyboardInterrupt:
        print("\nStreaming stopped.")
    finally:
        sock.close()


if __name__ == "__main__":
    main()
