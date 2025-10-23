import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import socket
import requests
import json
import os
import sys
import datetime
from tkinter import font as tkfont
from PIL import Image, ImageTk
import importlib.resources as pkg_resources
from importlib.resources import files

class RelayTesterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Controlador de Catracas")
        self.root.geometry("300x200+{}+0".format(root.winfo_screenwidth() - 300))  # Janela menor
        
        # Configurações do usuário master
        self.MASTER_USER = {
            'login': 'admin',
            'password': 'CardTec3363',
            'hidden': True
        }
        
        # Configurar ícone da aplicação
        self.set_window_icon(self.root)
        
        # Variáveis para controle de janelas
        self.config_window = None
        self.users_window = None
        self.login_window = None
        self.help_window = None
        
        # Configurações
        self.current_ip = tk.StringVar(value="192.168.1.100")
        self.port = tk.StringVar(value="80")
        self.protocol = tk.StringVar(value="HTTP")
        self.password = tk.StringVar(value="0")
        self.image_state = True
        self.relay_devices = []
        self.areas = {}  # Dicionário para armazenar áreas
        
        # Caminhos para arquivos embutidos
        self.config_file = self.get_data_path("config.txt")
        self.areas_file = self.get_data_path("areas.txt")
        self.passwords_file = self.get_data_path("senha.txt")
        self.log_file = self.get_data_path("log.txt")
        
        # Verificar e criar diretório de dados se necessário
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        
        self.load_config()
        self.load_areas()
        
        # Cores disponíveis para áreas (nomes em português)
        self.available_colors = {
            'Vermelho': '#FF0000',
            'Verde': '#4CAF50', 
            'Laranja': '#FF6B35',
            'Turquesa': '#4ECDC4',
            'Azul Claro': '#45B7D1',
            'Verde Claro': '#96CEB4',
            'Amarelo': '#F7DC6F',
            'Roxo': '#9B59B6',
            'Rosa': '#E91E63',
            'Cinza': '#95A5A6',
            'Marrom': '#8B4513',
            'Azul Marinho': '#2C3E50'
        }
        
        # Cores para botões específicos
        self.button_colors = {
            'emergency': '#FF0000',  # Vermelho para Geral
            'config': '#4CAF50',     # Verde
            'active': '#FF4500',     # Laranja mais escuro
            'success': '#4BB543'     # Verde sucesso
        }
        # Adicionar cores disponíveis ao button_colors
        self.button_colors.update(self.available_colors)
        
        # Carregar senhas
        self.passwords = self.load_passwords()
        
        # Criar widgets
        self.create_main_screen()
        
        # Fonte
        self.message_font = tkfont.Font(size=10, weight='bold')
    
    def get_data_path(self, filename):
        """Obtém o caminho para arquivos de dados (configuração, senhas, logs)"""
        if getattr(sys, 'frozen', False):
            # Se estamos rodando como executável
            base_path = os.path.dirname(sys.executable)
        else:
            # Se estamos rodando como script
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        # Para arquivos de dados (config, senhas, logs), usamos uma subpasta 'data'
        data_dir = os.path.join(base_path, 'data')
        return os.path.join(data_dir, filename)
    
    def resource_path(self, relative_path):
        """Obtém o caminho absoluto para recursos embutidos (imagens)"""
        if getattr(sys, 'frozen', False):
            # Se estamos rodando como executável
            base_path = sys._MEIPASS
        else:
            # Se estamos rodando como script
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        return os.path.join(base_path, relative_path)
    
    def set_window_icon(self, window):
        """Configura o ícone da janela usando logino.png"""
        try:
            icon_path = self.resource_path("loginho.png")
            if os.path.exists(icon_path):
                img = Image.open(icon_path)
                img = img.resize((32, 32), Image.Resampling.LANCZOS)
                icon = ImageTk.PhotoImage(img)
                window.tk.call('wm', 'iconphoto', window._w, icon)
                # Manter referência para evitar garbage collection
                if window == self.root:
                    self.root_icon = icon
                elif window == self.config_window:
                    self.config_icon = icon
                elif window == self.users_window:
                    self.users_icon = icon
                elif window == self.login_window:
                    self.login_icon = icon
                elif window == self.help_window:
                    self.help_icon = icon
        except Exception as e:
            print(f"Não foi possível carregar o ícone: {str(e)}")
    
    def load_config(self):
        """Carrega as configurações salvas no arquivo config.txt"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    data = f.read()
                    if data:
                        self.relay_devices = json.loads(data)
                        if self.relay_devices:
                            self.current_ip.set(self.relay_devices[0]['ip'])
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar configurações: {str(e)}")
            self.relay_devices = []
    
    def load_areas(self):
        """Carrega as áreas salvas no arquivo areas.txt"""
        try:
            if os.path.exists(self.areas_file):
                with open(self.areas_file, "r") as f:
                    data = f.read()
                    if data:
                        self.areas = json.loads(data)
            else:
                # Áreas iniciais vazias - o usuário cadastra as áreas que quiser
                self.areas = {}
                self.save_areas()
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar áreas: {str(e)}")
            self.areas = {}
    
    def save_config(self):
        """Salva as configurações no arquivo config.txt"""
        try:
            with open(self.config_file, "w") as f:
                f.write(json.dumps(self.relay_devices))
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar configurações: {str(e)}")
    
    def save_areas(self):
        """Salva as áreas no arquivo areas.txt"""
        try:
            with open(self.areas_file, "w") as f:
                f.write(json.dumps(self.areas))
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar áreas: {str(e)}")
    
    def load_passwords(self):
        """Carrega as senhas do arquivo senha.txt"""
        passwords = {}
        try:
            if os.path.exists(self.passwords_file):
                with open(self.passwords_file, "r") as f:
                    for line in f:
                        if ":" in line:
                            user, pwd = line.strip().split(":")
                            passwords[user] = pwd
                
                # Se há exatamente 1 usuário cadastrado, adiciona o master
                if len(passwords) == 1:
                    passwords[self.MASTER_USER['login']] = self.MASTER_USER['password']
                    self.save_passwords(passwords)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar senhas: {str(e)}")
        
        return passwords
    
    def save_passwords(self, passwords=None):
        """Salva as senhas no arquivo senha.txt"""
        passwords = passwords or self.passwords
        
        # Remove o usuário master se for o único (além dele mesmo)
        if len(passwords) == 1 and self.MASTER_USER['login'] in passwords:
            passwords = {}
        
        try:
            with open(self.passwords_file, "w") as f:
                for user, pwd in passwords.items():
                    # Não salva o usuário master oculto
                    if user != self.MASTER_USER['login'] or pwd != self.MASTER_USER['password']:
                        f.write(f"{user}:{pwd}\n")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar senhas: {str(e)}")
        
        # Atualiza o dicionário interno
        self.passwords = passwords
        
        # Se há exatamente 1 usuário (não master), adiciona o master
        if len(self.passwords) == 1 and self.MASTER_USER['login'] not in self.passwords:
            self.passwords[self.MASTER_USER['login']] = self.MASTER_USER['password']
            # Não salva novamente para evitar loop
    
    def log_message(self, message):
        """Salva mensagem no arquivo de log"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        try:
            with open(self.log_file, "a", encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Erro ao salvar log: {str(e)}")
    
    def create_main_screen(self):
        """Cria a tela principal com botões de emergência por área"""
        # Frame principal
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)  # Menos padding
        
        # Menu (três risquinhos)
        menubar = tk.Menu(self.root)
        config_menu = tk.Menu(menubar, tearoff=0)
        config_menu.add_command(label="Relés", command=self.show_config_screen)
        config_menu.add_command(label="Áreas", command=self.show_areas_screen)
        config_menu.add_command(label="Usuários", command=self.show_users_screen)
        config_menu.add_command(label="Ajuda", command=self.show_help_screen)
        menubar.add_cascade(label="☰", menu=config_menu)
        self.root.config(menu=menubar)
        
        # Logo - ainda menor
        try:
            logo_path = self.resource_path("logo.png")
            self.logo_image = Image.open(logo_path)
            self.logo_image = self.logo_image.resize((120, 37), Image.Resampling.LANCZOS)  # Menor
            self.logo_photo = ImageTk.PhotoImage(self.logo_image)
            
            logo_label = ttk.Label(self.main_frame, image=self.logo_photo)
            logo_label.pack(pady=2)  # Menos padding
        except Exception as e:
            print(f"Não foi possível carregar a imagem logo.png: {str(e)}")
            ttk.Label(self.main_frame, text="Logo", font=('Helvetica', 8)).pack(pady=2)
        
        # Frame para botões das áreas
        self.buttons_frame = ttk.Frame(self.main_frame)
        self.buttons_frame.pack(fill=tk.BOTH, expand=True, pady=2)  # Menos padding
        
        # Criar botões para cada área
        self.create_area_buttons()
        
        # Label para mensagem de status (menor)
        self.status_label = ttk.Label(self.main_frame, text="", font=('Helvetica', 8))
        self.status_label.pack(pady=2)
        
        # Botão GERAL pequeno no canto inferior direito
        self.create_emergency_button()
    
    def create_emergency_button(self):
        """Cria o botão de emergência geral pequeno no canto inferior direito"""
        self.emergency_btn = tk.Button(
            self.root,
            text="GERAL",
            command=lambda: self.toggle_image_and_send_pulse_area('GERAL'),
            bg=self.button_colors['emergency'],
            fg="white",
            font=('Helvetica', 8, 'bold'),  # Fonte menor
            activebackground=self.button_colors['active'],
            relief=tk.RAISED,
            borderwidth=2,  # Borda mais fina
            width=6,        # Largura menor
            height=2,       # Altura menor
            compound=tk.CENTER
        )
        # Posicionar no canto inferior direito
        self.emergency_btn.place(relx=1.0, rely=1.0, anchor='se', x=-5, y=-5)
        self.emergency_btn.config(highlightthickness=0)
    
    def create_area_buttons(self):
        """Cria os botões para cada área (menores)"""
        # Limpar botões existentes
        for widget in self.buttons_frame.winfo_children():
            widget.destroy()
        
        if not self.areas:
            # Se não há áreas, mostrar mensagem
            ttk.Label(self.buttons_frame, text="Nenhuma área cadastrada", 
                     font=('Helvetica', 9), foreground='gray').pack(expand=True)
            return
        
        # Criar botões para cada área cadastrada pelo usuário
        row, col = 0, 0
        max_cols = 2  # Máximo de 2 colunas
        
        for area_name, area_data in self.areas.items():
            color_name = area_data['color']
            color = self.button_colors.get(color_name, self.button_colors['Vermelho'])
            
            btn = tk.Button(
                self.buttons_frame,
                text=area_name.upper(),  # Apenas o nome da área, sem "EMERGÊNCIA"
                command=lambda area=area_name: self.toggle_image_and_send_pulse_area(area),
                bg=color,
                fg="white",
                font=('Helvetica', 9, 'bold'),  # Fonte menor
                activebackground=self.button_colors['active'],
                relief=tk.RAISED,
                borderwidth=2,  # Borda mais fina
                width=12,       # Largura menor
                height=2,       # Altura menor
                compound=tk.CENTER,
                wraplength=100  # Wrap para nomes longos
            )
            btn.grid(row=row, column=col, padx=3, pady=3, sticky="nsew")  # Menos padding
            btn.config(highlightthickness=0)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        # Configurar grid para expandir
        for i in range(row + 1):
            self.buttons_frame.grid_rowconfigure(i, weight=1)
        for j in range(max_cols):
            self.buttons_frame.grid_columnconfigure(j, weight=1)
    
    def block_main_window(self):
        """Bloqueia a janela principal quando uma secundária está aberta"""
        if self.config_window or self.users_window or self.login_window or self.help_window:
            self.root.attributes('-disabled', True)
        else:
            self.root.attributes('-disabled', False)
    
    def block_other_windows(self, current_window):
        """Bloqueia outras janelas secundárias quando uma está aberta"""
        if self.config_window and self.config_window != current_window:
            self.config_window.destroy()
            self.config_window = None
        
        if self.users_window and self.users_window != current_window:
            self.users_window.destroy()
            self.users_window = None
        
        if self.login_window and self.login_window != current_window:
            self.login_window.destroy()
            self.login_window = None
        
        if self.help_window and self.help_window != current_window:
            self.help_window.destroy()
            self.help_window = None
        
        self.block_main_window()
    
    def show_config_screen(self):
        """Mostra a tela de configurações após verificar senha"""
        if not self.passwords or self.check_password("Configurações"):
            self.block_other_windows(None)
            
            if self.config_window is None or not self.config_window.winfo_exists():
                self.create_config_screen()
            else:
                self.config_window.lift()
    
    def show_areas_screen(self):
        """Mostra a tela de gerenciamento de áreas após verificar senha"""
        if not self.passwords or self.check_password("Áreas"):
            self.block_other_windows(None)
            
            if self.config_window is None or not self.config_window.winfo_exists():
                self.create_areas_screen()
            else:
                self.config_window.lift()
    
    def show_users_screen(self):
        """Mostra a tela de usuários após verificar senha"""
        if not self.passwords or self.check_password("Usuários"):
            self.block_other_windows(None)
            
            if self.users_window is None or not self.users_window.winfo_exists():
                self.create_users_screen()
            else:
                self.users_window.lift()
    
    def show_help_screen(self):
        """Mostra a tela de ajuda (não requer senha)"""
        self.block_other_windows(None)
        
        if self.help_window is None or not self.help_window.winfo_exists():
            self.create_help_screen()
        else:
            self.help_window.lift()
    
    def check_password(self, screen_name):
        """Verifica a senha para acessar telas protegidas"""
        # Janela personalizada para login - aumentada para evitar corte do botão
        self.login_window = tk.Toplevel(self.root)
        self.login_window.title(f"Acesso a {screen_name}")
        self.login_window.geometry("320x180")
        self.login_window.resizable(False, False)
        
        # Configurar ícone
        self.set_window_icon(self.login_window)
        
        # Bloquear outras janelas
        self.block_other_windows(self.login_window)
        
        # Centralizar janela
        window_width = 320
        window_height = 180
        screen_width = self.login_window.winfo_screenwidth()
        screen_height = self.login_window.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.login_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Frame principal para melhor organização
        main_frame = ttk.Frame(self.login_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="Usuário:").pack(pady=(5, 0))
        user_entry = ttk.Entry(main_frame)
        user_entry.pack(pady=5, fill=tk.X)
        
        ttk.Label(main_frame, text="Senha:").pack(pady=(5, 0))
        pwd_entry = ttk.Entry(main_frame, show="*")
        pwd_entry.pack(pady=5, fill=tk.X)
        
        # Configurar evento Enter para o campo de senha
        pwd_entry.bind('<Return>', lambda event: verify())
        
        result = {'authenticated': False}
        
        def verify():
            user = user_entry.get().strip()
            pwd = pwd_entry.get().strip()
            
            if user in self.passwords and self.passwords[user] == pwd:
                result['authenticated'] = True
                self.login_window.destroy()
                self.login_window = None
                self.block_main_window()
            else:
                messagebox.showerror("Acesso Negado", "Usuário ou senha incorretos!")
                user_entry.delete(0, tk.END)
                pwd_entry.delete(0, tk.END)
                user_entry.focus()
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=10, fill=tk.X)
        
        btn_entrar = ttk.Button(btn_frame, text="Entrar", command=verify)
        btn_entrar.pack(expand=True, ipadx=20)
        
        # Configurar comportamento ao fechar
        self.login_window.protocol("WM_DELETE_WINDOW", lambda: self.on_login_close(result))
        
        # Focar no campo de usuário e aguardar
        user_entry.focus()
        self.login_window.grab_set()
        self.login_window.wait_window()
        
        return result['authenticated']
    
    def on_login_close(self, result):
        """Lidar com o fechamento da janela de login"""
        result['authenticated'] = False
        self.login_window.destroy()
        self.login_window = None
        self.block_main_window()
    
    def create_config_screen(self):
        """Cria a tela de configurações"""
        self.config_window = tk.Toplevel(self.root)
        self.config_window.title("Configurações")
        self.config_window.geometry("750x600")
        
        # Configurar ícone da janela
        self.set_window_icon(self.config_window)
        
        # Bloquear outras janelas
        self.block_other_windows(self.config_window)
        
        # Centralizar janela
        window_width = 750
        window_height = 600
        screen_width = self.config_window.winfo_screenwidth()
        screen_height = self.config_window.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.config_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Notebook para abas
        notebook = ttk.Notebook(self.config_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Aba de dispositivos
        devices_tab = ttk.Frame(notebook)
        notebook.add(devices_tab, text="Dispositivos")
        
        # Frame para adicionar novo dispositivo
        add_frame = ttk.LabelFrame(devices_tab, text="Adicionar novo dispositivo", padding=10)
        add_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(add_frame, text="Nome:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.new_name = ttk.Entry(add_frame)
        self.new_name.grid(row=0, column=1, sticky=tk.EW, pady=2, padx=5)
        
        ttk.Label(add_frame, text="Endereço IP:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.new_ip = ttk.Entry(add_frame)
        self.new_ip.grid(row=1, column=1, sticky=tk.EW, pady=2, padx=5)
        
        # Área do dispositivo (apenas áreas cadastradas pelo usuário)
        available_areas = list(self.areas.keys())
        ttk.Label(add_frame, text="Área:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.new_area = ttk.Combobox(add_frame, values=available_areas)
        if available_areas:
            self.new_area.set(available_areas[0])  # Define a primeira área disponível como padrão
        self.new_area.grid(row=2, column=1, sticky=tk.EW, pady=2, padx=5)
        
        # Variável para controle da porta
        self.advanced_options = tk.BooleanVar(value=False)
        self.custom_port = tk.StringVar(value="80")
        
        # Frame para opções avançadas
        advanced_frame = ttk.Frame(add_frame)
        advanced_frame.grid(row=3, column=0, columnspan=2, sticky=tk.EW, pady=5)
        
        ttk.Checkbutton(
            advanced_frame, 
            text="Avançado", 
            variable=self.advanced_options,
            command=self.toggle_advanced_options
        ).pack(side=tk.LEFT, padx=5)
        
        # Frame para configuração de porta (inicialmente oculto)
        self.port_frame = ttk.Frame(add_frame)
        
        ttk.Label(self.port_frame, text="Porta:").grid(row=0, column=0, sticky=tk.W, padx=5)
        port_entry = ttk.Entry(self.port_frame, textvariable=self.custom_port, width=8)
        port_entry.grid(row=0, column=1, sticky=tk.W)
        
        ttk.Button(add_frame, text="Incluir Novo Relé", 
                 command=self.add_new_relay).grid(row=5, column=0, columnspan=2, pady=5)
        
        # Lista de dispositivos
        list_frame = ttk.LabelFrame(devices_tab, text="Dispositivos cadastrados", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        canvas = tk.Canvas(list_frame)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.update_relays_list()
        
        # Aba de teste
        test_tab = ttk.Frame(notebook)
        notebook.add(test_tab, text="Teste")
        
        # Botão de teste
        test_frame = ttk.Frame(test_tab)
        test_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(test_frame, text="Testar Conexão", 
                command=self.test_all_connections,
                bg=self.button_colors['config'],
                fg="white",
                font=('Helvetica', 10, 'bold'),
                activebackground="#20B220",
                relief=tk.RAISED,
                borderwidth=3).pack(pady=10, ipadx=10, ipady=5)
        
        # Área de log de teste
        test_log_frame = ttk.LabelFrame(test_tab, text="Log de Teste", padding=10)
        test_log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.result_text = tk.Text(test_log_frame, height=15, wrap=tk.WORD, state=tk.DISABLED)
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(self.result_text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.result_text.yview)
        
        # Nova aba de Log do Sistema
        log_tab = ttk.Frame(notebook)
        notebook.add(log_tab, text="Log do Sistema")
        
        # Frame para o log do sistema
        sys_log_frame = ttk.LabelFrame(log_tab, text="Log Completo do Sistema", padding=10)
        sys_log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.sys_log_text = tk.Text(sys_log_frame, height=25, wrap=tk.WORD, state=tk.DISABLED)
        self.sys_log_text.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(self.sys_log_text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.sys_log_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.sys_log_text.yview)
        
        # Botão para carregar o log
        btn_frame = ttk.Frame(log_tab)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(btn_frame, text="Atualizar Log", 
                 command=self.load_system_log).pack(pady=5)
        
        # Carregar log inicial
        self.load_system_log()
        
        # Configurar fechamento da janela
        self.config_window.protocol("WM_DELETE_WINDOW", self.on_config_close)
    
    def create_areas_screen(self):
        """Cria a tela de gerenciamento de áreas"""
        self.config_window = tk.Toplevel(self.root)
        self.config_window.title("Gerenciamento de Áreas")
        self.config_window.geometry("600x500")
        
        # Configurar ícone da janela
        self.set_window_icon(self.config_window)
        
        # Bloquear outras janelas
        self.block_other_windows(self.config_window)
        
        # Centralizar janela
        window_width = 600
        window_height = 500
        screen_width = self.config_window.winfo_screenwidth()
        screen_height = self.config_window.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.config_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Frame para adicionar nova área
        add_frame = ttk.LabelFrame(self.config_window, text="Adicionar Nova Área", padding=10)
        add_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(add_frame, text="Nome da Área:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.new_area_name = ttk.Entry(add_frame)
        self.new_area_name.grid(row=0, column=1, sticky=tk.EW, pady=2, padx=5)
        
        ttk.Label(add_frame, text="Cor:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.new_area_color = ttk.Combobox(add_frame, values=list(self.available_colors.keys()))
        self.new_area_color.set('Verde')  # Cor padrão
        self.new_area_color.grid(row=1, column=1, sticky=tk.EW, pady=2, padx=5)
        
        ttk.Button(add_frame, text="Adicionar Área", 
                 command=self.add_new_area).grid(row=2, column=0, columnspan=2, pady=5)
        
        # Lista de áreas (apenas áreas cadastradas pelo usuário)
        list_frame = ttk.LabelFrame(self.config_window, text="Áreas Cadastradas", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        canvas = tk.Canvas(list_frame)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        self.areas_scrollable_frame = ttk.Frame(canvas)
        
        self.areas_scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        
        canvas.create_window((0, 0), window=self.areas_scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.update_areas_list()
        
        # Configurar fechamento da janela
        self.config_window.protocol("WM_DELETE_WINDOW", self.on_config_close)
    
    def add_new_area(self):
        """Adiciona uma nova área"""
        area_name = self.new_area_name.get().strip()
        color = self.new_area_color.get().strip()
        
        if not area_name:
            messagebox.showwarning("Aviso", "Por favor, informe o nome da área.")
            return
        
        if area_name in self.areas:
            messagebox.showwarning("Aviso", "Já existe uma área com este nome.")
            return
        
        # Adicionar nova área
        self.areas[area_name] = {'color': color, 'devices': []}
        self.save_areas()
        self.update_areas_list()
        self.create_area_buttons()  # Atualizar botões na tela principal
        
        # Atualizar combobox de áreas na tela de configuração de dispositivos
        if hasattr(self, 'new_area'):
            available_areas = list(self.areas.keys())
            self.new_area['values'] = available_areas
            if available_areas:
                self.new_area.set(available_areas[0])
        
        self.new_area_name.delete(0, tk.END)
        self.append_message(f"Área '{area_name}' adicionada com sucesso!", "black")
    
    def update_areas_list(self):
        """Atualiza a lista de áreas na tela de configuração"""
        for widget in self.areas_scrollable_frame.winfo_children():
            widget.destroy()
        
        for i, (area_name, area_data) in enumerate(self.areas.items()):
            frame = ttk.LabelFrame(self.areas_scrollable_frame, text=area_name, padding=5)
            frame.pack(fill=tk.X, padx=5, pady=5)
            
            # Mostrar cor atual
            color_display = tk.Frame(frame, width=20, height=20, 
                                   bg=self.available_colors.get(area_data['color'], '#CCCCCC'))
            color_display.pack(side=tk.LEFT, padx=5)
            
            # Mostrar quantidade de dispositivos
            device_count = len([d for d in self.relay_devices if d.get('area') == area_name])
            ttk.Label(frame, text=f"Dispositivos: {device_count}").pack(side=tk.LEFT, padx=10)
            
            # Mostrar cor usada
            ttk.Label(frame, text=f"Cor: {area_data['color']}").pack(side=tk.LEFT, padx=10)
            
            btn_frame = ttk.Frame(frame)
            btn_frame.pack(side=tk.RIGHT, padx=5)
            
            ttk.Button(btn_frame, text="Remover", 
                      command=lambda an=area_name: self.remove_area(an)).pack(side=tk.RIGHT, padx=2)
    
    def remove_area(self, area_name):
        """Remove uma área"""
        # Verificar se há dispositivos nesta área
        devices_in_area = [d for d in self.relay_devices if d.get('area') == area_name]
        if devices_in_area:
            messagebox.showwarning("Aviso", 
                                f"Não é possível remover a área '{area_name}' porque existem {len(devices_in_area)} dispositivo(s) vinculado(s) a ela.\n"
                                f"Transfira os dispositivos para outra área antes de remover.")
            return
        
        if messagebox.askyesno("Confirmar", f"Remover a área '{area_name}'?"):
            del self.areas[area_name]
            self.save_areas()
            self.update_areas_list()
            self.create_area_buttons()  # Atualizar botões na tela principal
            
            # Atualizar combobox de áreas na tela de configuração de dispositivos
            if hasattr(self, 'new_area'):
                available_areas = list(self.areas.keys())
                self.new_area['values'] = available_areas
                if available_areas:
                    self.new_area.set(available_areas[0])
            
            self.append_message(f"Área '{area_name}' removida.", "black")
    
    def load_system_log(self):
        """Carrega o conteúdo do arquivo de log do sistema"""
        if hasattr(self, 'sys_log_text'):
            self.sys_log_text.config(state=tk.NORMAL)
            self.sys_log_text.delete(1.0, tk.END)
            
            try:
                if os.path.exists("log.txt"):
                    with open("log.txt", "r", encoding='utf-8') as f:
                        content = f.read()
                        self.sys_log_text.insert(tk.END, content)
                else:
                    self.sys_log_text.insert(tk.END, "Arquivo de log não encontrado.")
            except Exception as e:
                self.sys_log_text.insert(tk.END, f"Erro ao carregar log: {str(e)}")
            
            self.sys_log_text.config(state=tk.DISABLED)
            self.sys_log_text.see(tk.END)
    
    def create_help_screen(self):
        """Cria a tela de ajuda"""
        self.help_window = tk.Toplevel(self.root)
        self.help_window.title("Ajuda e Suporte")
        self.help_window.geometry("300x300")  # Mantém o tamanho original
        
        # Centraliza a janela
        self.help_window.update_idletasks()  # Atualiza os dados da janela
        width = self.help_window.winfo_width()
        height = self.help_window.winfo_height()
        x = (self.help_window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.help_window.winfo_screenheight() // 2) - (height // 2)
        self.help_window.geometry(f"+{x}+{y}")
        
        # Configurar ícone da janela
        self.set_window_icon(self.help_window)
        
        # Bloquear outras janelas
        self.block_other_windows(self.help_window)
        
        # Frame principal
        main_frame = ttk.Frame(self.help_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Logo
        try:
            logo_img = Image.open(self.resource_path("logo.png"))
            logo_img = logo_img.resize((200, 62), Image.Resampling.LANCZOS)
            self.help_logo = ImageTk.PhotoImage(logo_img)
            
            logo_label = ttk.Label(main_frame, image=self.help_logo)
            logo_label.pack(pady=(0, 20))
        except Exception as e:
            print(f"Não foi possível carregar a imagem logo.png: {str(e)}")
            ttk.Label(main_frame, text="Logo da Empresa", font=('Helvetica', 12)).pack(pady=(0, 20))
        
        # Informações de contato
        info_frame = ttk.LabelFrame(main_frame, text="Informações de Contato", padding=10)
        info_frame.pack(fill=tk.BOTH, expand=True)
        
        # E-mail
        ttk.Label(info_frame, text="E-mail de Suporte:", font=('Helvetica', 10, 'bold')).pack(pady=(5, 0))
        ttk.Label(info_frame, text="suporte@relovoux.com").pack(pady=(0, 10))
        
        # Telefone
        ttk.Label(info_frame, text="Telefone:", font=('Helvetica', 10, 'bold')).pack(pady=(5, 0))
        ttk.Label(info_frame, text="(41) 3051-4645\n(41) 3363-0324").pack(pady=(0, 10))
        
        # Botão de fechar
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(btn_frame, text="Fechar", command=self.on_help_close).pack()
        
        # Configurar fechamento da janela
        self.help_window.protocol("WM_DELETE_WINDOW", self.on_help_close)
    
    def on_help_close(self):
        """Lidar com o fechamento da janela de ajuda"""
        self.help_window.destroy()
        self.help_window = None
        self.block_main_window()
    
    def toggle_advanced_options(self):
        """Mostra/oculta as opções avançadas"""
        if self.advanced_options.get():
            self.port_frame.grid(row=4, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)
        else:
            self.port_frame.grid_forget()
    
    def create_users_screen(self):
        """Cria a tela de gerenciamento de usuários"""
        self.users_window = tk.Toplevel(self.root)
        self.users_window.title("Gerenciamento de Usuários")
        self.users_window.geometry("500x400")
        
        # Configurar ícone da janela
        self.set_window_icon(self.users_window)
        
        # Bloquear outras janelas
        self.block_other_windows(self.users_window)
        
        # Centralizar janela
        window_width = 500
        window_height = 400
        screen_width = self.users_window.winfo_screenwidth()
        screen_height = self.users_window.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.users_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Frame para adicionar novo usuário
        add_frame = ttk.LabelFrame(self.users_window, text="Adicionar/Modificar Usuário", padding=10)
        add_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(add_frame, text="Usuário:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.new_user = ttk.Entry(add_frame)
        self.new_user.grid(row=0, column=1, sticky=tk.EW, pady=2, padx=5)
        
        ttk.Label(add_frame, text="Senha:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.new_pwd = ttk.Entry(add_frame, show="*")
        self.new_pwd.grid(row=1, column=1, sticky=tk.EW, pady=2, padx=5)
        
        # Configurar evento Enter para o campo de senha
        self.new_pwd.bind('<Return>', lambda event: self.add_update_user())
        
        ttk.Button(add_frame, text="Adicionar/Atualizar", 
                 command=self.add_update_user).grid(row=2, column=0, columnspan=2, pady=5)
        
        # Lista de usuários
        list_frame = ttk.LabelFrame(self.users_window, text="Usuários Cadastrados", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        canvas = tk.Canvas(list_frame)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        self.users_scrollable_frame = ttk.Frame(canvas)
        
        self.users_scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        
        canvas.create_window((0, 0), window=self.users_scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.update_users_list()
        
        # Configurar fechamento da janela
        self.users_window.protocol("WM_DELETE_WINDOW", self.on_users_close)
    
    def add_update_user(self):
        """Adiciona ou atualiza um usuário"""
        user = self.new_user.get().strip()
        pwd = self.new_pwd.get().strip()
        
        if not user or not pwd:
            messagebox.showwarning("Aviso", "Por favor, preencha usuário e senha.")
            return
        
        self.passwords[user] = pwd
        self.save_passwords()
        self.update_users_list()
        
        self.new_user.delete(0, tk.END)
        self.new_pwd.delete(0, tk.END)
        
        self.append_message(f"Usuário '{user}' atualizado com sucesso!", "black")
    
    def update_users_list(self):
        """Atualiza a lista de usuários na tela de configuração"""
        for widget in self.users_scrollable_frame.winfo_children():
            widget.destroy()
        
        for i, (user, pwd) in enumerate(self.passwords.items()):
            # Não mostra o usuário master oculto
            if user == self.MASTER_USER['login'] and pwd == self.MASTER_USER['password']:
                continue
                
            frame = ttk.Frame(self.users_scrollable_frame)
            frame.pack(fill=tk.X, padx=5, pady=2)
            
            ttk.Label(frame, text=f"Usuário: {user}").pack(side=tk.LEFT, padx=5)
            
            ttk.Button(frame, text="Remover", 
                      command=lambda u=user: self.remove_user(u)).pack(side=tk.RIGHT, padx=5)
        
        self.users_scrollable_frame.columnconfigure(1, weight=1)
    
    def remove_user(self, user):
        """Remove um usuário da lista"""
        if messagebox.askyesno("Confirmar", f"Remover o usuário '{user}'?"):
            # Se for o último usuário (além do master), remove o master também
            if len(self.passwords) == 2 and self.MASTER_USER['login'] in self.passwords:
                del self.passwords[self.MASTER_USER['login']]
            
            del self.passwords[user]
            self.save_passwords()
            self.update_users_list()
            self.append_message(f"Usuário '{user}' removido.", "black")
            
            # Se agora temos 1 usuário (não master), adiciona o master
            if len(self.passwords) == 1 and self.MASTER_USER['login'] not in self.passwords:
                self.passwords[self.MASTER_USER['login']] = self.MASTER_USER['password']
                # Não salva para evitar loop
    
    def on_config_close(self):
        """Lidar com o fechamento da janela de configuração"""
        self.config_window.destroy()
        self.config_window = None
        self.block_main_window()
    
    def on_users_close(self):
        """Lidar com o fechamento da janela de usuários"""
        self.users_window.destroy()
        self.users_window = None
        self.block_main_window()
    
    def update_relays_list(self):
        """Atualiza a lista de relés na aba de configuração"""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        for i, device in enumerate(self.relay_devices):
            frame = ttk.LabelFrame(self.scrollable_frame, text=f"Relé {i+1}", padding=5)
            frame.pack(fill=tk.X, padx=5, pady=5)
            
            ttk.Label(frame, text="Nome:").grid(row=0, column=0, sticky=tk.W)
            name_entry = ttk.Entry(frame)
            name_entry.insert(0, device['name'])
            name_entry.grid(row=0, column=1, sticky=tk.EW, padx=5)
            
            ttk.Label(frame, text="IP:").grid(row=1, column=0, sticky=tk.W)
            ip_entry = ttk.Entry(frame)
            ip_entry.insert(0, device['ip'])
            ip_entry.grid(row=1, column=1, sticky=tk.EW, padx=5)
            
            # Área do dispositivo (apenas áreas cadastradas pelo usuário)
            available_areas = list(self.areas.keys())
            ttk.Label(frame, text="Área:").grid(row=2, column=0, sticky=tk.W)
            area_combo = ttk.Combobox(frame, values=available_areas)
            area_combo.set(device.get('area', available_areas[0] if available_areas else ''))
            area_combo.grid(row=2, column=1, sticky=tk.EW, padx=5)
            
            # Mostrar porta se for diferente da padrão
            port = device.get('port', '80')
            if port != '80':
                ttk.Label(frame, text=f"Porta: {port}").grid(row=3, column=0, columnspan=2, sticky=tk.W, padx=5)
            
            btn_frame = ttk.Frame(frame)
            btn_frame.grid(row=4, column=0, columnspan=2, pady=5)
            
            ttk.Button(btn_frame, text="Salvar", 
                      command=lambda idx=i, n=name_entry, ip=ip_entry, ac=area_combo: self.save_relay(idx, n, ip, ac)).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="Remover", 
                      command=lambda idx=i: self.remove_relay(idx)).pack(side=tk.LEFT, padx=5)
        
        self.scrollable_frame.columnconfigure(1, weight=1)
    
    def add_new_relay(self):
        """Adiciona um novo relé à lista"""
        name = self.new_name.get().strip()
        ip = self.new_ip.get().strip()
        area = self.new_area.get().strip()
        
        if not name or not ip:
            messagebox.showwarning("Aviso", "Por favor, preencha o nome e o IP do relé.")
            return
        
        if not area:
            messagebox.showwarning("Aviso", "Por favor, selecione uma área para o relé.")
            return
        
        for device in self.relay_devices:
            if device['ip'] == ip:
                messagebox.showwarning("Aviso", "Já existe um relé com este endereço IP.")
                return
        
        # Obter a porta (padrão 80 ou personalizada)
        port = self.custom_port.get() if self.advanced_options.get() else '80'
        
        # Validar porta
        try:
            port_int = int(port)
            if not 1 <= port_int <= 65535:
                raise ValueError
        except ValueError:
            messagebox.showerror("Erro", "Porta inválida! Deve ser um número entre 1 e 65535.")
            return
        
        # Adicionar dispositivo
        device_data = {'name': name, 'ip': ip, 'area': area}
        if port != '80':
            device_data['port'] = port
        
        self.relay_devices.append(device_data)
        self.save_config()
        self.update_relays_list()
        
        self.new_name.delete(0, tk.END)
        self.new_ip.delete(0, tk.END)
        self.advanced_options.set(False)
        self.toggle_advanced_options()
        
        self.append_message(f"Relé '{name}' ({ip}:{port}) adicionado à área '{area}' com sucesso!", "black")
    
    def save_relay(self, index, name_entry, ip_entry, area_combo):
        """Salva as alterações em um relé existente"""
        name = name_entry.get().strip()
        ip = ip_entry.get().strip()
        area = area_combo.get().strip()
        
        if not name or not ip:
            messagebox.showwarning("Aviso", "Por favor, preencha o nome e o IP do relé.")
            return
        
        if not area:
            messagebox.showwarning("Aviso", "Por favor, selecione uma área para o relé.")
            return
        
        for i, device in enumerate(self.relay_devices):
            if device['ip'] == ip and i != index:
                messagebox.showwarning("Aviso", "Já existe outro relé com este endereço IP.")
                return
        
        # Manter a porta existente ou usar a padrão
        port = self.relay_devices[index].get('port', '80')
        
        # Atualizar dispositivo
        device_data = {'name': name, 'ip': ip, 'area': area}
        if port != '80':
            device_data['port'] = port
        
        self.relay_devices[index] = device_data
        self.save_config()
        
        self.append_message(f"Relé '{name}' ({ip}:{port}) atualizado com sucesso!", "black")
    
    def remove_relay(self, index):
        """Remove um relé da lista"""
        device = self.relay_devices[index]
        if messagebox.askyesno("Confirmar", f"Remover o relé '{device['name']}' ({device['ip']})?"):
            del self.relay_devices[index]
            self.save_config()
            self.update_relays_list()
            port = device.get('port', '80')
            self.append_message(f"Relé '{device['name']}' ({device['ip']}:{port}) removido.", "black")
    
    def toggle_image_and_send_pulse_area(self, area_name):
        """Alterna a imagem e envia o pulso de emergência para uma área específica"""
        # Obter dispositivos da área
        if area_name == 'GERAL':
            devices_to_activate = self.relay_devices  # TODOS os dispositivos
            display_name = 'GERAL'
        else:
            devices_to_activate = [d for d in self.relay_devices if d.get('area') == area_name]
            display_name = area_name
        
        if not devices_to_activate:
            messagebox.showinfo("Informação", f"Não há dispositivos cadastrados na área '{display_name}'.")
            return
        
        # Atualizar botão para mostrar que o comando está sendo enviado
        if area_name == 'GERAL':
            self.emergency_btn.config(text="ENVIANDO...", bg='#FF8C00')
        else:
            for widget in self.buttons_frame.winfo_children():
                if hasattr(widget, 'cget') and area_name.upper() in widget.cget('text'):
                    widget.config(text="ENVIANDO...", bg='#FF8C00')
                    break
        
        self.status_label.config(text=f"Enviando comando para área '{display_name}'...", foreground='black')
        self.root.update()
        
        try:
            # Enviar comandos e obter resultados
            results = self.send_delayed_pulse_to_devices(devices_to_activate, display_name)
            
            # Mostrar resultados em uma nova janela
            self.show_results_window(results, display_name)
            
            # Atualizar interface após envio
            if area_name == 'GERAL':
                self.emergency_btn.config(text="GERAL", bg=self.button_colors['emergency'])
            else:
                self.create_area_buttons()  # Restaurar botões normais
            
            self.status_label.config(text=f"Comando para área '{display_name}' enviado com sucesso!", foreground=self.button_colors['success'])
        except Exception as e:
            # Se ocorrer algum erro, restaurar o estado normal do botão
            if area_name == 'GERAL':
                self.emergency_btn.config(text="GERAL", bg=self.button_colors['emergency'])
            else:
                self.create_area_buttons()
            
            self.status_label.config(text=f"Erro ao enviar comando para área '{display_name}'", foreground='red')
            print(f"Erro ao enviar comando: {str(e)}")
        
        # Resetar após 3 segundos
        self.root.after(3000, lambda: self.status_label.config(text=""))
    
    def send_delayed_pulse_to_devices(self, devices, area_name):
        """Envia o comando com delay de 5 segundos para dispositivos específicos e retorna resultados"""
        password = self.password.get()
        results = []
        
        if not devices:
            self.log_message(f"Nenhum dispositivo na área '{area_name}' para enviar comando.")
            return results
        
        for device in devices:
            ip = device['ip']
            port = device.get('port', '80')
            device_name = device['name']
            device_area = device.get('area', 'Nenhuma')
            status = "Falha"
            message = ""
            
            try:
                url1_on = f"http://{ip}:{port}/relay_cgi.cgi?type=0&relay=0&on=1&time=0&pwd={password}"
                url2_on = f"http://{ip}:{port}/relay_cgi.cgi?type=0&relay=1&on=1&time=0&pwd={password}"
                
                response1_on = requests.get(url1_on, timeout=5)
                response2_on = requests.get(url2_on, timeout=5)
                
                if response1_on.status_code == 200 and response2_on.status_code == 200:
                    status = "Sucesso"
                    message = f"Comando enviado com sucesso"
                    
                    # Agenda o desligamento após 5 segundos
                    self.root.after(5000, lambda ip=ip, port=port, password=password, device_name=device_name: self.send_off_commands(ip, port, password, device_name))
                else:
                    message = f"Erro HTTP - Status: {response1_on.status_code}, {response2_on.status_code}"
                
            except Exception as e:
                message = f"Erro de conexão: {str(e)}"
            
            results.append({
                'device': device_name,
                'ip': ip,
                'port': port,
                'area': device_area,
                'status': status,
                'message': message
            })
            
            self.log_message(f"Área '{area_name}' - {device_name} ({ip}:{port}): {status} - {message}")
        
        return results
    
    def send_off_commands(self, ip, port, password, device_name):
        """Envia os comandos para desligar os relés após o delay"""
        try:
            url1_off = f"http://{ip}:{port}/relay_cgi.cgi?type=0&relay=0&on=0&time=0&pwd={password}"
            url2_off = f"http://{ip}:{port}/relay_cgi.cgi?type=0&relay=1&on=0&time=0&pwd={password}"
            
            response1_off = requests.get(url1_off, timeout=5)
            response2_off = requests.get(url2_off, timeout=5)
            
            if response1_off.status_code == 200 and response2_off.status_code == 200:
                self.log_message(f"Comando finalizado {device_name} ({ip}:{port}).")
            else:
                self.log_message(f"Erro ao desligar relés em {device_name} ({ip}:{port}). Status: {response1_off.status_code}, {response2_off.status_code}")
        
        except Exception as e:
            self.log_message(f"Falha ao enviar comandos de desligamento para {device_name} ({ip}:{port}): {str(e)}")
    
    def show_results_window(self, results, area_name):
        """Mostra uma janela com os resultados do comando de emergência"""
        results_window = tk.Toplevel(self.root)
        results_window.title(f"Resultados - Área {area_name}")
        results_window.geometry("700x400")  # Largura aumentada para caber a coluna de área
        
        # Configurar ícone
        self.set_window_icon(results_window)
        
        # Centralizar janela
        window_width = 700
        window_height = 400
        screen_width = results_window.winfo_screenwidth()
        screen_height = results_window.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        results_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Frame principal
        main_frame = ttk.Frame(results_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        ttk.Label(main_frame, text=f"Resultados do Comando - Área {area_name}", 
                 font=('Helvetica', 12, 'bold')).pack(pady=(0, 10))
        
        # Frame para a tabela de resultados
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Cabeçalho da tabela
        ttk.Label(table_frame, text="Dispositivo", font=('Helvetica', 10, 'bold')).grid(row=0, column=0, padx=5, pady=2, sticky=tk.W)
        ttk.Label(table_frame, text="IP:Porta", font=('Helvetica', 10, 'bold')).grid(row=0, column=1, padx=5, pady=2, sticky=tk.W)
        ttk.Label(table_frame, text="Área", font=('Helvetica', 10, 'bold')).grid(row=0, column=2, padx=5, pady=2, sticky=tk.W)
        ttk.Label(table_frame, text="Status", font=('Helvetica', 10, 'bold')).grid(row=0, column=3, padx=5, pady=2, sticky=tk.W)
        ttk.Label(table_frame, text="Detalhes", font=('Helvetica', 10, 'bold')).grid(row=0, column=4, padx=5, pady=2, sticky=tk.W)
        
        # Preencher tabela com resultados
        for i, result in enumerate(results, start=1):
            # Dispositivo
            ttk.Label(table_frame, text=result['device']).grid(row=i, column=0, padx=5, pady=2, sticky=tk.W)
            
            # IP:Porta
            ttk.Label(table_frame, text=f"{result['ip']}:{result['port']}").grid(row=i, column=1, padx=5, pady=2, sticky=tk.W)
            
            # Área
            ttk.Label(table_frame, text=result.get('area', 'Nenhuma')).grid(row=i, column=2, padx=5, pady=2, sticky=tk.W)
            
            # Status (com cor)
            status_label = ttk.Label(table_frame, text=result['status'])
            status_label.grid(row=i, column=3, padx=5, pady=2, sticky=tk.W)
            if result['status'] == "Sucesso":
                status_label.config(foreground='green')
            else:
                status_label.config(foreground='red')
            
            # Detalhes
            ttk.Label(table_frame, text=result['message']).grid(row=i, column=4, padx=5, pady=2, sticky=tk.W)
        
        # Botão de fechar
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(btn_frame, text="Fechar", command=results_window.destroy).pack()
    
    def test_all_connections(self):
        """Testa a conexão com todos os dispositivos cadastrados"""
        self.clear_messages()
        
        if not self.relay_devices:
            self.append_message("Nenhum dispositivo cadastrado para testar.", "red")
            return
        
        connected_count = 0
        disconnected_count = 0
        
        for device in self.relay_devices:
            ip = device['ip']
            port = int(device.get('port', '80'))
            area = device.get('area', 'Nenhuma')
            
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                result = sock.connect_ex((ip, port))
                sock.close()
                
                if result == 0:
                    self.append_message(f"{device['name']} ({ip}:{port}) - Área {area}: Conectado", "green")
                    connected_count += 1
                else:
                    self.append_message(f"{device['name']} ({ip}:{port}) - Área {area}: Desconectado", "red")
                    disconnected_count += 1
            
            except Exception as e:
                self.append_message(f"{device['name']} ({ip}:{port}) - Área {area}: Erro ao testar - {str(e)}", "red")
                disconnected_count += 1
    
    def clear_messages(self):
        """Limpa a área de mensagens"""
        if hasattr(self, 'result_text') and self.result_text.winfo_exists():
            self.result_text.config(state=tk.NORMAL)
            self.result_text.delete(1.0, tk.END)
            self.result_text.config(state=tk.DISABLED)
    
    def append_message(self, message, color):
        """Adiciona uma mensagem à área de resultados e ao log"""
        if hasattr(self, 'result_text') and self.result_text.winfo_exists():
            self.result_text.config(state=tk.NORMAL)
            self.result_text.insert(tk.END, message + "\n", color)
            self.result_text.tag_config(color, foreground=color)
            self.result_text.see(tk.END)
            self.result_text.config(state=tk.DISABLED)
        
        self.log_message(message)

if __name__ == "__main__":
    root = tk.Tk()
    app = RelayTesterApp(root)
    root.mainloop()