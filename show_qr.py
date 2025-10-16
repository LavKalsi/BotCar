import socket
import qrcode
from PIL import Image

def get_local_ip():
    """Get the Raspberry Pi local IP address on the network."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "0.0.0.0"

def main():
    ip = get_local_ip()
    url = f"http://{ip}:5000"  # Flask control server

    # Generate QR code
    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Show the QR code image using default viewer
    img.show(title=f"Scan to control car ({url})")

    # Optionally save the QR code for later
    img.save("/tmp/car_control_qr.png")
    print(f"QR code generated for {url}")

if __name__ == "__main__":
    main()
