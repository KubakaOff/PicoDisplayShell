import builtins,deflate,gc,json,jpegdec,io,math,os,time,random
from machine import Timer, Pin
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY, PEN_RGB332
from pimoroni import RGBLED, Button
led = RGBLED(6, 7, 8)
button_a = Button(12, repeat_time=500)
a_pressed = False
button_b = Button(13, repeat_time=600)
button_b_held = Button(13)
button_b_held_duration = 0
b_held_executed = False
button_x = Button(14, repeat_time=110, hold_time=750)
button_y = Button(15, repeat_time=110, hold_time=750)
display = PicoGraphics(display=DISPLAY_PICO_DISPLAY, pen_type=PEN_RGB332, rotate=0)
WHITE = display.create_pen(255,255,255)
BLACK = display.create_pen(0,0,0)
WIDTH, HEIGHT = display.get_bounds()
COMMAND_QUEUE = ["(A): Enter a character","(X): Next Character","(Y): Previous Character","(B): Press - Backspace ; Hold - Enter"]
MAX_LINES = 15
CURRENT_CHAR_INDEX = 0
CHARS = """ abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890.,+-*/\|!?&%^$@#~="':;()<>{}[]"""
COMMAND_TO_EXECUTE = ""
CURRENT_DIRECTORY = "/"
EXECUTING_COMMAND = False
PROVIDING_INPUT = False
config_file_path = 'config.json'
default_config = {
    'username': 'root',
    'device_name': 'pico',
    'backlight': 0.5,
    'oc' : False}
led.set_rgb(0,0,0)
timer_b_active = False
display.set_font('bitmap8')
def load_config(file):
    try:
        with open(file, 'r') as f:
            config = json.load(f)
    except OSError:
        config = default_config
        save_config(file, config)
    return config
def save_config(file, config):
    with open(file, 'w') as f:
        json.dump(config, f)
def cleardisp():
    display.set_pen(BLACK)
    display.clear()
def display_text_on_line(text, line):
    display.text(text, 0, line * 9, scale=1)
def input(prompt):
    global COMMAND_QUEUE, CHARS, CURRENT_CHAR_INDEX, COMMAND_TO_EXECUTE, EXECUTING_COMMAND, PROVIDING_INPUT
    EXECUTING_COMMAND = True
    PROVIDING_INPUT = True
    COMMAND_TO_EXECUTE = ""
    print(prompt + CHARS[CURRENT_CHAR_INDEX])
    while PROVIDING_INPUT:
        handle_button_presses()
    output = COMMAND_TO_EXECUTE
    COMMAND_TO_EXECUTE = ""
    EXECUTING_COMMAND = False
    return output

def print(*args, sep=' ', end='\n', file=None, flush=None):
    text = sep.join(map(str, args))
    global COMMAND_QUEUE
    cleardisp()
    display.set_font('bitmap8')
    display.set_pen(WHITE)
    MAX_TEXT_WIDTH = WIDTH
    wrapped_lines = wrap_text_lines(text, MAX_TEXT_WIDTH)

    if len(wrapped_lines) >= MAX_LINES:
        COMMAND_QUEUE = []
        COMMAND_QUEUE.extend(wrapped_lines[-15:])
    else:
        while len(COMMAND_QUEUE) + len(wrapped_lines) > MAX_LINES:
            COMMAND_QUEUE.pop(0)
    COMMAND_QUEUE.extend(wrapped_lines)

    for i, line in enumerate(COMMAND_QUEUE):
        display.text(line, 0, i * 9, scale=1, spacing=1)
    display.update()

def separate_generator(char="=", times=60):
    return char * times

def wrap_text_lines(text, max_width):
    wrapped_lines = []
    current_line = ""

    for char in str(text):
        current_line_width = display.measure_text(current_line + char, 1, 1)

        if current_line_width <= max_width:
            current_line += char
        else:
            wrapped_lines.append(current_line)
            current_line = char

    wrapped_lines.append(current_line)

    for i in range(len(wrapped_lines)):
        line_width = display.measure_text(wrapped_lines[i], 1, 1)
        if line_width > max_width:
            excess_width = line_width - max_width
            num_lines_to_remove = (excess_width // max_width) + 1

            del wrapped_lines[i:i+num_lines_to_remove]
            break

    adjusted_lines = []
    for line in wrapped_lines:
        while display.measure_text(line, 1, 1) > max_width:
            new_line = line[:-1]
            wrapped_char = line[-1]
            adjusted_lines.append(new_line)
            line = wrapped_char
        adjusted_lines.append(line)

    return adjusted_lines
def handle_button_presses():
    global CURRENT_CHAR_INDEX, COMMAND_QUEUE, button_b_held_duration, b_held_executed, a_pressed, COMMAND_TO_EXECUTE, PROVIDING_INPUT
    if button_x.read():
        cleardisp()
        display.set_pen(WHITE)
        CURRENT_CHAR_INDEX = (CURRENT_CHAR_INDEX + 1) % len(CHARS)
        if COMMAND_QUEUE:
            last_line_index = len(COMMAND_QUEUE) - 1
            last_line = COMMAND_QUEUE[last_line_index]
            COMMAND_QUEUE[last_line_index] = last_line[:-1] + CHARS[CURRENT_CHAR_INDEX]
        else:
            COMMAND_QUEUE.append(CHARS[CURRENT_CHAR_INDEX])
        for i, line in enumerate(COMMAND_QUEUE):
            display.text(line, 0, i * 9, scale=1, spacing=1)
        display.update()
    if button_y.read():
        cleardisp()
        display.set_pen(WHITE)
        CURRENT_CHAR_INDEX = (CURRENT_CHAR_INDEX - 1) % len(CHARS)
        if COMMAND_QUEUE:
            last_line_index = len(COMMAND_QUEUE) - 1
            last_line = COMMAND_QUEUE[last_line_index]
            COMMAND_QUEUE[last_line_index] = last_line[:-1] + CHARS[CURRENT_CHAR_INDEX]
        else:
            COMMAND_QUEUE.append(CHARS[CURRENT_CHAR_INDEX])
        for i, line in enumerate(COMMAND_QUEUE):
            display.text(line, 0, i * 9, scale=1, spacing=1)
        display.update()
    if button_a.read():
        if not a_pressed:
            cleardisp()
            display.set_pen(WHITE)
            COMMAND_TO_EXECUTE = str(COMMAND_TO_EXECUTE) + str(CHARS[CURRENT_CHAR_INDEX])
            if COMMAND_QUEUE:
                last_line_index = len(COMMAND_QUEUE) - 1
                last_line = COMMAND_QUEUE[last_line_index]
                last_line_index = len(COMMAND_QUEUE) - 1
                COMMAND_QUEUE[last_line_index] = last_line + CHARS[CURRENT_CHAR_INDEX]
                wrapped_lines = wrap_text_lines(COMMAND_QUEUE[last_line_index], WIDTH)
                if len(wrapped_lines) >= MAX_LINES:
                    COMMAND_QUEUE = wrapped_lines[-15:]
                else:
                    COMMAND_QUEUE.pop(len(COMMAND_QUEUE) - 1)
                    while len(COMMAND_QUEUE) + len(wrapped_lines) > MAX_LINES:
                        COMMAND_QUEUE.pop(0)
                COMMAND_QUEUE.extend(wrapped_lines)
            for i, line in enumerate(COMMAND_QUEUE):
                display.text(line, 0, i * 9, scale=1, spacing=1)
            display.update()
        else:
            a_pressed = False
    if button_b_held.raw():
        button_b_held_duration += 1

    if button_b_held_duration >= 50:
        handle_button_b_long()
        b_held_executed = True
    elif button_b_held_duration > 0 and not button_b.raw() and not b_held_executed:
        handle_button_b_short()
        button_b_held_duration = 0
    elif not button_b_held.raw():
        button_b_held_duration = 0
        b_held_executed = False
    time.sleep(0.01)

def handle_button_b_short():
    global COMMAND_QUEUE, COMMAND_TO_EXECUTE, CHARS, CURRENT_CHAR_INDEX
    last_line_index = len(COMMAND_QUEUE) - 1
    last_line = COMMAND_QUEUE[last_line_index]

    if last_line and COMMAND_QUEUE:
        if COMMAND_TO_EXECUTE != "":
            # Remove the last character from the last line (simulate backspace)
            COMMAND_QUEUE[last_line_index] = last_line[:-2] + CHARS[CURRENT_CHAR_INDEX]
            COMMAND_TO_EXECUTE = COMMAND_TO_EXECUTE[:-1]
    else:
        # Remove the last line from COMMAND_QUEUE (simulate backspace on an empty line)
        COMMAND_QUEUE.pop()
    update_terminal()
def handle_button_b_long():
    global COMMAND_QUEUE, PROVIDING_INPUT, button_b_held_duration
    button_b_held_duration = 0
    last_line_index = len(COMMAND_QUEUE) - 1
    last_line = COMMAND_QUEUE[last_line_index]
    last_line = last_line[:-1]
    COMMAND_QUEUE[-1] = last_line
    if not PROVIDING_INPUT:
        execute_commands(COMMAND_TO_EXECUTE)
        update_terminal()
    elif PROVIDING_INPUT:
        PROVIDING_INPUT=False

def update_terminal():
    global COMMAND_QUEUE
    cleardisp()
    display.set_pen(WHITE)
    if COMMAND_QUEUE:
        last_line_index = len(COMMAND_QUEUE) - 1
        last_line = COMMAND_QUEUE[last_line_index]
        wrapped_lines = wrap_text_lines(last_line, WIDTH)
        if len(wrapped_lines) >= MAX_LINES:
            COMMAND_QUEUE = []
            COMMAND_QUEUE.extend(wrapped_lines[-15:])
        else:
            COMMAND_QUEUE.pop()
            while len(COMMAND_QUEUE) + len(wrapped_lines) > MAX_LINES:
                COMMAND_QUEUE.pop(0)
        COMMAND_QUEUE.extend(wrapped_lines)
    for i, line in enumerate(COMMAND_QUEUE):
        display.text(line, 0, i * 9, scale=1, spacing=1)
    display.update()

def update_line(text, line):
    pass # WILL WORK ON THIS LATER

def microreader(filename):
    global COMMAND_QUEUE
    cursor_position = 0
    button_x = Button(14)
    button_y = Button(15)
    button_a = Button(12)
    COMMAND_QUEUE = []
    try:
        with open(filename, 'rb') as f:
            gc.collect()
            if filename.lower().endswith('.gz'):
                COMMAND_QUEUE.append("Decompressing file...")
                update_terminal()
                stream = io.BytesIO(f.read())
                d_stream = deflate.DeflateIO(stream)
                data_str = d_stream.read().decode()
                text = data_str.split('\n')
            else:
                text = f.readlines()
            COMMAND_QUEUE.append("Loading microreader...")
            update_terminal()
            lines = []
            for i, line in enumerate(text):
                lines.extend(wrap_text_lines(line, WIDTH))
        while True:
            if button_x.read():
                if cursor_position > 0:
                    cursor_position -=1
            elif button_y.read():
                if cursor_position < len(lines) - 15:
                    cursor_position +=1
            elif button_a.read():
                a_pressed = True
                COMMAND_QUEUE = []
                gc.collect()
                break
            start_line = max(0, cursor_position)
            end_line = min(len(lines), start_line + min(15, len(lines)))
            display_lines = lines[start_line:end_line]
            display_lines += [''] * (15 - len(display_lines))
            cleardisp()
            display.set_pen(WHITE)
            for i, line in enumerate(display_lines):
                display.text(str(line), 0, i * 9, scale=1, spacing=1)
            display.update()
    except OSError:
        print(f"File '{parts[1]}' not found.")

def execute_commands(command=COMMAND_TO_EXECUTE):
    global EXECUTING_COMMAND, CHARS, CURRENT_CHAR_INDEX, CURRENT_DIRECTORY, backlight, config, COMMAND_QUEUE,a_pressed, COMMAND_TO_EXECUTE
    if not PROVIDING_INPUT:
        EXECUTING_COMMAND = True
        command = str(command)
        parts = command.split()
        if not parts:
            print("No command provided.")
        elif parts[0] == "ls":
            print(CURRENT_DIRECTORY)
            if len(parts) == 2:
                if parts[1].startswith('/'):
                    file_list = os.listdir(parts[1])
                else:
                    file_list = os.listdir(CURRENT_DIRECTORY + '/' + parts[1])
            else:
                file_list = os.listdir(CURRENT_DIRECTORY)
            max_width = max(len(item) for item in file_list) + 2
            terminal_width = 40
            num_columns = terminal_width // max_width
            for i, item in enumerate(file_list):
                print(f"{item:{max_width}}")
        elif parts[0] == "echo":
            words = command.split()[1:]
            to_echo = ' '.join(words)
            print(to_echo)
        elif parts[0] == "cat":
            files = parts[1:]
            output_file = None
            if ">" in parts:
                output_file_index = parts.index(">")
                if output_file_index + 1 < len(parts):
                    output_file = parts[output_file_index + 1]
            if ">>" in parts:
                output_file_index = parts.index(">>")
                if output_file_index + 1 < len(parts):
                    output_file = parts[output_file_index + 1]
                    mode = "a"
                else:
                    mode = "w"
            for file_name in files:
                try:
                    with open(file_name, 'r') as file:
                        content = file.read()

                    if output_file:
                        with open(output_file, mode) as output:
                            output.write(content)
                    else:
                        print(content)

                except OSError:
                    print(f"cat: {file_name}: No such file or directory")
        elif parts[0] == "micropython" or parts[0] == "mp":
            if len(parts) == 2:
                try:
                    with open(parts[1], 'r') as f:
                        if parts[1].lower().endswith('.gz'):
                            with open(parts[1],'rb')as f:gc.collect();d=deflate.DeflateIO(f);p=d.read();exec(p);gc.collect()
                        else:
                            script_code = f.read()
                            gc.collect()
                            exec(script_code)
                            gc.collect()
                except OSError:
                    print(f"Error: File '{parts[1]}' not found.")
            else:
                print("Usage: 'micropython [file]'")
        elif parts[0] == "microreader" or parts[0] == "mr":
            if len(parts) == 2:
                microreader(parts[1])
            else:
                print("Usage: 'microreader [file]'")
        elif parts[0] == "mem":
            free_ram = gc.mem_free()
            used_ram = gc.mem_alloc()
            total_ram = free_ram + used_ram
            print(f"{math.floor(used_ram/1024)} kB/{math.floor(total_ram/1024)} kB used.")
        elif parts[0] == "freemem" or parts[0] == "fm":
            beforeclean = gc.mem_alloc()
            gc.collect()
            afterclean = gc.mem_alloc()
            print(f"Freed {beforeclean-afterclean} bytes of memory ({math.floor((abs(beforeclean - afterclean) / beforeclean) * 100)}%).")
        elif parts[0] == "microfetch" or parts[0] == "mf":
            print("System Information:")
            print(separate_generator())
            print("Board: "+ os.uname().machine)
            print("  CPU Frequency: " + str(math.floor(machine.freq()/1000000)) + " MHz")
            print("MicroPython version: "+ str(os.uname().version))
    
            free_ram = gc.mem_free()
            used_ram = gc.mem_alloc()
            total_ram = free_ram + used_ram
            ram_perc = int((used_ram / total_ram) * 100)
            print("RAM Usage: " + str(math.floor(used_ram/1024)) + " kB/" + str(math.floor(total_ram/1024)) + " kB (" + str(ram_perc) + "% used)")
    
            fs_stat = os.statvfs('/')
            total_space = fs_stat[0] * fs_stat[2]
            free_space = fs_stat[0] * fs_stat[3]
            print("Storage:")
            print("  Total Space: " + str(math.floor(total_space/1024)) + " kB")
            print("  Free Space: " + str(math.floor(free_space/1024)) + " kB")
        elif parts[0] == "cd":
            try:
                os.chdir(parts[1])
                CURRENT_DIRECTORY = os.getcwd()
            except OSError:
                print(f"Directory '{parts[1]}' not found!")
        elif parts[0] == "username" or parts[0] == "un":
            if parts[1] != "change":
                print(username)
            else:
                config['username'] = parts[2]
                save_config(config_file_path, config)
                print(f"Username changed to '{parts[2]}'.")
        elif parts[0] == "devicename":
            if parts[1] != "change":
                print(device_name)
            else:
                config['device_name'] = parts[2]
                save_config(config_file_path, config)
                print(f"Device name changed to '{parts[2]}'.")
        elif parts[0] == "help":
            microreader("help.gz")
        elif parts[0] == "mkdir":
            if len(parts) == 2:
                if str(parts[1].startswith('/')):
                    os.mkdir(str(parts[1]))
                else:
                    os.mkdir(str(CURRENT_DIRECTORY) + '/' + str(parts[1]))
            else:
                print("Usage: 'mkdir [dir]'")
        elif parts[0] == "backlight" or parts[0] == "bl":
            if len(parts) == 1:
                print(str(backlight))
            elif len(parts) == 2:
                fl = float(parts[1])
                if 0 <= fl <= 1:
                    backlight = fl
                    config['backlight'] = backlight
                    save_config(config_file_path, config)
                    display.set_backlight(fl)
                else:
                    print("The value must be between 0 and 1.")
            else:
                print("Usage: 'backlight {value}'")
        elif parts[0] == "pwd":
            print(CURRENT_DIRECTORY)
        elif parts[0] == "oc":
            if len(parts) == 1:
                print(f"Current CPU Frequency is {math.floor(machine.freq()/1000000)} MHz.")
            elif len(parts) == 2:
                fre = int(parts[1]) * 1000
                fre *= 1000
                machine.freq(fre)
                time.sleep(0.5)
                gc.collect()
                print(f"Current CPU Frequency is {math.floor(machine.freq()/1000000)} MHz.")
            else:
                print("Usage: 'oc {frequency (in MHz)}'")
        elif parts[0] == "microjpg" or parts[0] == "mj":
            if len(parts) == 2:
                gc.collect()
                zoom = 0
                btn_x = Button(14)
                btn_a = Button(12)
                if CURRENT_DIRECTORY != '/':
                    file = str(CURRENT_DIRECTORY) + '/' + str(parts[1])
                else:
                    file = str(parts[1])
                cleardisp()
                jpg = jpegdec.JPEG(display)
                jpg.open_file(file)
                jpg.decode(0, 0, zoom)
                display.update()
                while True:
                    if btn_x.read():
                        if zoom >= 8:
                            zoom = 0
                        elif zoom == 0:
                            zoom = 2
                        else:
                            zoom = zoom * 2
                        cleardisp()
                        jpg.decode(0, 0, zoom)
                        display.update()
                    elif btn_a.read():
                        a_pressed = True
                        gc.collect()
                        break
            else:
                print("Usage: 'microjpg [jpg file]'")
        else:
            print("Command not found. Check the command 'help' for help.")
        COMMAND_TO_EXECUTE = ""
        EXECUTING_COMMAND=False
        gc.collect()
        print(f"{username}@{device_name}:{CURRENT_DIRECTORY}$ " + CHARS[CURRENT_CHAR_INDEX])
config = load_config(config_file_path)
username = config['username']
device_name = config['device_name']
backlight = config['backlight']
ocfreq = config['oc']
if ocfreq != False:
    fre = int(ocfreq) * 1000
    fre *= 1000
    machine.freq(fre)
    time.sleep(0.5)
display.set_backlight(backlight)
cleardisp()
# COMMENT THIS IF YOU HAVE A STARTER COMMAND
print(f"{username}@{device_name}:{CURRENT_DIRECTORY}$ " + CHARS[CURRENT_CHAR_INDEX])
# UNCOMMENT THIS IF YOU WANT A STARTER COMMAND
# execute_commands('microfetch')
gc.collect()
while True:
    if not EXECUTING_COMMAND:
        # COMMENT THIS IF YOU WANT TO EXECUTE THE COMMANDS THROUGH A PC
        handle_button_presses()
        # UNCOMMENT THIS IF YOU WANT TO EXECUTE THE COMMANDS THROUGH A PC
        # execute_commands(builtins.input(f"{username}@{device_name}:{CURRENT_DIRECTORY}$ "))
