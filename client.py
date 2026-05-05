import socket
import threading
import tkinter as tk
from tkinter import ttk
from datetime import datetime

HOST = '127.0.0.1'
PORT = 12345

BG          = "#0B0F17"   # fundo principal
BG_PANEL    = "#111826"   # painel lateral
BG_CARD     = "#0F1623"   # área de chat
BG_INPUT    = "#1A2333"   # inputs
BORDER      = "#1F2A3D"
TEXT        = "#E6EDF7"
TEXT_DIM    = "#7C8AA3"
ACCENT      = "#00E0B8"   # verde-ciano neon
ACCENT_DARK = "#00B894"
DANGER      = "#FF5C7A"
INFO        = "#5AA9FF"
WARN        = "#FFB347"

FONT_UI     = ("SF Pro Display", 11)
FONT_UI_B   = ("SF Pro Display", 11, "bold")
FONT_TITLE  = ("SF Pro Display", 14, "bold")
FONT_CHAT   = ("JetBrains Mono", 11)
FONT_SMALL  = ("SF Pro Display", 9)


class ModernEntry(tk.Entry):
    def __init__(self, master, placeholder="", **kw):
        super().__init__(
            master,
            bg=BG_INPUT, fg=TEXT, insertbackground=ACCENT,
            relief="flat", bd=0, font=FONT_UI,
            highlightthickness=1,
            highlightbackground=BORDER,
            highlightcolor=ACCENT,
            **kw,
        )
        self._placeholder = placeholder
        self._has_placeholder = False
        if placeholder:
            self._show_placeholder()
            self.bind("<FocusIn>", self._clear_placeholder)
            self.bind("<FocusOut>", self._restore_placeholder)

    def _show_placeholder(self):
        self.insert(0, self._placeholder)
        self.config(fg=TEXT_DIM)
        self._has_placeholder = True

    def _clear_placeholder(self, _=None):
        if self._has_placeholder:
            self.delete(0, tk.END)
            self.config(fg=TEXT)
            self._has_placeholder = False

    def _restore_placeholder(self, _=None):
        if not self.get():
            self._show_placeholder()

    def real_get(self):
        return "" if self._has_placeholder else self.get()


class ModernButton(tk.Canvas):
    def __init__(self, master, text, command=None,
                 bg=ACCENT, fg="#08110D", hover=ACCENT_DARK,
                 width=120, height=36, **kw):
        super().__init__(master, width=width, height=height,
                         bg=master["bg"], highlightthickness=0, bd=0, **kw)
        self.command = command
        self._bg, self._fg, self._hover = bg, fg, hover
        self._bw, self._bh = width, height
        self._draw(bg)
        self._tid = self.create_text(width // 2, height // 2,
                                     text=text, fill=fg, font=FONT_UI_B)
        self.bind("<Enter>", lambda e: self._draw(self._hover))
        self.bind("<Leave>", lambda e: self._draw(self._bg))
        self.bind("<Button-1>", lambda e: command and command())

    def _draw(self, color):
        self.delete("bg")
        r = 8
        w, h = self._bw, self._bh
        # rounded rect
        self.create_arc((0, 0, 2*r, 2*r), start=90, extent=90, fill=color, outline=color, tags="bg")
        self.create_arc((w-2*r, 0, w, 2*r), start=0, extent=90, fill=color, outline=color, tags="bg")
        self.create_arc((0, h-2*r, 2*r, h), start=180, extent=90, fill=color, outline=color, tags="bg")
        self.create_arc((w-2*r, h-2*r, w, h), start=270, extent=90, fill=color, outline=color, tags="bg")
        self.create_rectangle((r, 0, w-r, h), fill=color, outline=color, tags="bg")
        self.create_rectangle((0, r, w, h-r), fill=color, outline=color, tags="bg")
        if hasattr(self, "_tid"):
            self.tag_raise(self._tid)


def ask_name():
    """Diálogo modernizado para entrada do nome."""
    dlg = tk.Tk()
    dlg.title("Conectar")
    dlg.configure(bg=BG)
    dlg.geometry("380x260")
    dlg.resizable(False, False)

    # Centralizar
    dlg.update_idletasks()
    x = (dlg.winfo_screenwidth() // 2) - 190
    y = (dlg.winfo_screenheight() // 2) - 130
    dlg.geometry(f"+{x}+{y}")

    result = {"name": None}

    header = tk.Frame(dlg, bg=BG)
    header.pack(pady=(28, 6))
    tk.Label(header, text="◆", fg=ACCENT, bg=BG,
             font=("SF Pro Display", 22, "bold")).pack()
    tk.Label(dlg, text="NEXUS CHAT", fg=TEXT, bg=BG,
             font=("SF Pro Display", 16, "bold")).pack()
    tk.Label(dlg, text="secure socket terminal", fg=TEXT_DIM, bg=BG,
             font=FONT_SMALL).pack(pady=(0, 18))

    entry = ModernEntry(dlg, placeholder="seu nome de usuário")
    entry.pack(padx=40, fill="x", ipady=8)
    entry.focus_set()

    def submit(_=None):
        v = entry.real_get().strip()
        if v:
            result["name"] = v
            dlg.destroy()

    entry.bind("<Return>", submit)

    btn = ModernButton(dlg, "CONECTAR", command=submit, width=300, height=40)
    btn.pack(pady=18)

    dlg.protocol("WM_DELETE_WINDOW", dlg.destroy)
    dlg.mainloop()
    return result["name"]


class ChatClient:
    def __init__(self, host, port):
        self.name = ask_name()
        if not self.name:
            return

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((host, port))
        self.client_socket.send(self.name.encode('utf-8'))

        self.root = tk.Tk()
        self.root.title(f"Nexus Chat — {self.name}")
        self.root.configure(bg=BG)
        self.root.geometry("900x600")
        self.root.minsize(720, 480)

        self._build_ui()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.running = True
        self.receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
        self.receive_thread.start()

        self._system_message(f"Conectado ao servidor {HOST}:{PORT}")

    # ---------- UI ----------
    def _build_ui(self):
        # Topbar
        topbar = tk.Frame(self.root, bg=BG_PANEL, height=56)
        topbar.pack(side="top", fill="x")
        topbar.pack_propagate(False)

        tk.Label(topbar, text="◆", fg=ACCENT, bg=BG_PANEL,
                 font=("SF Pro Display", 18, "bold")).pack(side="left", padx=(18, 8))
        tk.Label(topbar, text="NEXUS CHAT", fg=TEXT, bg=BG_PANEL,
                 font=FONT_TITLE).pack(side="left")

        self.status_dot = tk.Label(topbar, text="●", fg=ACCENT, bg=BG_PANEL,
                                   font=("SF Pro Display", 12))
        self.status_dot.pack(side="right", padx=(0, 16))
        tk.Label(topbar, text=f"online · {self.name}", fg=TEXT_DIM, bg=BG_PANEL,
                 font=FONT_SMALL).pack(side="right")

        # Linha divisória
        tk.Frame(self.root, bg=BORDER, height=1).pack(fill="x")

        # Container principal
        main = tk.Frame(self.root, bg=BG)
        main.pack(fill="both", expand=True)

        # Sidebar
        sidebar = tk.Frame(main, bg=BG_PANEL, width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="USUÁRIOS ONLINE", fg=TEXT_DIM, bg=BG_PANEL,
                 font=("SF Pro Display", 9, "bold")).pack(anchor="w", padx=18, pady=(18, 8))

        self.users_frame = tk.Frame(sidebar, bg=BG_PANEL)
        self.users_frame.pack(fill="both", expand=True, padx=10)

        # Botão desconectar no fim da sidebar
        btn_wrap = tk.Frame(sidebar, bg=BG_PANEL)
        btn_wrap.pack(side="bottom", fill="x", pady=14)
        ModernButton(btn_wrap, "DESCONECTAR", command=self.on_closing,
                     bg=DANGER, hover="#E04668", fg="#FFFFFF",
                     width=190, height=38).pack()

        # Área de chat
        chat_wrap = tk.Frame(main, bg=BG)
        chat_wrap.pack(side="left", fill="both", expand=True)

        # Cabeçalho do chat (destinatário)
        header = tk.Frame(chat_wrap, bg=BG, height=48)
        header.pack(fill="x", padx=20, pady=(14, 6))
        header.pack_propagate(False)

        tk.Label(header, text="Conversando com:", fg=TEXT_DIM, bg=BG,
                 font=FONT_SMALL).pack(side="left")

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Modern.TCombobox",
                        fieldbackground=BG_INPUT, background=BG_INPUT,
                        foreground=TEXT, arrowcolor=ACCENT,
                        bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER,
                        selectbackground=BG_INPUT, selectforeground=TEXT)
        self.root.option_add("*TCombobox*Listbox.background", BG_INPUT)
        self.root.option_add("*TCombobox*Listbox.foreground", TEXT)
        self.root.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
        self.root.option_add("*TCombobox*Listbox.selectForeground", "#08110D")
        self.root.option_add("*TCombobox*Listbox.font", FONT_UI)

        self.user_dropdown = ttk.Combobox(header, values=["Todos"],
                                          state="readonly", width=22,
                                          style="Modern.TCombobox", font=FONT_UI)
        self.user_dropdown.current(0)
        self.user_dropdown.pack(side="left", padx=10)

        # Caixa de mensagens
        chat_box = tk.Frame(chat_wrap, bg=BG_CARD,
                            highlightbackground=BORDER, highlightthickness=1)
        chat_box.pack(fill="both", expand=True, padx=20, pady=8)

        self.chat_area = tk.Text(chat_box, bg=BG_CARD, fg=TEXT,
                                 font=FONT_CHAT, relief="flat", bd=0,
                                 wrap="word", padx=14, pady=12,
                                 insertbackground=ACCENT,
                                 selectbackground=BG_INPUT)
        scrollbar = tk.Scrollbar(chat_box, command=self.chat_area.yview,
                                 bg=BG_CARD, troughcolor=BG_CARD,
                                 activebackground=ACCENT, bd=0,
                                 highlightthickness=0, width=8)
        self.chat_area.config(yscrollcommand=scrollbar.set, state="disabled")
        scrollbar.pack(side="right", fill="y")
        self.chat_area.pack(side="left", fill="both", expand=True)

        # Tags coloridas
        self.chat_area.tag_config("time",     foreground=TEXT_DIM)
        self.chat_area.tag_config("system",   foreground=INFO,   font=FONT_CHAT)
        self.chat_area.tag_config("you",      foreground=ACCENT, font=("JetBrains Mono", 11, "bold"))
        self.chat_area.tag_config("user",     foreground=WARN,   font=("JetBrains Mono", 11, "bold"))
        self.chat_area.tag_config("private",  foreground="#C792EA", font=("JetBrains Mono", 11, "italic"))
        self.chat_area.tag_config("text",     foreground=TEXT)

        # Barra de envio
        send_bar = tk.Frame(chat_wrap, bg=BG)
        send_bar.pack(fill="x", padx=20, pady=(6, 16))

        input_wrap = tk.Frame(send_bar, bg=BG_INPUT,
                              highlightbackground=BORDER, highlightthickness=1)
        input_wrap.pack(side="left", fill="x", expand=True, ipady=2)

        tk.Label(input_wrap, text=">", fg=ACCENT, bg=BG_INPUT,
                 font=("JetBrains Mono", 13, "bold")).pack(side="left", padx=(12, 4))

        self.message_entry = tk.Entry(input_wrap, bg=BG_INPUT, fg=TEXT,
                                      insertbackground=ACCENT, relief="flat", bd=0,
                                      font=FONT_CHAT)
        self.message_entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 8))
        self.message_entry.bind("<Return>", self.send_message)

        ModernButton(send_bar, "ENVIAR", command=self.send_message,
                     width=110, height=40).pack(side="left", padx=(10, 0))

    # ---------- Sidebar de usuários ----------
    def _render_users(self, users):
        for w in self.users_frame.winfo_children():
            w.destroy()

        for u in users:
            row = tk.Frame(self.users_frame, bg=BG_PANEL)
            row.pack(fill="x", pady=2)

            color = ACCENT if u == "Todos" else (INFO if u == "(você)" else TEXT)
            icon = "◆" if u == "Todos" else "●"
            tk.Label(row, text=icon, fg=color, bg=BG_PANEL,
                     font=("SF Pro Display", 10)).pack(side="left", padx=(8, 8))
            tk.Label(row, text=u, fg=TEXT, bg=BG_PANEL,
                     font=FONT_UI).pack(side="left")

    # ---------- Mensagens ----------
    def _timestamp(self):
        return datetime.now().strftime("%H:%M")

    def _append(self, segments):
        """segments: lista de (texto, tag)"""
        self.chat_area.config(state="normal")
        for text, tag in segments:
            self.chat_area.insert(tk.END, text, tag)
        self.chat_area.insert(tk.END, "\n")
        self.chat_area.config(state="disabled")
        self.chat_area.yview(tk.END)

    def _system_message(self, msg):
        self._append([
            (f"[{self._timestamp()}] ", "time"),
            ("• ", "system"),
            (msg, "system"),
        ])

    def _format_incoming(self, message):
        # Mensagens privadas
        if message.startswith("[Privado de "):
            self._append([
                (f"[{self._timestamp()}] ", "time"),
                (message, "private"),
            ])
            return

        # Mensagens de sistema (entrou/saiu)
        if message.endswith("entrou no chat.") or message.endswith("saiu do chat.") \
           or message.startswith("Sua conexão"):
            self._system_message(message)
            return

        # "nome: texto"
        if ": " in message:
            sender, body = message.split(": ", 1)
            self._append([
                (f"[{self._timestamp()}] ", "time"),
                (f"{sender} ", "user"),
                ("» ", "time"),
                (body, "text"),
            ])
        else:
            self._append([
                (f"[{self._timestamp()}] ", "time"),
                (message, "text"),
            ])

    def send_message(self, event=None):
        message = self.message_entry.get().strip()
        if not message:
            return
        self.message_entry.delete(0, tk.END)

        recipient = self.user_dropdown.get()
        if recipient == "Todos":
            self.client_socket.send(f"ALL:{message}".encode('utf-8'))
            self._append([
                (f"[{self._timestamp()}] ", "time"),
                ("você ", "you"),
                ("» ", "time"),
                (message, "text"),
            ])
        elif recipient != "(você)":
            self.client_socket.send(f"UNICAST:{recipient}:{message}".encode('utf-8'))
            self._append([
                (f"[{self._timestamp()}] ", "time"),
                (f"você → {recipient}: ", "you"),
                (message, "private"),
            ])

    def receive_messages(self):
        while self.running:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                if not message:
                    break
                if message.startswith("USERS:"):
                    raw = message[6:].split(",")
                    users = ["Todos"] + ["(você)" if u == self.name else u for u in raw if u]
                    self.user_dropdown["values"] = users
                    self._render_users(users)
                else:
                    self._format_incoming(message)
            except OSError:
                break

    def on_closing(self):
        self.running = False
        try:
            self.client_socket.send(f"DISCONNECT:{self.name}".encode('utf-8'))
            self.client_socket.close()
        except OSError:
            pass
        try:
            self.root.quit()
            self.root.destroy()
        except tk.TclError:
            pass


if __name__ == "__main__":
    client = ChatClient(HOST, PORT)
    if hasattr(client, "root"):
        client.root.mainloop()
