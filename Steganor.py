from flask import Flask, render_template, request
from PIL import Image
from io import BytesIO
import base64
import os
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto import Random

app = Flask(__name__)
DEBUG = False
headerText = "M6nMjy5THr2J"


def encrypt(key, source, encode=True):
    key = SHA256.new(key).digest()
    IV = Random.new().read(AES.block_size)
    encryptor = AES.new(key, AES.MODE_CBC, IV)
    padding = AES.block_size - len(source) % AES.block_size
    source += bytes([padding]) * padding
    data = IV + encryptor.encrypt(source)
    return base64.b64encode(data).decode() if encode else data


def decrypt(key, source, decode=True):
    if decode:
        source = base64.b64decode(source.encode())
    key = SHA256.new(key).digest()
    IV = source[:AES.block_size]
    decryptor = AES.new(key, AES.MODE_CBC, IV)
    data = decryptor.decrypt(source[AES.block_size:])
    padding = data[-1]
    if data[-padding:] != bytes([padding]) * padding:
        raise ValueError("Invalid padding...")
    return data[:-padding]


def convertToRGB(img):
    try:
        rgba_image = img
        rgba_image.load()
        background = Image.new("RGB", rgba_image.size, (255, 255, 255))
        background.paste(rgba_image, mask=rgba_image.split()[3])
        print("[yellow]Converted image to RGB [/yellow]")
        return background
    except Exception as e:
        print("[red]Couldn't convert image to RGB [/red]- %s" % e)


def encodeImage(image, message, password):
    try:
        width, height = image.size
        pix = image.getdata()
        current_pixel = 0
        tmp = 0

        for ch in message:
            binary_value = format(ord(ch), '08b')

            p1 = pix[current_pixel]
            p2 = pix[current_pixel + 1]
            p3 = pix[current_pixel + 2]

            three_pixels = [val for val in p1 + p2 + p3]

            for i in range(0, 8):
                current_bit = binary_value[i]

                if current_bit == '0':
                    if three_pixels[i] % 2 != 0:
                        three_pixels[i] = three_pixels[i] - 1 if three_pixels[i] == 255 else three_pixels[i] + 1
                elif current_bit == '1':
                    if three_pixels[i] % 2 == 0:
                        three_pixels[i] = three_pixels[i] - 1 if three_pixels[i] == 255 else three_pixels[i] + 1

            current_pixel += 3
            tmp += 1

            if tmp == len(message):
                if three_pixels[-1] % 2 == 0:
                    three_pixels[-1] = three_pixels[-1] - 1 if three_pixels[-1] == 255 else three_pixels[-1] + 1
            else:
                if three_pixels[-1] % 2 != 0:
                    three_pixels[-1] = three_pixels[-1] - 1 if three_pixels[-1] == 255 else three_pixels[-1] + 1

            three_pixels = tuple(three_pixels)

            st = 0
            end = 3

            for i in range(0, 3):
                image.putpixel((current_pixel, current_pixel), three_pixels[st:end])
                st += 3
                end += 3

                if (current_pixel == width - 1):
                    current_pixel = 0
                else:
                    current_pixel += 1

        encoded_filename = "encoded.png"
        image.save(encoded_filename)
        print("\n")
        print("[yellow]Image encoded and saved as [u][bold]%s[/green][/u][/bold]" % encoded_filename)
        return encoded_filename

    except Exception as e:
        print("[red]An error occurred - [/red]%s" % e)
        return None


def decodeImage(image, password):
    try:
        pix = image.getdata()
        current_pixel = 0
        decoded = ""

        while True:
            binary_value = ""
            p1 = pix[current_pixel]
            p2 = pix[current_pixel + 1]
            p3 = pix[current_pixel + 2]
            three_pixels = [val for val in p1 + p2 + p3]

            for i in range(0, 8):
                if three_pixels[i] % 2 == 0:
                    binary_value += "0"
                elif three_pixels[i] % 2 != 0:
                    binary_value += "1"

            binary_value.strip()
            ascii_value = int(binary_value, 2)
            decoded += chr(ascii_value)
            current_pixel += 3

            if three_pixels[-1] % 2 != 0:
                break

        return decoded

    except Exception as e:
        print("[red]An error occurred - [/red]%s" % e)
        return None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/encode', methods=['POST'])
def encode():
    img = request.files['image']
    message = request.form['message']
    password = request.form['password']

    try:
        image = Image.open(img)
        if image.mode != 'RGB':
            image = convertToRGB(image)

        newimg = image.copy()
        encoded_filename = encodeImage(image=newimg, message=message, password=password)

        if encoded_filename:
            return render_template('result.html', result=f"Image encoded and saved as {encoded_filename}")
        else:
            return render_template('result.html', result="Error encoding image")

    except Exception as e:
        return render_template('result.html', result=f"An error occurred - {e}")


@app.route('/decode', methods=['POST'])
def decode():
    img = request.files['image']
    password = request.form['password']

    try:
        image = Image.open(img)
        decoded_message = decodeImage(image=image, password=password)

        if decoded_message:
            return render_template('result.html', result=f"Decoded Text: {decoded_message}")
        else:
            return render_template('result.html', result="Error decoding image")

    except Exception as e:
        return render_template('result.html', result=f"An error occurred - {e}")


if __name__ == '__main__':
    app.run(debug=True)