
import PySimpleGUI as sg
import pyaudio
import numpy as np
import math
from screeninfo import get_monitors
import colorsys
from PIL import ImageGrab, Image

""" RealTime Audio Waveform plot """

# VARS CONSTS:
_VARS = {'window': False,
         'stream': False,
         'audioData': np.array([])}
WIDTH = 500
HEIGHT = 500
for m in get_monitors():
    print(str(m))
    WIDTH = m.width
    HEIGHT = m.height
print(WIDTH,HEIGHT)

# pysimpleGUI INIT:
AppFont = 'Any 16'
sg.theme('DarkBlue3')
layout = [[sg.Graph(canvas_size=(WIDTH, HEIGHT-200),
                    graph_bottom_left=(0, 0),
                    graph_top_right=(100, 100),
                    background_color='#809AB6',
                    key='graph')],
          [sg.ProgressBar(4000, orientation='h',
                          size=(20, 20), key='-PROG-'), 
           sg.Text('0', key='-VOL-')],
          [sg.Button('Listen', font=AppFont),
           sg.Button('Stop', font=AppFont, disabled=True),
           sg.Button('Exit', font=AppFont),
           sg.Button('Circle', font=AppFont),
           sg.Button('Line', font=AppFont),
           sg.Button('Trail', font=AppFont),
           sg.Button('Pixel', font=AppFont)]]
_VARS['window'] = sg.Window('Mic to waveform plot + Max Level',
                            layout, finalize=True,
                            background_color='#809AB6',
                            transparent_color='#809AB6',
                            keep_on_top=True,
                            no_titlebar=True )
_VARS['window'].Maximize()
graph = _VARS['window']['graph']

_VARS['window'].bind("<Escape>", "Exit")
_VARS['window'].bind("<c>", "Circle")
_VARS['window'].bind("<l>", "Line")
_VARS['window'].bind("<t>", "Trail")
_VARS['window'].bind("<p>", "Pixel")
_VARS['window'].bind("<Spacebar>", "Listen")


# INIT vars:
CHUNK = 1024  # Samples: 1024,  512, 256, 128
RATE = 44100  # Equivalent to Human Hearing at 40 kHz
INTERVAL = 1  # Sampling Interval in Seconds ie Interval to listen
TIMEOUT = 10  # In ms for the event loop
pAud = pyaudio.PyAudio()
CIRCLE = False
LINE = False
TRAIL = False
HUE = 0
PIXEL = False
maxVol = 0
vol = 0


# FUNCTIONS:

# PYSIMPLEGUI PLOTS


def drawAxis(dataRangeMin=0, dataRangeMax=100):
    # Y Axis
    graph.DrawLine((0, 50), (100, 50))
    # X Axis
    graph.DrawLine((0, dataRangeMin), (0, dataRangeMax))

# PYAUDIO STREAM


def stop():
    if _VARS['stream']:
        _VARS['stream'].stop_stream()
        _VARS['stream'].close()
        _VARS['window']['-PROG-'].update(0)
        _VARS['window']['-VOL-'].update('1')
        _VARS['window'].FindElement('Stop').Update(disabled=True)
        _VARS['window'].FindElement('Listen').Update(disabled=False)


def callback(in_data, frame_count, time_info, status):
    _VARS['audioData'] = np.frombuffer(in_data, dtype=np.int16)
    return (in_data, pyaudio.paContinue)


def listen():
    _VARS['window'].FindElement('Stop').Update(disabled=False)
    _VARS['window'].FindElement('Listen').Update(disabled=True)
    _VARS['stream'] = pAud.open(format=pyaudio.paInt16,
                                channels=1,
                                rate=RATE,
                                input=True,
                                frames_per_buffer=CHUNK,
                                stream_callback=callback)
    _VARS['stream'].start_stream()

def rgb_to_hex(r, g, b):
    return '#{:02x}{:02x}{:02x}'.format(int(r), int(g), int(b))

# INIT:

drawAxis()

listen()

im = Image.open('image.jpg', 'r')
imWidth, imHeight = im.size
pixel_values = list(im.getdata())
pixel_values = np.array(pixel_values).reshape((imWidth, imHeight, 3))
# MAIN LOOP
while True:
    HUE = (HUE+5)%360
    r, g, b = colorsys.hsv_to_rgb(HUE/360,1,1)
    #print(HUE,r,g,b)
    colour = rgb_to_hex(r*255, g*255, b*255)
    event, values = _VARS['window'].read(timeout=TIMEOUT)
    if event == sg.WIN_CLOSED or event == 'Exit':
        stop()
        pAud.terminate()
        break
    if event == 'Listen':
        listen()
    if event == 'Stop':
        stop()
    if event == 'Circle':
        if CIRCLE is False:
            CIRCLE = True
        else:
            CIRCLE = False
    if event == 'Line':
        if LINE is False:
            LINE = True
        else:
            LINE = False
    if event == 'Trail':
        if TRAIL is False:
            TRAIL = True
        else:
            TRAIL = False
    if event == 'Pixel':
        if PIXEL is False:
            PIXEL = True
        else:
            PIXEL = False

    # Along with the global audioData variable, this\
    # bit updates the waveform plot, left it here for
    # explanatory purposes, but could be a method.

    elif _VARS['audioData'].size != 0:
        # Uodate volumne meter
        vol = np.amax(_VARS['audioData'])
        _VARS['window']['-PROG-'].update(vol)
        if (vol > maxVol):
            maxVol = vol
            _VARS['window']['-VOL-'].update(str(maxVol))
        # Redraw plot
        if (HUE%50 == 0 or TRAIL is False):
            graph.erase()
        #drawAxis()
        
        # do pixilation stuff
        if PIXEL:
            #px = ImageGrab.grab().load()
            step = vol/(20000/50)
            if (step < 2):
                step = 2
            for x in range(0, imWidth, int(step)):
                for y in range(0, imHeight, int(step)):
                    pixColour = rgb_to_hex(pixel_values[imHeight-1-y][x][0], pixel_values[imHeight-1-y][x][1], pixel_values[imHeight-1-y][x][2])
                    point1 = (x,y)
                    point2 = ((x+step),(y+step))
                    #print("color "+str(pixColour)+" at "+str(point1)+" to "+str(point2))
                    graph.DrawRectangle(point1, point2, fill_color=pixColour, line_color=None)

        # Here we go through the points in the audioData object and draw them
        # Note that we are rescaling ( dividing by 100 ) and centering (+50 )
        # try different values to get a feel for what they do.
        currentPoint = (0,0)
        oldPoint = (0,0)
        if CIRCLE is False:
            i = 0
            for x in range(CHUNK):
                currentPoint = (x, (_VARS['audioData'][x]/100)+50)
                #print("circle at "+str(currentPoint))
                graph.DrawCircle(currentPoint, 0.4,
                                line_color=colour, fill_color=colour)
                if (i > 0 and LINE):
                    graph.DrawLine(oldPoint, currentPoint, color=colour)                
                oldPoint = currentPoint
                i += 1
        else:
            i = 0
            interval = 360/len(range(CHUNK))
            for x in range(CHUNK):
                angle = i*interval
                length = _VARS['audioData'][x]/25+25
                currentPoint = (50 + math.cos(math.radians(angle))*length, 50 + math.sin(math.radians(angle))*length)
                graph.DrawCircle(currentPoint, 0.4,
                                line_color=colour, fill_color=colour)
                if (i > 0 and LINE):
                    graph.DrawLine(oldPoint, currentPoint, color=colour)
                oldPoint = currentPoint
                
                i += 1

_VARS['window'].close()