#!/usr/bin/env python
# -*- coding: utf-8 -*-


from PIL import Image
from PIL.GifImagePlugin import getdata


def create_gif(path, files, delays, loops=0):
    imgs = []
    for img_file in files:
        img = Image.open(path + "/" + img_file)
        imgs.append(img)

    delays = [delay / 1000.0 for delay in delays]
    write_gif(path + ".gif", imgs, delays, loops)


def _int2bin(i):
    i1 = i % 256
    i2 = int(i/256)
    return chr(i1) + chr(i2)


def _get_header(im):
    bb = "GIF89a"
    bb += _int2bin(im.size[0])
    bb += _int2bin(im.size[1])
    bb += "\x87\x00\x00"
    return bb


def _get_app_ext(loops):
    if loops == 0:
        loops = 2**16-1
    bb = "\x21\xFF\x0B"
    bb += "NETSCAPE2.0"
    bb += "\x03\x01"
    bb += _int2bin(loops)
    bb += '\x00'
    return bb


def _get_graph_ctrl_ext(duration=0.1):
    bb = '\x21\xF9\x04\x08'
    bb += _int2bin(int(duration * 100))
    bb += '\xff\x00'
    return bb


def _get_image_des(im):
    bb = '\x2C'
    bb += _int2bin(0)
    bb += _int2bin(0)
    bb += _int2bin(im.size[0])
    bb += _int2bin(im.size[1])
    bb += '\x87'
    return bb


def _write_gif_to_file(fp, images, durations, loops):
    palettes, occur = [], []
    for im in images:
        palettes.append(im.palette.getdata()[1])
    for palette in palettes:
        occur.append(palettes.count(palette))

    global_palette = palettes[occur.index(max(occur))]

    frame = 0
    first_frame = True

    for im, palette in zip(images, palettes):

        if first_frame:
            header = _get_header(im)
            appext = _get_app_ext(loops)

            fp.write(header)
            fp.write(global_palette)
            fp.write(appext)

            first_frame = False
        if True:
            data = getdata(im)
            imdes, data = data[0], data[1:]
            graphext = _get_graph_ctrl_ext(durations[frame])
            lid = _get_image_des(im)

            if palette != global_palette:
                fp.write(graphext)
                fp.write(lid)
                fp.write(palette)
                fp.write('\x08')
            else:
                fp.write(graphext)
                fp.write(imdes)

            for d in data:
                fp.write(d)
        frame += 1

    fp.write(";")
    return frame


def write_gif(filename, images, duration, loops=0):
    p_images = []
    for i in range(len(images)):
        im = images[i].convert('RGB').convert('P', palette=Image.ADAPTIVE, dither=False, colors=255)
        p_images.append(im)

    with open(filename, 'wb') as gif_f:
        _write_gif_to_file(gif_f, p_images, duration, loops)

