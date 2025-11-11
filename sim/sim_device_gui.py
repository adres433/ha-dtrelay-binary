\
#!/usr/bin/env python3
\"\"\"Improved GUI simulator for Dingtian DT-Relay devices with numbered IO, colors, message counter, themes and proxy option.\"\"\"

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading, socket, time, random, argparse, queue, sys
from binascii import hexlify

DEFAULT_PORT = 60000

LANG_STRINGS = {
    'en': {
        'title': "DTRelay Simulator (GUI)",
        'start': "Start",
        'stop': "Stop",
        'protocol': "Protocol",
        'udp': "UDP",
        'tcp': "TCP",
        'channels': "Channels",
        'port': "Port",
        'lang': "Language",
        'theme': "Theme",
        'light': "Light",
        'dark': "Dark",
        'mode': "Mode",
        'simulate': "simulate",
        'proxy': "proxy",
        'both': "both",
        'auto_inputs': "Auto inputs",
        'log': "Log",
        'address': "Real device IP",
        'messages': "Messages",
    },
    'pl': {
        'title': "Symulator DTRelay (GUI)",
        'start': "Uruchom",
        'stop': "Zatrzymaj",
        'protocol': "Protokół",
        'udp': "UDP",
        'tcp': "TCP",
        'channels': "Kanały",
        'port': "Port",
        'lang': "Język",
        'theme': "Motyw",
        'light': "Jasny",
        'dark': "Ciemny",
        'mode': "Tryb",
        'simulate': "symulacja",
        'proxy': "proxy",
        'both': "oba",
        'auto_inputs': "Auto wejścia",
        'log': "Dziennik",
        'address': "IP urządzenia",
        'messages': "Wiadomości",
    }
}

class SimulatorCore(threading.Thread):
    def __init__(self, mode='UDP', port=DEFAULT_PORT, channels=16, lang='en', auto_inputs=True, real_ip=None, run_mode='simulate', ui_queue=None):
        super().__init__(daemon=True)
        self.mode = mode.upper()
        self.port = int(port)
        self.channels = channels
        self.lang = lang
        self.auto_inputs = auto_inputs
        self.real_ip = real_ip
        self.run_mode = run_mode  # simulate, proxy, both
        self.ui_queue = ui_queue or queue.Queue()
        self._stop = threading.Event()
        self.outputs = [False]*self.channels
        self.inputs = [False]*self.channels
        self.msg_count = 0
        self._lock = threading.Lock()
        self.sock = None
        self.tcp_server = None

    def log(self, msg):
        try:
            self.ui_queue.put(msg)
        except Exception:
            pass

    def stop(self):
        self._stop.set()
        try:
            if self.sock:
                self.sock.close()
        except Exception:
            pass
        try:
            if self.tcp_server:
                self.tcp_server.close()
        except Exception:
            pass

    def _build_find_response(self):
        payload = bytearray(34)
        payload[0] = 0x05
        sn = random.randint(100000,999999)
        payload[2:6] = (sn).to_bytes(4, 'little')
        payload[14:18] = (self.channels).to_bytes(4, 'little')
        try:
            ip_u = int.from_bytes(socket.inet_aton(socket.gethostbyname(socket.gethostname())), 'little')
            payload[18:22] = ip_u.to_bytes(4, 'little')
        except Exception:
            pass
        return bytes(payload)

    def _build_status_text(self):
        out_str = ''.join('1' if v else '0' for v in self.outputs)
        in_str = ''.join('1' if v else '0' for v in self.inputs)
        return f"{out_str}:{in_str}:{self.channels}"

    def _handle_write_text(self, text):
        parts = text.strip().split(':')
        if len(parts) >= 2:
            mask = parts[0].zfill(self.channels)[:self.channels]
            setb = parts[1].zfill(self.channels)[:self.channels]
            for i in range(self.channels):
                if mask[i] == '1':
                    self.outputs[i] = (setb[i] == '1')
            self.log(f"Applied textual write -> outputs now: {''.join('1' if v else '0' for v in self.outputs)}")
            return True
        return False

    def _handle_binary_frame(self, data, addr=None, sock=None):
        if not data:
            return
        b0 = data[0] if len(data)>0 else None
        if b0 == 0x05:
            resp = self._build_find_response()
            self.log(f"Received FIND probe from {addr}; replying ({len(resp)} bytes)")
            if self.mode == 'UDP' and sock:
                try:
                    sock.sendto(resp, addr)
                except Exception as e:
                    self.log(f"Send find resp failed: {e}")
            return
        if len(data) >= 6:
            relay_cmd = data[3]
            if relay_cmd == 0:
                txt = self._build_status_text().encode('utf-8')
                self.log(f"Received READ STATUS from {addr}; replying text status")
                if self.mode == 'UDP' and sock:
                    try:
                        sock.sendto(txt, addr)
                    except Exception as e:
                        self.log(f"Send status failed: {e}")
                return
            if relay_cmd == 1:
                payload = data[6:]
                half = len(payload)//2
                set_bytes = payload[half:half*2]
                bits = []
                for byte in set_bytes:
                    for bit in range(8):
                        bits.append(((byte >> bit) & 1) == 1)
                for i in range(min(self.channels, len(bits))):
                    self.outputs[i] = bits[i]
                self.log(f"Received WRITE RELAY from {addr}; outputs updated")
                return

    def run(self):
        if self.mode == 'UDP':
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            except Exception:
                pass
            self.sock.bind(('', self.port))
            self.sock.settimeout(0.5)
            self.log(f"UDP listener started on port {self.port}")
        else:
            self.tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.tcp_server.bind(('', self.port))
            self.tcp_server.listen(1)
            self.tcp_server.settimeout(0.5)
            self.log(f"TCP server listening on port {self.port}")

        last_auto = time.time()
        while not self._stop.is_set():
            try:
                if self.mode == 'UDP' and self.sock:
                    try:
                        data, addr = self.sock.recvfrom(4096)
                    except socket.timeout:
                        data = None
                        addr = None
                    if data:
                        with self._lock:
                            self.msg_count += 1
                        try:
                            text = data.decode('utf-8', errors='ignore')
                            if ':' in text:
                                self.log(f"UDP Text from {addr}: {text.strip()}")
                                if self.run_mode in ('proxy','both') and self.real_ip:
                                    try:
                                        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                                        s.sendto(data, (self.real_ip, self.port))
                                        s.close()
                                        self.log(f"Forwarded packet to real device {self.real_ip}:{self.port}")
                                    except Exception as e:
                                        self.log(f"Proxy forward failed: {e}")
                                else:
                                    self._handle_write_text(text)
                                    resp = self._build_status_text().encode('utf-8')
                                    try:
                                        self.sock.sendto(resp, addr)
                                    except Exception as e:
                                        self.log(f"Send status failed: {e}")
                                continue
                        except Exception:
                            pass
                        self.log(f"UDP Binary from {addr}: {hexlify(data)}")
                        if self.run_mode in ('proxy','both') and self.real_ip:
                            try:
                                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                                s.sendto(data, (self.real_ip, self.port))
                                s.close()
                                self.log(f"Forwarded binary to real device {self.real_ip}:{self.port}")
                            except Exception as e:
                                self.log(f"Proxy forward failed: {e}")
                        else:
                            self._handle_binary_frame(data, addr, self.sock)
                elif self.mode == 'TCP' and self.tcp_server:
                    try:
                        conn, addr = self.tcp_server.accept()
                        conn.settimeout(0.5)
                        self.log(f"TCP client connected: {addr}")
                        while True:
                            try:
                                data = conn.recv(4096)
                                if not data:
                                    break
                                with self._lock:
                                    self.msg_count += 1
                                self.log(f"TCP data from {addr}: {hexlify(data)}")
                                self._handle_binary_frame(data, addr, conn)
                                try:
                                    text = data.decode('utf-8', errors='ignore')
                                    if ':' in text:
                                        self._handle_write_text(text)
                                except Exception:
                                    pass
                            except socket.timeout:
                                continue
                        conn.close()
                    except socket.timeout:
                        pass
                if self.auto_inputs and (time.time() - last_auto) > random.uniform(2.0,5.0):
                    i = random.randrange(0, self.channels)
                    self.inputs[i] = not self.inputs[i]
                    last_auto = time.time()
                    self.log(f"Auto toggled input I{i+1} -> {self.inputs[i]}")
                time.sleep(0.01)
            except Exception as e:
                self.log(f"Main loop exception: {e}")
                time.sleep(0.5)
        try:
            if self.sock:
                self.sock.close()
            if self.tcp_server:
                self.tcp_server.close()
        except Exception:
            pass
        self.log("Simulator stopped")

class SimulatorGUI:
    def __init__(self, root, default_lang='en'):
        self.root = root
        self.lang = default_lang if default_lang in LANG_STRINGS else 'en'
        self.strings = LANG_STRINGS[self.lang]
        root.title(self.strings['title'])
        self.ui_queue = queue.Queue()
        # top frame
        top = ttk.Frame(root, padding=8)
        top.grid(row=0, column=0, sticky='ew')
        ttk.Label(top, text=self._s('protocol')).grid(row=0, column=0, padx=4)
        self.protocol_var = tk.StringVar(value='UDP')
        proto = ttk.Combobox(top, textvariable=self.protocol_var, values=['UDP','TCP'], width=6, state='readonly')
        proto.grid(row=0, column=1, padx=4)
        ttk.Label(top, text=self._s('channels')).grid(row=0, column=2, padx=4)
        self.channels_var = tk.IntVar(value=16)
        ch = ttk.Combobox(top, textvariable=self.channels_var, values=[2,4,8,16,32], width=5, state='readonly')
        ch.grid(row=0, column=3, padx=4)
        ttk.Label(top, text=self._s('port')).grid(row=0, column=4, padx=4)
        self.port_var = tk.IntVar(value=60000)
        ttk.Entry(top, textvariable=self.port_var, width=6).grid(row=0, column=5, padx=4)
        ttk.Label(top, text=self._s('mode')).grid(row=0, column=6, padx=4)
        self.mode_var = tk.StringVar(value='simulate')
        ttk.Combobox(top, textvariable=self.mode_var, values=['simulate','proxy','both'], width=10, state='readonly').grid(row=0, column=7, padx=4)
        ttk.Label(top, text=self._s('address')).grid(row=0, column=8, padx=4)
        self.real_ip_var = tk.StringVar(value='')
        ttk.Entry(top, textvariable=self.real_ip_var, width=12).grid(row=0, column=9, padx=4)
        ttk.Label(top, text=self._s('lang')).grid(row=1, column=0, padx=4)
        self.lang_var = tk.StringVar(value=self.lang)
        ttk.Combobox(top, textvariable=self.lang_var, values=['en','pl'], width=6, state='readonly').grid(row=1, column=1, padx=4)
        ttk.Label(top, text=self._s('theme')).grid(row=1, column=2, padx=4)
        self.theme_var = tk.StringVar(value='light')
        ttk.Combobox(top, textvariable=self.theme_var, values=['light','dark'], width=6, state='readonly').grid(row=1, column=3, padx=4)
        self.auto_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(top, text=self._s('auto_inputs'), variable=self.auto_var).grid(row=1, column=4, padx=4)
        self.start_btn = ttk.Button(top, text=self._s('start'), command=self.start_sim)
        self.start_btn.grid(row=1, column=7, padx=4)
        self.stop_btn = ttk.Button(top, text=self._s('stop'), command=self.stop_sim, state='disabled')
        self.stop_btn.grid(row=1, column=8, padx=4)
        # center frame: IO
        center = ttk.Frame(root, padding=8)
        center.grid(row=1, column=0)
        self.io_frame = ttk.Frame(center)
        self.io_frame.grid(row=0, column=0)
        self.leds = []
        self.buttons = []
        # status label
        self.status_var = tk.StringVar(value='')
        ttk.Label(root, textvariable=self.status_var).grid(row=3, column=0, sticky='w', padx=8)
        # log area
        log_frame = ttk.Frame(root, padding=8)
        log_frame.grid(row=2, column=0, sticky='ew')
        ttk.Label(log_frame, text=self._s('log')).grid(row=0, column=0, sticky='w')
        self.log_widget = scrolledtext.ScrolledText(log_frame, height=10, width=120, state='disabled')
        self.log_widget.grid(row=1, column=0)
        self.sim = None
        self.root.after(200, self._ui_poll)

    def _s(self, key):
        return LANG_STRINGS[self.lang].get(key, key)

    def start_sim(self):
        if self.sim:
            return
        prot = self.protocol_var.get()
        ch = self.channels_var.get()
        port = self.port_var.get()
        mode = self.mode_var.get()
        real_ip = self.real_ip_var.get().strip() or None
        auto = self.auto_var.get()
        lang = self.lang_var.get()
        theme = self.theme_var.get()
        self.lang = lang
        self.strings = LANG_STRINGS[self.lang]
        for widget in self.io_frame.winfo_children():
            widget.destroy()
        self.leds = []
        self.buttons = []
        cols = 8
        for i in range(ch):
            r = i // cols
            c = i % cols
            led = tk.Label(self.io_frame, text=f"I{i+1}:0", relief='sunken', width=8, bg='lightgrey')
            led.grid(row=r*2, column=c, padx=2, pady=2)
            btn = tk.Button(self.io_frame, text=f"Q{i+1}:0", width=10, command=lambda idx=i: self._toggle_output(idx), bg='#f0f0f0')
            btn.grid(row=r*2+1, column=c, padx=2, pady=2)
            self.leds.append(led)
            self.buttons.append(btn)
        # create and start simulator core
        self.sim = SimulatorCore(mode=prot, port=port, channels=ch, lang=lang, auto_inputs=auto, real_ip=real_ip, run_mode=mode, ui_queue=self.log_queue())
        self.sim.start()
        # apply theme
        if theme == 'dark':
            for led in self.leds:
                led.config(bg='#444', fg='white')
            for btn in self.buttons:
                btn.config(bg='#222', fg='white')
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.log(f"Simulator started ({prot} port={port} ch={ch} mode={mode}) Theme={theme} Lang={lang}")

    def stop_sim(self):
        if not self.sim:
            return
        self.sim.stop()
        self.sim = None
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.log("Simulator stopped")

    def log_queue(self):
        def put(msg):
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            self.ui_queue.put(f"[{timestamp}] {msg}")
        return put

    def _ui_poll(self):
        try:
            while not self.ui_queue.empty():
                msg = self.ui_queue.get_nowait()
                self.log(msg)
        except Exception:
            pass
        if self.sim:
            try:
                cnt = getattr(self.sim, 'msg_count', 0)
                self.status_var.set(f\"{self._s('messages')}: {cnt}\")
            except Exception:
                pass
            for i, led in enumerate(self.leds):
                try:
                    state = self.sim.inputs[i]
                    led.config(text=f\"I{i+1}:{'1' if state else '0'}\")
                    led.config(bg='green' if state else ('#444' if self.theme_var.get()=='dark' else 'lightgrey'))
                except Exception:
                    pass
            for i, btn in enumerate(self.buttons):
                try:
                    state = self.sim.outputs[i]
                    btn.config(text=f\"Q{i+1}:{'1' if state else '0'}\")
                    btn.config(bg='#ff9900' if state else ('#222' if self.theme_var.get()=='dark' else '#f0f0f0'))
                except Exception:
                    pass
        self.root.after(200, self._ui_poll)

    def _toggle_output(self, idx):
        if not self.sim:
            return
        self.sim.outputs[idx] = not self.sim.outputs[idx]
        self.sim.log(f"Manually toggled output Q{idx+1} -> {self.sim.outputs[idx]}")
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            msg = self.sim._build_status_text().encode('utf-8')
            s.sendto(msg, ('127.0.0.1', self.sim.port))
            s.close()
        except Exception as e:
            self.sim.log(f"Send status failed: {e}")

    def log(self, msg):
        self.log_widget.config(state='normal')
        self.log_widget.insert('end', msg + "\n")
        self.log_widget.see('end')
        self.log_widget.config(state='disabled')

def main():
    parser = argparse.ArgumentParser(description="DTRelay GUI Simulator")
    parser.add_argument('--lang', default='en', choices=['en','pl'])
    parser.add_argument('--mode', default='udp', choices=['udp','tcp'])
    parser.add_argument('--channels', default=16, type=int, choices=[2,4,8,16,32])
    parser.add_argument('--port', default=60000, type=int)
    parser.add_argument('--proxy_ip', default='', help='Real device IP for proxying')
    args = parser.parse_args()

    root = tk.Tk()
    gui = SimulatorGUI(root, default_lang=args.lang)
    gui.protocol_var.set(args.mode.upper())
    gui.channels_var.set(args.channels)
    gui.port_var.set(args.port)
    if args.proxy_ip:
        gui.real_ip_var.set(args.proxy_ip)
    root.mainloop()

if __name__ == '__main__':
    main()
