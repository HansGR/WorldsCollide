"""Minimal headless libretro frontend for the playtest harness.

Drives a libretro SNES core (snes9x) directly through its C ABI via
ctypes: one retro_run() call per frame, a live pointer to WRAM for state
assertions and pokes, savestates via retro_serialize, scripted joypad
input, and RGB565 framebuffer capture for PNG screenshots.

No display, no audio device, no RetroArch -- pure CPU emulation.

Core sourcing: the stable-retro PyPI package bundles a Linux x86_64
snes9x_libretro.so (see find_core()); no separate download or build is
required.
"""

import ctypes as C
import struct
import zlib
import os

# --- libretro constants ---------------------------------------------------

RETRO_ENVIRONMENT_GET_CAN_DUPE = 3
RETRO_ENVIRONMENT_GET_SYSTEM_DIRECTORY = 9
RETRO_ENVIRONMENT_SET_PIXEL_FORMAT = 10
RETRO_ENVIRONMENT_GET_VARIABLE = 15
RETRO_ENVIRONMENT_GET_VARIABLE_UPDATE = 17
RETRO_ENVIRONMENT_GET_LOG_INTERFACE = 27
RETRO_ENVIRONMENT_GET_SAVE_DIRECTORY = 31

RETRO_PIXEL_FORMAT_0RGB1555 = 0
RETRO_PIXEL_FORMAT_XRGB8888 = 1
RETRO_PIXEL_FORMAT_RGB565 = 2

RETRO_MEMORY_SAVE_RAM = 0
RETRO_MEMORY_SYSTEM_RAM = 2

RETRO_DEVICE_JOYPAD = 1

JOYPAD = {
    'B': 0, 'Y': 1, 'SELECT': 2, 'START': 3,
    'UP': 4, 'DOWN': 5, 'LEFT': 6, 'RIGHT': 7,
    'A': 8, 'X': 9, 'L': 10, 'R': 11,
}

# --- callback signatures --------------------------------------------------

environment_t = C.CFUNCTYPE(C.c_bool, C.c_uint, C.c_void_p)
video_refresh_t = C.CFUNCTYPE(None, C.c_void_p, C.c_uint, C.c_uint, C.c_size_t)
audio_sample_t = C.CFUNCTYPE(None, C.c_int16, C.c_int16)
audio_sample_batch_t = C.CFUNCTYPE(C.c_size_t, C.POINTER(C.c_int16), C.c_size_t)
input_poll_t = C.CFUNCTYPE(None)
input_state_t = C.CFUNCTYPE(C.c_int16, C.c_uint, C.c_uint, C.c_uint, C.c_uint)


class retro_game_info(C.Structure):
    _fields_ = [
        ("path", C.c_char_p),
        ("data", C.c_void_p),
        ("size", C.c_size_t),
        ("meta", C.c_char_p),
    ]


class retro_system_info(C.Structure):
    _fields_ = [
        ("library_name", C.c_char_p),
        ("library_version", C.c_char_p),
        ("valid_extensions", C.c_char_p),
        ("need_fullpath", C.c_bool),
        ("block_extract", C.c_bool),
    ]


class retro_game_geometry(C.Structure):
    _fields_ = [
        ("base_width", C.c_uint),
        ("base_height", C.c_uint),
        ("max_width", C.c_uint),
        ("max_height", C.c_uint),
        ("aspect_ratio", C.c_float),
    ]


class retro_system_timing(C.Structure):
    _fields_ = [
        ("fps", C.c_double),
        ("sample_rate", C.c_double),
    ]


class retro_system_av_info(C.Structure):
    _fields_ = [
        ("geometry", retro_game_geometry),
        ("timing", retro_system_timing),
    ]


def find_core():
    """Locate the snes9x libretro core bundled with the stable-retro
    PyPI package (pip install stable-retro)."""
    try:
        import stable_retro
        path = os.path.join(os.path.dirname(stable_retro.__file__),
                            "cores", "snes9x_libretro.so")
        if os.path.exists(path):
            return path
    except ImportError:
        pass
    raise FileNotFoundError(
        "snes9x_libretro.so not found: pip install stable-retro")


class Core:
    """One loaded libretro core instance driving one ROM.

    Note: libretro cores are stateful singletons per process -- create
    only one Core per Python process (fork for parallelism).
    """

    def __init__(self, core_path=None, rom_path=None):
        self.lib = C.CDLL(core_path or find_core())
        self._setup_prototypes()

        # State captured by callbacks
        self.frame = None          # (bytes, width, height, pitch) RGB565
        self.buttons = set()       # currently-held JOYPAD button names
        self.frame_count = 0
        self._pixel_format = RETRO_PIXEL_FORMAT_0RGB1555  # libretro default

        # Persistent buffers handed to the core (must outlive it)
        self._sysdir = C.c_char_p(b"/tmp")
        self._savedir = C.c_char_p(b"/tmp")

        # Keep callback objects referenced or ctypes will GC them
        self._cb_env = environment_t(self._on_environment)
        self._cb_video = video_refresh_t(self._on_video)
        self._cb_audio = audio_sample_t(lambda l, r: None)
        self._cb_audio_batch = audio_sample_batch_t(lambda data, frames: frames)
        self._cb_input_poll = input_poll_t(lambda: None)
        self._cb_input_state = input_state_t(self._on_input_state)

        self.lib.retro_set_environment(self._cb_env)
        self.lib.retro_init()
        self.lib.retro_set_video_refresh(self._cb_video)
        self.lib.retro_set_audio_sample(self._cb_audio)
        self.lib.retro_set_audio_sample_batch(self._cb_audio_batch)
        self.lib.retro_set_input_poll(self._cb_input_poll)
        self.lib.retro_set_input_state(self._cb_input_state)

        if rom_path is not None:
            self.load(rom_path)

    def _setup_prototypes(self):
        lib = self.lib
        lib.retro_set_environment.argtypes = [environment_t]
        lib.retro_set_video_refresh.argtypes = [video_refresh_t]
        lib.retro_set_audio_sample.argtypes = [audio_sample_t]
        lib.retro_set_audio_sample_batch.argtypes = [audio_sample_batch_t]
        lib.retro_set_input_poll.argtypes = [input_poll_t]
        lib.retro_set_input_state.argtypes = [input_state_t]
        lib.retro_load_game.argtypes = [C.POINTER(retro_game_info)]
        lib.retro_load_game.restype = C.c_bool
        lib.retro_get_system_info.argtypes = [C.POINTER(retro_system_info)]
        lib.retro_get_system_av_info.argtypes = [C.POINTER(retro_system_av_info)]
        lib.retro_get_memory_data.argtypes = [C.c_uint]
        lib.retro_get_memory_data.restype = C.c_void_p
        lib.retro_get_memory_size.argtypes = [C.c_uint]
        lib.retro_get_memory_size.restype = C.c_size_t
        lib.retro_serialize_size.restype = C.c_size_t
        lib.retro_serialize.argtypes = [C.c_void_p, C.c_size_t]
        lib.retro_serialize.restype = C.c_bool
        lib.retro_unserialize.argtypes = [C.c_void_p, C.c_size_t]
        lib.retro_unserialize.restype = C.c_bool

    # --- callbacks --------------------------------------------------------

    def _on_environment(self, cmd, data):
        if cmd == RETRO_ENVIRONMENT_GET_CAN_DUPE:
            C.cast(data, C.POINTER(C.c_bool))[0] = True
            return True
        if cmd == RETRO_ENVIRONMENT_SET_PIXEL_FORMAT:
            self._pixel_format = C.cast(data, C.POINTER(C.c_uint))[0]
            return True
        if cmd == RETRO_ENVIRONMENT_GET_SYSTEM_DIRECTORY:
            C.cast(data, C.POINTER(C.c_char_p))[0] = self._sysdir
            return True
        if cmd == RETRO_ENVIRONMENT_GET_SAVE_DIRECTORY:
            C.cast(data, C.POINTER(C.c_char_p))[0] = self._savedir
            return True
        # Everything else (core options, log interface, ...): defaults
        return False

    def _on_video(self, data, width, height, pitch):
        if data:  # None = duped frame, keep previous
            buf = C.string_at(data, pitch * height)
            self.frame = (buf, width, height, pitch)

    def _on_input_state(self, port, device, index, button_id):
        if port == 0 and device == RETRO_DEVICE_JOYPAD:
            for name in self.buttons:
                if JOYPAD[name] == button_id:
                    return 1
        return 0

    # --- game control -----------------------------------------------------

    def load(self, rom_path):
        with open(rom_path, 'rb') as f:
            self._rom_data = f.read()  # keep referenced for the core
        info = retro_game_info()
        info.path = rom_path.encode()
        info.data = C.cast(C.c_char_p(self._rom_data), C.c_void_p)
        info.size = len(self._rom_data)
        info.meta = None
        if not self.lib.retro_load_game(C.byref(info)):
            raise RuntimeError(f"core failed to load {rom_path}")

        av = retro_system_av_info()
        self.lib.retro_get_system_av_info(C.byref(av))
        self.fps = av.timing.fps

        wram_ptr = self.lib.retro_get_memory_data(RETRO_MEMORY_SYSTEM_RAM)
        wram_size = self.lib.retro_get_memory_size(RETRO_MEMORY_SYSTEM_RAM)
        if not wram_ptr or wram_size == 0:
            raise RuntimeError("core did not expose system RAM")
        # Live view of WRAM ($7E0000-$7FFFFF): read AND write
        self.wram = (C.c_ubyte * wram_size).from_address(wram_ptr)
        self.wram_size = wram_size

    def run(self, frames=1):
        for _ in range(frames):
            self.lib.retro_run()
            self.frame_count += 1

    def run_until(self, predicate, timeout=3600, step=1):
        """Advance frames until predicate(self) is true. Returns frames
        consumed, or raises TimeoutError."""
        for elapsed in range(0, timeout, step):
            if predicate(self):
                return elapsed
            self.run(step)
        raise TimeoutError(f"condition not met within {timeout} frames")

    # --- state ------------------------------------------------------------

    def read_u8(self, addr):
        return self.wram[addr]

    def read_u16(self, addr):
        return self.wram[addr] | (self.wram[addr + 1] << 8)

    def write_u8(self, addr, value):
        self.wram[addr] = value & 0xff

    def write_u16(self, addr, value):
        self.wram[addr] = value & 0xff
        self.wram[addr + 1] = (value >> 8) & 0xff

    def save_state(self):
        size = self.lib.retro_serialize_size()
        buf = C.create_string_buffer(size)
        if not self.lib.retro_serialize(buf, size):
            raise RuntimeError("retro_serialize failed")
        return buf.raw

    def load_state(self, state):
        buf = C.create_string_buffer(state, len(state))
        if not self.lib.retro_unserialize(buf, len(state)):
            raise RuntimeError("retro_unserialize failed")

    # --- screenshots ------------------------------------------------------

    def screenshot(self, path):
        """Write the last rendered frame as a PNG (stdlib only)."""
        if self.frame is None:
            raise RuntimeError("no frame rendered yet")
        buf, width, height, pitch = self.frame
        rows = []
        if self._pixel_format == RETRO_PIXEL_FORMAT_RGB565:
            for y in range(height):
                row = bytearray()
                base = y * pitch
                for x in range(width):
                    px = buf[base + 2*x] | (buf[base + 2*x + 1] << 8)
                    r = (px >> 11) & 0x1f
                    g = (px >> 5) & 0x3f
                    b = px & 0x1f
                    row += bytes(((r << 3) | (r >> 2),
                                  (g << 2) | (g >> 4),
                                  (b << 3) | (b >> 2)))
                rows.append(bytes(row))
        elif self._pixel_format == RETRO_PIXEL_FORMAT_XRGB8888:
            for y in range(height):
                row = bytearray()
                base = y * pitch
                for x in range(width):
                    row += bytes((buf[base + 4*x + 2],
                                  buf[base + 4*x + 1],
                                  buf[base + 4*x + 0]))
                rows.append(bytes(row))
        else:  # 0RGB1555
            for y in range(height):
                row = bytearray()
                base = y * pitch
                for x in range(width):
                    px = buf[base + 2*x] | (buf[base + 2*x + 1] << 8)
                    r = (px >> 10) & 0x1f
                    g = (px >> 5) & 0x1f
                    b = px & 0x1f
                    row += bytes(((r << 3) | (r >> 2),
                                  (g << 3) | (g >> 2),
                                  (b << 3) | (b >> 2)))
                rows.append(bytes(row))
        _write_png(path, width, height, rows)
        return path


def _write_png(path, width, height, rgb_rows):
    def chunk(tag, data):
        return (struct.pack('>I', len(data)) + tag + data
                + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff))
    raw = b''.join(b'\x00' + row for row in rgb_rows)
    png = (b'\x89PNG\r\n\x1a\n'
           + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
           + chunk(b'IDAT', zlib.compress(raw, 6))
           + chunk(b'IEND', b''))
    with open(path, 'wb') as f:
        f.write(png)
