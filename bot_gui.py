"""
Auto Finance Bot Manager - Modern Dark Theme
Professional, intuitive interface
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue
import logging
import os
import json
from pathlib import Path
from dotenv import load_dotenv, set_key
from scrape_selective import SelectiveScraper
from scheduler import UpdateScheduler
from platform_manager import PlatformConfig, BotLauncher
from conversation_storage import ConversationStorage

load_dotenv()


class DarkModernGUI:
    """Modern dark theme bot manager"""
    
    # Dark theme colors
    COLORS = {
        'bg': '#1e1e1e',
        'bg_secondary': '#252526',
        'bg_tertiary': '#2d2d30',
        'fg': '#cccccc',
        'fg_dim': '#858585',
        'accent': '#007acc',
        'success': '#4ec9b0',
        'warning': '#ce9178',
        'error': '#f48771',
        'border': '#3e3e42'
    }
    
    def __init__(self, root):
        self.root = root
        self.root.title("Auto Finance Bot Manager")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        # State
        self.running_bots = {}
        self.log_queue = queue.Queue()
        self.log_history = []
        self.scraper = SelectiveScraper()
        self.scheduler = UpdateScheduler()
        self.conversation_storage = ConversationStorage()
        
        # Setup
        self.setup_dark_theme()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Build UI
        self.build_ui()
        self.setup_logging()
        self.update_logs()
    
    def setup_dark_theme(self):
        """Configure dark theme"""
        self.root.configure(bg=self.COLORS['bg'])
        
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure styles for dark theme
        style.configure('Dark.TFrame', background=self.COLORS['bg'])
        style.configure('Card.TFrame', background=self.COLORS['bg_secondary'], relief='flat', borderwidth=1)
        style.configure('Dark.TLabel', background=self.COLORS['bg'], foreground=self.COLORS['fg'])
        style.configure('Card.TLabel', background=self.COLORS['bg_secondary'], foreground=self.COLORS['fg'])
        style.configure('Title.TLabel', background=self.COLORS['bg'], foreground=self.COLORS['fg'], 
                       font=('Segoe UI', 16, 'bold'))
        style.configure('Subtitle.TLabel', background=self.COLORS['bg'], foreground=self.COLORS['fg'],
                       font=('Segoe UI', 11, 'bold'))
        style.configure('Dark.TButton', background=self.COLORS['bg_tertiary'], foreground=self.COLORS['fg'])
        style.configure('Accent.TButton', background=self.COLORS['accent'], foreground='white')
        
        style.map('Dark.TButton',
                 background=[('active', self.COLORS['accent'])])
    
    def build_ui(self):
        """Build modern UI"""
        # Top bar
        top_bar = tk.Frame(self.root, bg=self.COLORS['bg_tertiary'], height=60)
        top_bar.pack(fill=tk.X)
        top_bar.pack_propagate(False)
        
        # Title
        tk.Label(
            top_bar, 
            text="AUTO FINANCE",
            font=('Segoe UI', 18, 'bold'),
            bg=self.COLORS['bg_tertiary'],
            fg=self.COLORS['accent']
        ).pack(side=tk.LEFT, padx=30, pady=15)
        
        # Status indicator
        self.status_label = tk.Label(
            top_bar,
            text="● No bots running",
            font=('Segoe UI', 10),
            bg=self.COLORS['bg_tertiary'],
            fg=self.COLORS['fg_dim']
        )
        self.status_label.pack(side=tk.RIGHT, padx=30)
        
        # Main content
        content = tk.Frame(self.root, bg=self.COLORS['bg'])
        content.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Bot controls (40%)
        left_panel = tk.Frame(content, bg=self.COLORS['bg'], width=480)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=20, pady=20)
        left_panel.pack_propagate(False)
        
        # Right panel - Info/Actions (60%)
        right_panel = tk.Frame(content, bg=self.COLORS['bg'])
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 20), pady=20)
        
        # Build panels
        self.build_left_panel(left_panel)
        self.build_right_panel(right_panel)
    
    def build_left_panel(self, parent):
        """Build left panel - bot controls"""
        # Model selector card
        model_card = self.create_card(parent, "AI Model")
        
        model_frame = tk.Frame(model_card, bg=self.COLORS['bg_secondary'])
        model_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.selected_model_var = tk.StringVar(value=os.getenv('BOT_MODEL', 'claude-sonnet-4-20250514'))
        
        model_combo = ttk.Combobox(
            model_frame,
            textvariable=self.selected_model_var,
            values=["claude-sonnet-4-20250514", "claude-3-5-haiku-20241022", "gpt-4o", "gpt-4o-mini"],
            state='readonly',
            font=('Segoe UI', 9)
        )
        model_combo.pack(fill=tk.X)
        model_combo.bind('<<ComboboxSelected>>', self.on_model_changed)
        
        # Platform bots
        all_bots = PlatformConfig.get_available_bots()
        platforms = {}
        for bot in all_bots:
            if bot['platform'] not in platforms:
                platforms[bot['platform']] = []
            platforms[bot['platform']].append(bot)
        
        # Create card for each platform
        for platform_key, bots in platforms.items():
            self.create_platform_card(parent, platform_key, bots)
    
    def build_right_panel(self, parent):
        """Build right panel - tabs"""
        # Tab control
        tab_frame = tk.Frame(parent, bg=self.COLORS['bg'])
        tab_frame.pack(fill=tk.X, pady=(0, 15))
        
        tabs = [
            ("Activity", self.show_activity),
            ("Conversations", self.show_conversations),
            ("Analytics", self.show_analytics),
            ("Prompt", self.show_prompt),
            ("Settings", self.show_settings),
            ("Updates", self.show_updates)
        ]
        
        self.tab_buttons = {}
        for i, (name, command) in enumerate(tabs):
            btn = tk.Button(
                tab_frame,
                text=name,
                command=command,
                bg=self.COLORS['bg_tertiary'],
                fg=self.COLORS['fg'],
                font=('Segoe UI', 10),
                relief='flat',
                padx=20,
                pady=10,
                cursor='hand2'
            )
            btn.pack(side=tk.LEFT, padx=2)
            self.tab_buttons[name] = btn
        
        # Tab content area
        self.tab_content = tk.Frame(parent, bg=self.COLORS['bg'])
        self.tab_content.pack(fill=tk.BOTH, expand=True)
        
        # Build all tab views
        self.activity_frame = tk.Frame(self.tab_content, bg=self.COLORS['bg'])
        self.conversations_frame = tk.Frame(self.tab_content, bg=self.COLORS['bg'])
        self.analytics_frame = tk.Frame(self.tab_content, bg=self.COLORS['bg'])
        self.prompt_frame = tk.Frame(self.tab_content, bg=self.COLORS['bg'])
        self.settings_frame = tk.Frame(self.tab_content, bg=self.COLORS['bg'])
        self.updates_frame = tk.Frame(self.tab_content, bg=self.COLORS['bg'])
        
        self.build_activity_tab()
        self.build_conversations_tab()
        self.build_analytics_tab()
        self.build_prompt_tab()
        self.build_settings_tab()
        self.build_updates_tab()
        
        # Show default
        self.show_activity()
    
    def create_card(self, parent, title):
        """Create a dark mode card"""
        card = tk.Frame(parent, bg=self.COLORS['bg_secondary'], highlightbackground=self.COLORS['border'], 
                       highlightthickness=1)
        card.pack(fill=tk.X, pady=(0, 15))
        
        # Title
        title_frame = tk.Frame(card, bg=self.COLORS['bg_tertiary'])
        title_frame.pack(fill=tk.X)
        
        tk.Label(
            title_frame,
            text=title,
            font=('Segoe UI', 10, 'bold'),
            bg=self.COLORS['bg_tertiary'],
            fg=self.COLORS['fg'],
            anchor='w'
        ).pack(fill=tk.X, padx=15, pady=10)
        
        return card
    
    def create_platform_card(self, parent, platform_key, bots):
        """Create platform bot card"""
        platform_info = PlatformConfig.get_platform_info(platform_key)
        card = self.create_card(parent, f"{platform_info['name']} Bots")
        
        for bot in bots:
            bot_id = bot['id']
            
            bot_frame = tk.Frame(card, bg=self.COLORS['bg_secondary'])
            bot_frame.pack(fill=tk.X, padx=15, pady=10)
            
            # Bot name & status
            info = tk.Frame(bot_frame, bg=self.COLORS['bg_secondary'])
            info.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            tk.Label(
                info,
                text=bot['bot_name'].upper(),
                font=('Segoe UI', 11, 'bold'),
                bg=self.COLORS['bg_secondary'],
                fg=self.COLORS['fg']
            ).pack(side=tk.LEFT)
            
            # Status indicator
            is_running = bot_id in self.running_bots
            
            if not hasattr(self, 'bot_status'):
                self.bot_status = {}
            
            status_label = tk.Label(
                info,
                text="● ONLINE" if is_running else "● OFFLINE",
                font=('Segoe UI', 9, 'bold'),
                bg=self.COLORS['bg_secondary'],
                fg=self.COLORS['success'] if is_running else self.COLORS['fg_dim']
            )
            status_label.pack(side=tk.LEFT, padx=15)
            self.bot_status[bot_id] = status_label
            
            # Buttons
            btn_frame = tk.Frame(bot_frame, bg=self.COLORS['bg_secondary'])
            btn_frame.pack(side=tk.RIGHT)
            
            if not hasattr(self, 'bot_buttons'):
                self.bot_buttons = {}
            
            start_btn = tk.Button(
                btn_frame,
                text="START",
                command=lambda b=bot: self.start_bot(b),
                bg=self.COLORS['success'],
                fg='white',
                font=('Segoe UI', 9, 'bold'),
                relief='flat',
                padx=15,
                pady=5,
                cursor='hand2',
                state='disabled' if is_running else 'normal'
            )
            start_btn.pack(side=tk.LEFT, padx=3)
            
            stop_btn = tk.Button(
                btn_frame,
                text="STOP",
                command=lambda b=bot: self.stop_bot(b),
                bg=self.COLORS['error'],
                fg='white',
                font=('Segoe UI', 9, 'bold'),
                relief='flat',
                padx=15,
                pady=5,
                cursor='hand2',
                state='normal' if is_running else 'disabled'
            )
            stop_btn.pack(side=tk.LEFT, padx=3)
            
            self.bot_buttons[bot_id] = {'start': start_btn, 'stop': stop_btn}
    
    def build_activity_tab(self):
        """Build activity/logs tab"""
        parent = self.activity_frame
        
        tk.Label(
            parent,
            text="LIVE ACTIVITY",
            font=('Segoe UI', 12, 'bold'),
            bg=self.COLORS['bg'],
            fg=self.COLORS['fg']
        ).pack(anchor='w', pady=(0, 10))
        
        # Logs
        self.log_text = scrolledtext.ScrolledText(
            parent,
            wrap=tk.WORD,
            font=('Consolas', 9),
            bg='#0d1117',
            fg='#c9d1d9',
            insertbackground='white',
            relief='flat',
            highlightthickness=1,
            highlightbackground=self.COLORS['border']
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
    
    def build_conversations_tab(self):
        """Build conversations browser"""
        parent = self.conversations_frame
        
        # Header
        header = tk.Frame(parent, bg=self.COLORS['bg'])
        header.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(
            header,
            text="CONVERSATIONS",
            font=('Segoe UI', 12, 'bold'),
            bg=self.COLORS['bg'],
            fg=self.COLORS['fg']
        ).pack(side=tk.LEFT)
        
        # Search
        self.conv_search_var = tk.StringVar()
        search_entry = tk.Entry(
            header,
            textvariable=self.conv_search_var,
            bg=self.COLORS['bg_secondary'],
            fg=self.COLORS['fg'],
            insertbackground='white',
            relief='flat',
            font=('Segoe UI', 10)
        )
        search_entry.pack(side=tk.RIGHT, padx=5)
        
        tk.Button(
            header,
            text="SEARCH",
            command=self.search_conversations,
            bg=self.COLORS['accent'],
            fg='white',
            font=('Segoe UI', 9, 'bold'),
            relief='flat',
            padx=15,
            pady=5,
            cursor='hand2'
        ).pack(side=tk.RIGHT, padx=5)
        
        # Content
        content = tk.Frame(parent, bg=self.COLORS['bg'])
        content.pack(fill=tk.BOTH, expand=True)
        
        # Users list (30%)
        users_frame = tk.Frame(content, bg=self.COLORS['bg_secondary'], width=250)
        users_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        users_frame.pack_propagate(False)
        
        tk.Label(
            users_frame,
            text="USERS",
            font=('Segoe UI', 9, 'bold'),
            bg=self.COLORS['bg_secondary'],
            fg=self.COLORS['fg']
        ).pack(pady=10)
        
        self.users_listbox = tk.Listbox(
            users_frame,
            bg=self.COLORS['bg_tertiary'],
            fg=self.COLORS['fg'],
            font=('Segoe UI', 9),
            relief='flat',
            highlightthickness=0
        )
        self.users_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.users_listbox.bind('<<ListboxSelect>>', self.on_user_selected)
        
        # Conversations (70%)
        convos_frame = tk.Frame(content, bg=self.COLORS['bg_secondary'])
        convos_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(
            convos_frame,
            text="CONVERSATION HISTORY",
            font=('Segoe UI', 9, 'bold'),
            bg=self.COLORS['bg_secondary'],
            fg=self.COLORS['fg']
        ).pack(pady=10)
        
        self.convos_text = scrolledtext.ScrolledText(
            convos_frame,
            wrap=tk.WORD,
            font=('Segoe UI', 9),
            bg=self.COLORS['bg_tertiary'],
            fg=self.COLORS['fg'],
            relief='flat',
            highlightthickness=0
        )
        self.convos_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Load data
        self.refresh_conversations()
    
    def build_analytics_tab(self):
        """Build analytics dashboard"""
        parent = self.analytics_frame
        
        tk.Label(
            parent,
            text="ANALYTICS",
            font=('Segoe UI', 12, 'bold'),
            bg=self.COLORS['bg'],
            fg=self.COLORS['fg']
        ).pack(anchor='w', pady=(0, 15))
        
        # Stats grid
        self.analytics_grid = tk.Frame(parent, bg=self.COLORS['bg'])
        self.analytics_grid.pack(fill=tk.BOTH, expand=True)
        
        self.refresh_analytics()
    
    def build_prompt_tab(self):
        """Build system prompt editor tab"""
        parent = self.prompt_frame
        
        # Make scrollable
        canvas = tk.Canvas(parent, bg=self.COLORS['bg'], highlightthickness=0)
        scrollbar = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.COLORS['bg'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Content
        tk.Label(
            scrollable_frame,
            text="BOT PERSONALITY",
            font=('Segoe UI', 12, 'bold'),
            bg=self.COLORS['bg'],
            fg=self.COLORS['fg']
        ).pack(anchor='w', pady=(0, 15))
        
        # Preset buttons
        preset_card = self.create_card(scrollable_frame, "Personality Presets")
        
        preset_grid = tk.Frame(preset_card, bg=self.COLORS['bg_secondary'])
        preset_grid.pack(fill=tk.X, padx=15, pady=15)
        
        presets = [
            ("DEFAULT", "Casual & Concise", "default"),
            ("TECHNICAL", "Detailed & Expert", "technical"),
            ("BEGINNER", "Simple & Patient", "beginner_friendly"),
            ("MARKETING", "Enthusiastic & Sales", "marketing")
        ]
        
        for i, (name, desc, preset_key) in enumerate(presets):
            col = i % 2
            row = i // 2
            
            btn = tk.Button(
                preset_grid,
                text=f"{name}\n{desc}",
                command=lambda p=preset_key: self.apply_preset(p),
                bg=self.COLORS['bg_tertiary'],
                fg=self.COLORS['fg'],
                font=('Segoe UI', 9, 'bold'),
                relief='flat',
                pady=15,
                cursor='hand2'
            )
            btn.grid(row=row, column=col, sticky='ew', padx=5, pady=5)
            preset_grid.columnconfigure(col, weight=1)
        
        # Editor
        editor_card = self.create_card(scrollable_frame, "Custom System Prompt")
        
        self.prompt_text = scrolledtext.ScrolledText(
            editor_card,
            wrap=tk.WORD,
            height=20,
            font=('Consolas', 10),
            bg=self.COLORS['bg_tertiary'],
            fg=self.COLORS['fg'],
            insertbackground='white',
            relief='flat'
        )
        self.prompt_text.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Load current
        self.load_current_prompt()
        
        # Save button
        btn_frame = tk.Frame(editor_card, bg=self.COLORS['bg_secondary'])
        btn_frame.pack(fill=tk.X, padx=15, pady=15)
        
        tk.Button(
            btn_frame,
            text="SAVE PROMPT",
            command=self.save_custom_prompt,
            bg=self.COLORS['accent'],
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            relief='flat',
            padx=30,
            pady=10,
            cursor='hand2'
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            btn_frame,
            text="RESET TO DEFAULT",
            command=self.load_current_prompt,
            bg=self.COLORS['bg_tertiary'],
            fg=self.COLORS['fg'],
            font=('Segoe UI', 10),
            relief='flat',
            padx=20,
            pady=10,
            cursor='hand2'
        ).pack(side=tk.LEFT, padx=5)
    
    def load_current_prompt(self):
        """Load current system prompt"""
        prompt_file = Path("system_prompts.json")
        if prompt_file.exists():
            with open(prompt_file, 'r') as f:
                prompts = json.load(f)
                self.prompt_text.delete(1.0, tk.END)
                self.prompt_text.insert(1.0, prompts.get('default', ''))
    
    def apply_preset(self, preset_name):
        """Apply personality preset"""
        prompt_file = Path("system_prompts.json")
        if prompt_file.exists():
            with open(prompt_file, 'r') as f:
                prompts = json.load(f)
                preset_text = prompts.get(preset_name, prompts.get('default', ''))
                self.prompt_text.delete(1.0, tk.END)
                self.prompt_text.insert(1.0, preset_text)
                self.log(f"Loaded {preset_name} preset")
    
    def save_custom_prompt(self):
        """Save custom prompt"""
        custom = self.prompt_text.get(1.0, tk.END).strip()
        
        if not custom:
            messagebox.showerror("Error", "Prompt cannot be empty!")
            return
        
        prompt_file = Path("system_prompts.json")
        if prompt_file.exists():
            with open(prompt_file, 'r') as f:
                prompts = json.load(f)
        else:
            prompts = {}
        
        prompts['default'] = custom
        
        with open(prompt_file, 'w') as f:
            json.dump(prompts, f, indent=2)
        
        self.log("[OK] System prompt saved!")
        messagebox.showinfo("Saved", "System prompt saved!\n\nRestart bots for changes to take effect.")
    
    def build_settings_tab(self):
        """Build settings/configuration tab"""
        parent = self.settings_frame
        
        # Make scrollable
        canvas = tk.Canvas(parent, bg=self.COLORS['bg'], highlightthickness=0)
        scrollbar = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.COLORS['bg'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        parent = scrollable_frame  # Use scrollable frame as parent
        
        tk.Label(
            parent,
            text="CONFIGURATION",
            font=('Segoe UI', 12, 'bold'),
            bg=self.COLORS['bg'],
            fg=self.COLORS['fg']
        ).pack(anchor='w', pady=(0, 15))
        
        # API Keys
        api_card = self.create_card(parent, "API Keys")
        
        # Claude Key
        claude_frame = tk.Frame(api_card, bg=self.COLORS['bg_secondary'])
        claude_frame.pack(fill=tk.X, padx=15, pady=10)
        
        tk.Label(claude_frame, text="Claude (Anthropic):", bg=self.COLORS['bg_secondary'], 
                fg=self.COLORS['fg'], font=('Segoe UI', 9, 'bold')).grid(row=0, column=0, sticky='w', pady=5)
        
        self.claude_key_var = tk.StringVar(value=os.getenv('ANTHROPIC_API_KEY', ''))
        claude_entry = tk.Entry(claude_frame, textvariable=self.claude_key_var, show='*', width=50,
                               bg=self.COLORS['bg_tertiary'], fg=self.COLORS['fg'], insertbackground='white')
        claude_entry.grid(row=1, column=0, sticky='ew', padx=(0, 10))
        
        tk.Button(claude_frame, text="SAVE", command=lambda: self.save_api_key('ANTHROPIC_API_KEY', self.claude_key_var.get()),
                 bg=self.COLORS['accent'], fg='white', relief='flat', padx=15).grid(row=1, column=1)
        
        claude_frame.columnconfigure(0, weight=1)
        
        # OpenAI Key
        openai_frame = tk.Frame(api_card, bg=self.COLORS['bg_secondary'])
        openai_frame.pack(fill=tk.X, padx=15, pady=10)
        
        tk.Label(openai_frame, text="OpenAI:", bg=self.COLORS['bg_secondary'], 
                fg=self.COLORS['fg'], font=('Segoe UI', 9, 'bold')).grid(row=0, column=0, sticky='w', pady=5)
        
        self.openai_key_var = tk.StringVar(value=os.getenv('OPENAI_API_KEY', ''))
        openai_entry = tk.Entry(openai_frame, textvariable=self.openai_key_var, show='*', width=50,
                               bg=self.COLORS['bg_tertiary'], fg=self.COLORS['fg'], insertbackground='white')
        openai_entry.grid(row=1, column=0, sticky='ew', padx=(0, 10))
        
        tk.Button(openai_frame, text="SAVE", command=lambda: self.save_api_key('OPENAI_API_KEY', self.openai_key_var.get()),
                 bg=self.COLORS['accent'], fg='white', relief='flat', padx=15).grid(row=1, column=1)
        
        openai_frame.columnconfigure(0, weight=1)
        
        # Platform Tokens
        platforms = ['telegram', 'discord', 'slack']
        for platform in platforms:
            self.create_platform_token_section(parent, platform)
    
    def create_platform_token_section(self, parent, platform):
        """Create section to add platform tokens"""
        platform_name = platform.capitalize()
        card = self.create_card(parent, f"{platform_name} Bots")
        
        # Show existing
        all_bots = PlatformConfig.get_available_bots()
        platform_bots = [b for b in all_bots if b['platform'] == platform]
        
        existing_frame = tk.Frame(card, bg=self.COLORS['bg_secondary'])
        existing_frame.pack(fill=tk.X, padx=15, pady=10)
        
        if platform_bots:
            tk.Label(existing_frame, text="Configured:", bg=self.COLORS['bg_secondary'],
                    fg=self.COLORS['fg'], font=('Segoe UI', 9, 'bold')).pack(anchor='w', pady=(0, 5))
            for bot in platform_bots:
                tk.Label(existing_frame, text=f"✓ {bot['bot_name'].upper()}: {bot['token'][:20]}...",
                        bg=self.COLORS['bg_secondary'], fg=self.COLORS['success'], 
                        font=('Segoe UI', 9)).pack(anchor='w', pady=2)
        
        # Add new
        add_frame = tk.Frame(card, bg=self.COLORS['bg_secondary'])
        add_frame.pack(fill=tk.X, padx=15, pady=10)
        
        tk.Label(add_frame, text="Add New Bot:", bg=self.COLORS['bg_secondary'],
                fg=self.COLORS['fg'], font=('Segoe UI', 9, 'bold')).grid(row=0, column=0, columnspan=3, sticky='w', pady=(0, 5))
        
        tk.Label(add_frame, text="Name:", bg=self.COLORS['bg_secondary'], fg=self.COLORS['fg']).grid(row=1, column=0, sticky='w', padx=(0, 5))
        
        name_var = tk.StringVar()
        tk.Entry(add_frame, textvariable=name_var, width=12, bg=self.COLORS['bg_tertiary'],
                fg=self.COLORS['fg'], insertbackground='white').grid(row=1, column=1, padx=5)
        
        tk.Label(add_frame, text="Token:", bg=self.COLORS['bg_secondary'], fg=self.COLORS['fg']).grid(row=2, column=0, sticky='w', padx=(0, 5), pady=5)
        
        token_var = tk.StringVar()
        tk.Entry(add_frame, textvariable=token_var, width=40, bg=self.COLORS['bg_tertiary'],
                fg=self.COLORS['fg'], insertbackground='white').grid(row=2, column=1, sticky='ew', padx=5)
        
        tk.Button(add_frame, text="ADD BOT", command=lambda: self.add_bot_token(platform, name_var, token_var),
                 bg=self.COLORS['success'], fg='white', relief='flat', padx=15, pady=5).grid(row=2, column=2, padx=5)
        
        add_frame.columnconfigure(1, weight=1)
    
    def save_api_key(self, key_name, value):
        """Save API key"""
        if not value.strip():
            messagebox.showerror("Error", "Key cannot be empty!")
            return
        
        set_key(Path('.env'), key_name, value.strip())
        self.log(f"[OK] Saved {key_name}")
        messagebox.showinfo("Saved", f"{key_name} updated!")
    
    def add_bot_token(self, platform, name_var, token_var):
        """Add new bot token"""
        name = name_var.get().strip().upper()
        token = token_var.get().strip()
        
        if not name or not token:
            messagebox.showerror("Error", "Please provide both name and token")
            return
        
        env_key = f"{platform.upper()}_BOT_TOKEN_{name}"
        set_key(Path('.env'), env_key, token)
        
        self.log(f"[OK] Added {env_key}")
        messagebox.showinfo("Success", f"Bot added!\n\nRestart GUI to see it in bot list.")
        
        name_var.set('')
        token_var.set('')
    
    def build_updates_tab(self):
        """Build updates tab"""
        parent = self.updates_frame
        
        tk.Label(
            parent,
            text="DATA UPDATES",
            font=('Segoe UI', 12, 'bold'),
            bg=self.COLORS['bg'],
            fg=self.COLORS['fg']
        ).pack(anchor='w', pady=(0, 15))
        
        # Update buttons
        updates_grid = tk.Frame(parent, bg=self.COLORS['bg'])
        updates_grid.pack(fill=tk.X, pady=(0, 20))
        
        updates = [
            ("QUICK UPDATE", "Website Only\n~5-10 minutes", self.quick_update, self.COLORS['accent']),
            ("FULL UPDATE", "All Sources\n~20 minutes", self.full_update, self.COLORS['success']),
            ("BLOG ONLY", "Blog Posts\n~3-5 minutes", self.blog_update, self.COLORS['warning']),
            ("DOCS ONLY", "Documentation\n~3-5 minutes", self.docs_update, self.COLORS['warning'])
        ]
        
        for i, (title, desc, cmd, color) in enumerate(updates):
            row, col = i // 2, i % 2
            
            btn = tk.Button(
                updates_grid,
                text=f"{title}\n{desc}",
                command=cmd,
                bg=color,
                fg='white',
                font=('Segoe UI', 10, 'bold'),
                relief='flat',
                pady=20,
                cursor='hand2'
            )
            btn.grid(row=row, column=col, sticky='ew', padx=5, pady=5)
            updates_grid.columnconfigure(col, weight=1)
        
        # History
        history_card = self.create_card(parent, "Last Updated")
        
        self.last_update_label = tk.Label(
            history_card,
            text="Loading...",
            font=('Segoe UI', 9),
            bg=self.COLORS['bg_secondary'],
            fg=self.COLORS['fg'],
            justify='left'
        )
        self.last_update_label.pack(anchor='w', padx=15, pady=10)
        self.update_last_update_display()
    
    # Tab switching
    def show_tab(self, frame, tab_name):
        """Show specific tab"""
        for f in [self.activity_frame, self.conversations_frame, self.analytics_frame, 
                 self.prompt_frame, self.settings_frame, self.updates_frame]:
            f.pack_forget()
        
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Update tab button styles
        for name, btn in self.tab_buttons.items():
            if name == tab_name:
                btn.config(bg=self.COLORS['accent'], fg='white')
            else:
                btn.config(bg=self.COLORS['bg_tertiary'], fg=self.COLORS['fg'])
    
    def show_activity(self):
        """Show activity tab"""
        self.show_tab(self.activity_frame, "Activity")
    
    def show_conversations(self):
        """Show conversations tab"""
        self.show_tab(self.conversations_frame, "Conversations")
        self.refresh_conversations()
    
    def show_analytics(self):
        """Show analytics tab"""
        self.show_tab(self.analytics_frame, "Analytics")
        self.refresh_analytics()
    
    def show_settings(self):
        """Show settings tab"""
        self.show_tab(self.settings_frame, "Settings")
    
    def show_prompt(self):
        """Show prompt editor tab"""
        self.show_tab(self.prompt_frame, "Prompt")
    
    def show_updates(self):
        """Show updates tab"""
        self.show_tab(self.updates_frame, "Updates")
        self.update_last_update_display()
    
    # Bot control
    def start_bot(self, bot_config):
        """Start a bot"""
        bot_id = bot_config['id']
        
        if bot_id in self.running_bots:
            messagebox.showinfo("Running", f"{bot_config['display_name']} is already running!")
            return
        
        if bot_config.get('status') != 'active':
            messagebox.showerror("Not Supported", f"{bot_config['platform_name']} support in progress.")
            return
        
        self.log(f"Starting {bot_config['display_name']}...")
        
        def run_bot():
            try:
                bot = BotLauncher.launch_bot(bot_config)
                self.running_bots[bot_id] = {'bot': bot, 'config': bot_config}
                
                def update_ui():
                    if bot_id in self.bot_status:
                        self.bot_status[bot_id].config(text="● ONLINE", fg=self.COLORS['success'])
                    if bot_id in self.bot_buttons:
                        self.bot_buttons[bot_id]['start'].config(state='disabled')
                        self.bot_buttons[bot_id]['stop'].config(state='normal')
                    self.update_status_bar()
                
                self.root.after(0, update_ui)
                self.log(f"[OK] {bot_config['display_name']} started")
                bot.run()
            except Exception as e:
                self.log(f"[ERROR] {e}")
        
        threading.Thread(target=run_bot, daemon=False).start()
    
    def stop_bot(self, bot_config):
        """Stop a bot"""
        bot_id = bot_config['id']
        
        if bot_id not in self.running_bots:
            return
        
        self.log(f"Stopping {bot_config['display_name']}...")
        
        def stop_in_bg():
            try:
                bot = self.running_bots[bot_id].get('bot')
                if bot and hasattr(bot, 'stop'):
                    bot.stop()
                
                if bot_id in self.running_bots:
                    del self.running_bots[bot_id]
                
                def update_ui():
                    if bot_id in self.bot_status:
                        self.bot_status[bot_id].config(text="● OFFLINE", fg=self.COLORS['fg_dim'])
                    if bot_id in self.bot_buttons:
                        self.bot_buttons[bot_id]['start'].config(state='normal')
                        self.bot_buttons[bot_id]['stop'].config(state='disabled')
                    self.update_status_bar()
                
                self.root.after(0, update_ui)
                self.log(f"[OK] {bot_config['display_name']} stopped")
            except Exception as e:
                self.log(f"[ERROR] {e}")
        
        threading.Thread(target=stop_in_bg, daemon=True).start()
    
    def update_status_bar(self):
        """Update header status"""
        count = len(self.running_bots)
        if count == 0:
            self.status_label.config(text="● No bots running", fg=self.COLORS['fg_dim'])
        else:
            self.status_label.config(text=f"● {count} bot(s) running", fg=self.COLORS['success'])
    
    # Conversation methods
    def refresh_conversations(self):
        """Refresh conversation list"""
        if hasattr(self, 'users_listbox'):
            self.users_listbox.delete(0, tk.END)
            users = self.conversation_storage.get_all_users()
            for user in users:
                self.users_listbox.insert(tk.END, f"{user['username']} ({user['total_questions']})")
            if not hasattr(self.users_listbox, 'user_data'):
                self.users_listbox.user_data = {}
            self.users_listbox.user_data = users
    
    def on_user_selected(self, event):
        """Load user conversations"""
        selection = self.users_listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        users = getattr(self.users_listbox, 'user_data', [])
        if idx >= len(users):
            return
        
        user = users[idx]
        convos = self.conversation_storage.get_user_conversations(user['user_id'], 100)
        
        self.convos_text.delete(1.0, tk.END)
        self.convos_text.insert(tk.END, f"=== {user['username']} ===\n\n")
        
        for convo in convos:
            self.convos_text.insert(tk.END, f"[{convo['timestamp']}]\n")
            self.convos_text.insert(tk.END, f"Q: {convo['question']}\n")
            self.convos_text.insert(tk.END, f"A: {convo['answer']}\n\n")
            self.convos_text.insert(tk.END, "-" * 80 + "\n\n")
    
    def search_conversations(self):
        """Search conversations"""
        keyword = self.conv_search_var.get().strip()
        if not keyword:
            return
        
        results = self.conversation_storage.search_conversations(keyword, 50)
        
        self.convos_text.delete(1.0, tk.END)
        self.convos_text.insert(tk.END, f"=== Search: '{keyword}' ({len(results)} results) ===\n\n")
        
        for r in results:
            self.convos_text.insert(tk.END, f"[{r['timestamp']}] {r['username']}\n")
            self.convos_text.insert(tk.END, f"Q: {r['question']}\n")
            self.convos_text.insert(tk.END, f"A: {r['answer'][:200]}...\n\n")
    
    def refresh_analytics(self):
        """Refresh analytics"""
        for widget in self.analytics_grid.winfo_children():
            widget.destroy()
        
        analytics = self.conversation_storage.get_analytics()
        
        # Stats cards
        stats = [
            ("TOTAL CONVERSATIONS", str(analytics['total_conversations']), self.COLORS['accent']),
            ("UNIQUE USERS", str(analytics['unique_users']), self.COLORS['success']),
            ("TOKENS USED", f"{analytics['total_tokens_used']:,}", self.COLORS['warning']),
            ("LAST 24H", str(analytics['conversations_24h']), self.COLORS['error'])
        ]
        
        for i, (label, value, color) in enumerate(stats):
            card = tk.Frame(self.analytics_grid, bg=self.COLORS['bg_secondary'], 
                          highlightbackground=self.COLORS['border'], highlightthickness=1)
            card.grid(row=0, column=i, sticky='ew', padx=5, pady=5)
            self.analytics_grid.columnconfigure(i, weight=1)
            
            tk.Label(card, text=value, font=('Segoe UI', 32, 'bold'), bg=self.COLORS['bg_secondary'], 
                    fg=color).pack(pady=(20, 5))
            tk.Label(card, text=label, font=('Segoe UI', 8), bg=self.COLORS['bg_secondary'],
                    fg=self.COLORS['fg_dim']).pack(pady=(0, 20))
    
    # Update methods
    def quick_update(self):
        """Quick update"""
        if messagebox.askyesno("Quick Update", "Scrape website?\n\n~5-10 minutes"):
            self.log("Starting quick update...")
            threading.Thread(target=lambda: self._run_update('quick'), daemon=True).start()
    
    def full_update(self):
        """Full update"""
        if messagebox.askyesno("Full Update", "Scrape all sources?\n\n~20 minutes"):
            self.log("Starting full update...")
            threading.Thread(target=lambda: self._run_update('full'), daemon=True).start()
    
    def blog_update(self):
        """Blog update"""
        if messagebox.askyesno("Blog Update", "Scrape blog?\n\n~3-5 minutes"):
            self.log("Starting blog update...")
            threading.Thread(target=lambda: self._run_update('blog'), daemon=True).start()
    
    def docs_update(self):
        """Docs update"""
        if messagebox.askyesno("Docs Update", "Scrape docs?\n\n~3-5 minutes"):
            self.log("Starting docs update...")
            threading.Thread(target=lambda: self._run_update('docs'), daemon=True).start()
    
    def _run_update(self, update_type):
        """Run update"""
        try:
            if update_type == 'quick':
                success = self.scraper.quick_update()
            elif update_type == 'full':
                success = self.scraper.full_update()
            elif update_type == 'blog':
                success = self.scraper.blog_only_update()
            else:
                success = self.scraper.docs_only_update()
            
            if success:
                self.log(f"[OK] {update_type.capitalize()} update complete!")
                self.update_last_update_display()
                messagebox.showinfo("Success", "Update completed!")
        except Exception as e:
            self.log(f"[ERROR] {e}")
    
    def update_last_update_display(self):
        """Update last update display"""
        last_updates = self.scraper.get_last_update_info()
        
        text = []
        for source, timestamp in last_updates.items():
            if timestamp:
                from datetime import datetime
                try:
                    dt = datetime.fromisoformat(timestamp)
                    text.append(f"{source.upper()}: {dt.strftime('%Y-%m-%d %H:%M')}")
                except:
                    text.append(f"{source.upper()}: {timestamp}")
        
        if hasattr(self, 'last_update_label'):
            self.last_update_label.config(text="\n".join(text) if text else "No updates yet")
    
    def on_model_changed(self, event):
        """Model changed"""
        model = self.selected_model_var.get()
        set_key(Path('.env'), 'BOT_MODEL', model)
        self.log(f"Model changed to: {model}")
        messagebox.showinfo("Model Changed", f"{model}\n\nRestart bots for changes to take effect.")
    
    # Logging
    def setup_logging(self):
        """Setup logging"""
        class QueueHandler(logging.Handler):
            def __init__(self, log_queue):
                super().__init__()
                self.log_queue = log_queue
            
            def emit(self, record):
                self.log_queue.put(self.format(record))
        
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        handler = QueueHandler(self.log_queue)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        logger.addHandler(handler)
    
    def update_logs(self):
        """Update logs"""
        try:
            while True:
                msg = self.log_queue.get_nowait()
                self.log_history.append(msg)
                if hasattr(self, 'log_text'):
                    self.log_text.insert(tk.END, msg + '\n')
                    self.log_text.see(tk.END)
        except queue.Empty:
            pass
        
        self.root.after(100, self.update_logs)
    
    def log(self, message):
        """Log message"""
        self.log_queue.put(message)
    
    def on_closing(self):
        """Handle window close"""
        if self.running_bots:
            if messagebox.askyesno("Bots Running", f"{len(self.running_bots)} bot(s) running.\n\nStop all and close?"):
                for bot_id in list(self.running_bots.keys()):
                    bot_config = self.running_bots[bot_id]['config']
                    self.stop_bot(bot_config)
                self.root.after(1000, self.root.destroy)
        else:
            self.root.destroy()


def main():
    """Main entry"""
    root = tk.Tk()
    app = DarkModernGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

