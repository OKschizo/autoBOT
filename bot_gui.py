"""
Auto Finance Bot Manager - Complete GUI
First-time setup wizard + Multi-platform configuration
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue
import logging
import os
from pathlib import Path
from dotenv import load_dotenv, set_key
from scrape_selective import SelectiveScraper
from scheduler import UpdateScheduler
from platform_manager import PlatformConfig, BotLauncher

load_dotenv()


class SetupWizard:
    """First-time setup wizard"""
    
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("Auto Finance Bot Setup")
        self.window.geometry("600x500")
        self.window.transient(parent)
        self.window.grab_set()
        
        self.setup_complete = False
        self.setup_ui()
    
    def setup_ui(self):
        """Setup wizard UI"""
        # Title
        title = ttk.Label(
            self.window,
            text="Welcome to Auto Finance Bot Manager!",
            font=('Arial', 14, 'bold')
        )
        title.pack(pady=20)
        
        ttk.Label(
            self.window,
            text="Let's configure your bot in a few easy steps.",
            font=('Arial', 10)
        ).pack(pady=5)
        
        # Main frame
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Step 1: Claude API Key
        step1 = ttk.LabelFrame(main_frame, text="Step 1: AI Model API Key", padding="15")
        step1.pack(fill=tk.X, pady=10)
        
        ttk.Label(step1, text="Claude API Key:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Label(
            step1,
            text="Get your key from: console.anthropic.com",
            font=('Arial', 8),
            foreground="gray"
        ).grid(row=1, column=0, columnspan=2, sticky=tk.W)
        
        self.claude_key_var = tk.StringVar(value=os.getenv('ANTHROPIC_API_KEY', ''))
        self.claude_show_var = tk.BooleanVar(value=False)
        
        key_frame = ttk.Frame(step1)
        key_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.claude_entry = ttk.Entry(
            key_frame,
            textvariable=self.claude_key_var,
            width=50,
            show='*'
        )
        self.claude_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Checkbutton(
            key_frame,
            text="Show",
            variable=self.claude_show_var,
            command=self.toggle_claude_visibility
        ).pack(side=tk.LEFT)
        
        # Step 2: Telegram Bot
        step2 = ttk.LabelFrame(main_frame, text="Step 2: Telegram Bot Token", padding="15")
        step2.pack(fill=tk.X, pady=10)
        
        ttk.Label(step2, text="Bot Token:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Label(
            step2,
            text="Get your token from @BotFather on Telegram",
            font=('Arial', 8),
            foreground="gray"
        ).grid(row=1, column=0, columnspan=2, sticky=tk.W)
        
        self.tg_token_var = tk.StringVar(value=os.getenv('TELEGRAM_BOT_TOKEN_MAIN', ''))
        ttk.Entry(step2, textvariable=self.tg_token_var, width=50).grid(
            row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5
        )
        
        ttk.Label(step2, text="Bot Name (optional):").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.tg_name_var = tk.StringVar(value="MAIN")
        ttk.Entry(step2, textvariable=self.tg_name_var, width=20).grid(
            row=3, column=1, sticky=tk.W, pady=5
        )
        
        # Step 3: Optional Discord
        step3 = ttk.LabelFrame(main_frame, text="Step 3: Discord (Optional)", padding="15")
        step3.pack(fill=tk.X, pady=10)
        
        ttk.Label(step3, text="Discord Bot Token (leave empty to skip):").grid(
            row=0, column=0, sticky=tk.W, pady=5
        )
        
        self.discord_token_var = tk.StringVar(value='')
        ttk.Entry(step3, textvariable=self.discord_token_var, width=50).grid(
            row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5
        )
        
        ttk.Label(step3, text="Bot Name:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.discord_name_var = tk.StringVar(value="MAIN")
        ttk.Entry(step3, textvariable=self.discord_name_var, width=20).grid(
            row=2, column=1, sticky=tk.W, pady=5
        )
        
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=20)
        
        ttk.Button(
            btn_frame,
            text="Save & Continue",
            command=self.save_and_continue,
            width=20
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            btn_frame,
            text="Skip (Use Existing)",
            command=self.skip_setup,
            width=20
        ).pack(side=tk.LEFT, padx=5)
    
    def toggle_claude_visibility(self):
        """Toggle Claude key visibility"""
        self.claude_entry.config(show='' if self.claude_show_var.get() else '*')
    
    def save_and_continue(self):
        """Save configuration and close wizard"""
        env_file = Path('.env')
        
        # Validate
        claude_key = self.claude_key_var.get().strip()
        tg_token = self.tg_token_var.get().strip()
        
        if not claude_key:
            messagebox.showerror("Required", "Claude API key is required!")
            return
        
        if not tg_token:
            response = messagebox.askyesno(
                "No Telegram Token",
                "No Telegram token provided. Continue anyway?\n\n"
                "(You can add it later in Config tab)"
            )
            if not response:
                return
        
        # Save to .env
        set_key(env_file, 'ANTHROPIC_API_KEY', claude_key)
        
        if tg_token:
            tg_name = self.tg_name_var.get().strip().upper() or 'MAIN'
            set_key(env_file, f'TELEGRAM_BOT_TOKEN_{tg_name}', tg_token)
        
        # Optional Discord
        discord_token = self.discord_token_var.get().strip()
        if discord_token:
            discord_name = self.discord_name_var.get().strip().upper() or 'MAIN'
            set_key(env_file, f'DISCORD_BOT_TOKEN_{discord_name}', discord_token)
        
        # Save model config
        set_key(env_file, 'BOT_MODEL', 'claude-sonnet-4-20250514')
        
        messagebox.showinfo("Success", "Configuration saved!\n\nYou can now start your bots.")
        
        self.setup_complete = True
        self.window.destroy()
    
    def skip_setup(self):
        """Skip setup"""
        self.setup_complete = False
        self.window.destroy()


class BotManagerGUI:
    """Main bot manager GUI"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Auto Finance Bot Manager")
        self.root.geometry("950x800")
        
        # State
        self.running_bots = {}
        self.log_queue = queue.Queue()
        self.scraper = SelectiveScraper()
        self.scheduler = UpdateScheduler()
        self.scheduler_enabled = False
        
        # Check if setup needed
        self.check_first_time_setup()
        
        # Setup GUI
        self.setup_gui()
        self.setup_logging()
        self.update_logs()
    
    def check_first_time_setup(self):
        """Check if first-time setup is needed"""
        env_file = Path('.env')
        
        # Check if .env exists and has required keys
        needs_setup = False
        
        if not env_file.exists():
            needs_setup = True
        else:
            claude_key = os.getenv('ANTHROPIC_API_KEY')
            if not claude_key or claude_key == 'your-claude-key-here':
                needs_setup = True
        
        if needs_setup:
            wizard = SetupWizard(self.root)
            self.root.wait_window(wizard.window)
            
            # Reload environment
            load_dotenv(override=True)
    
    def setup_gui(self):
        """Setup main GUI"""
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tabs
        self.bots_tab = ttk.Frame(self.notebook)
        self.config_tab = ttk.Frame(self.notebook)
        self.updates_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.bots_tab, text="🤖 Bots")
        self.notebook.add(self.config_tab, text="⚙️ Configuration")
        self.notebook.add(self.updates_tab, text="🔄 Data Updates")
        
        # Setup each tab
        self.setup_bots_tab()
        self.setup_configuration_tab()
        self.setup_updates_tab()
    
    def setup_bots_tab(self):
        """Setup bots control tab"""
        # Get all configured bots
        all_bots = PlatformConfig.get_available_bots()
        
        # Group by platform
        platforms = {}
        for bot in all_bots:
            platform = bot['platform']
            if platform not in platforms:
                platforms[platform] = []
            platforms[platform].append(bot)
        
        # Create section for each platform
        for i, (platform_key, bots) in enumerate(platforms.items()):
            platform_info = PlatformConfig.get_platform_info(platform_key)
            platform_name = platform_info['name']
            
            frame = ttk.LabelFrame(
                self.bots_tab,
                text=f"{platform_name} Bots ({len(bots)})",
                padding="15"
            )
            frame.pack(fill=tk.X, padx=10, pady=10)
            
            # Each bot
            for bot in bots:
                self.create_bot_control(frame, bot)
        
        # Logs at bottom
        log_frame = ttk.LabelFrame(self.bots_tab, text="Activity Logs", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=12, font=('Consolas', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        ttk.Button(log_frame, text="Clear Logs", command=self.clear_logs).pack(pady=5)
    
    def create_bot_control(self, parent, bot_config):
        """Create control panel for a single bot"""
        bot_id = bot_config['id']
        
        bot_frame = ttk.Frame(parent)
        bot_frame.pack(fill=tk.X, pady=8)
        
        # Left: Info
        info_frame = ttk.Frame(bot_frame)
        info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(
            info_frame,
            text=bot_config['bot_name'].capitalize(),
            font=('Arial', 11, 'bold')
        ).pack(side=tk.LEFT, padx=5)
        
        status_label = ttk.Label(info_frame, text="●", foreground="red", font=('Arial', 16))
        status_label.pack(side=tk.LEFT, padx=5)
        
        status_text = ttk.Label(info_frame, text="Stopped", foreground="gray")
        status_text.pack(side=tk.LEFT, padx=5)
        
        # Store references
        if not hasattr(self, 'bot_status'):
            self.bot_status = {}
        self.bot_status[bot_id] = {'icon': status_label, 'text': status_text}
        
        # Right: Buttons
        btn_frame = ttk.Frame(bot_frame)
        btn_frame.pack(side=tk.RIGHT)
        
        start_btn = ttk.Button(btn_frame, text="Start", command=lambda: self.start_bot(bot_config), width=12)
        start_btn.pack(side=tk.LEFT, padx=3)
        
        stop_btn = ttk.Button(btn_frame, text="Stop", command=lambda: self.stop_bot(bot_config),
                             width=12, state=tk.DISABLED)
        stop_btn.pack(side=tk.LEFT, padx=3)
        
        if not hasattr(self, 'bot_buttons'):
            self.bot_buttons = {}
        self.bot_buttons[bot_id] = {'start': start_btn, 'stop': stop_btn}
    
    def setup_configuration_tab(self):
        """Setup configuration tab with input fields"""
        # Scrollable frame
        canvas = tk.Canvas(self.config_tab)
        scrollbar = ttk.Scrollbar(self.config_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # AI Model Section
        ai_frame = ttk.LabelFrame(scrollable_frame, text="AI Model Configuration", padding="15")
        ai_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(ai_frame, text="Claude API Key:", font=('Arial', 9, 'bold')).grid(
            row=0, column=0, sticky=tk.W, pady=5
        )
        
        key_container = ttk.Frame(ai_frame)
        key_container.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        self.claude_config_var = tk.StringVar(value=os.getenv('ANTHROPIC_API_KEY', ''))
        self.claude_show_config = tk.BooleanVar(value=False)
        
        self.claude_config_entry = ttk.Entry(key_container, textvariable=self.claude_config_var,
                                            width=60, show='*')
        self.claude_config_entry.grid(row=0, column=0, padx=5)
        
        ttk.Checkbutton(key_container, text="Show", variable=self.claude_show_config,
                       command=self.toggle_claude_config_visibility).grid(row=0, column=1)
        
        ttk.Button(ai_frame, text="Save API Key", command=self.save_claude_config).grid(
            row=2, column=0, sticky=tk.W, pady=5
        )
        
        # Telegram Section
        self.setup_platform_config_section(scrollable_frame, 'telegram', 'Telegram')
        
        # Discord Section
        self.setup_platform_config_section(scrollable_frame, 'discord', 'Discord')
        
        # Slack Section
        self.setup_platform_config_section(scrollable_frame, 'slack', 'Slack')
    
    def setup_platform_config_section(self, parent, platform_key, platform_name):
        """Setup configuration section for a platform"""
        frame = ttk.LabelFrame(parent, text=f"{platform_name} Bots", padding="15")
        frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Show existing bots
        all_bots = PlatformConfig.get_available_bots()
        platform_bots = [b for b in all_bots if b['platform'] == platform_key]
        
        if platform_bots:
            ttk.Label(frame, text="Configured:", font=('Arial', 9, 'bold')).grid(
                row=0, column=0, columnspan=4, sticky=tk.W, pady=(0, 5)
            )
            
            for i, bot in enumerate(platform_bots, 1):
                ttk.Label(frame, text=f"• {bot['bot_name'].capitalize()}:").grid(
                    row=i, column=0, sticky=tk.W, padx=(10, 5)
                )
                ttk.Label(frame, text=bot['token'][:25] + '...', foreground="gray", font=('Courier', 8)).grid(
                    row=i, column=1, sticky=tk.W
                )
                ttk.Button(
                    frame,
                    text="Remove",
                    command=lambda b=bot: self.remove_bot_token(b),
                    width=10
                ).grid(row=i, column=2, padx=5)
            
            sep_row = len(platform_bots) + 1
            ttk.Separator(frame, orient='horizontal').grid(
                row=sep_row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=10
            )
            add_row = sep_row + 1
        else:
            add_row = 0
        
        # Add new bot
        ttk.Label(frame, text="Add New Bot:", font=('Arial', 9, 'bold')).grid(
            row=add_row, column=0, columnspan=4, sticky=tk.W, pady=(0, 5)
        )
        
        ttk.Label(frame, text="Name:").grid(row=add_row+1, column=0, sticky=tk.W, padx=(10, 0))
        name_var = tk.StringVar()
        ttk.Entry(frame, textvariable=name_var, width=15).grid(row=add_row+1, column=1, sticky=tk.W, padx=5)
        
        ttk.Label(frame, text="Token:").grid(row=add_row+2, column=0, sticky=tk.W, padx=(10, 0))
        token_var = tk.StringVar()
        ttk.Entry(frame, textvariable=token_var, width=40).grid(
            row=add_row+2, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=5
        )
        
        ttk.Button(
            frame,
            text="Add Bot",
            command=lambda: self.add_bot_token(platform_key, name_var, token_var)
        ).grid(row=add_row+2, column=3, padx=5)
    
    def setup_updates_tab(self):
        """Setup data updates tab"""
        # Manual updates
        manual_frame = ttk.LabelFrame(self.updates_tab, text="Manual Updates", padding="15")
        manual_frame.pack(fill=tk.X, padx=10, pady=10)
        
        btn_grid = ttk.Frame(manual_frame)
        btn_grid.pack()
        
        ttk.Button(
            btn_grid,
            text="Quick Update\n(Website - 5-10 min)",
            command=self.quick_update,
            width=22
        ).grid(row=0, column=0, padx=5, pady=5)
        
        ttk.Button(
            btn_grid,
            text="Full Update\n(All Sources - 20 min)",
            command=self.full_update,
            width=22
        ).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(
            btn_grid,
            text="Blog Only\n(3-5 min)",
            command=self.blog_update,
            width=22
        ).grid(row=1, column=0, padx=5, pady=5)
        
        ttk.Button(
            btn_grid,
            text="Docs Only\n(3-5 min)",
            command=self.docs_update,
            width=22
        ).grid(row=1, column=1, padx=5, pady=5)
        
        # Update history
        history_frame = ttk.LabelFrame(self.updates_tab, text="Update History", padding="15")
        history_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.last_update_label = ttk.Label(history_frame, text="Loading...", justify=tk.LEFT)
        self.last_update_label.pack(anchor=tk.W)
        
        self.update_last_update_display()
        
        # Scheduler
        sched_frame = ttk.LabelFrame(self.updates_tab, text="Automated Scheduler", padding="15")
        sched_frame.pack(fill=tk.X, padx=10, pady=10)
        
        sched_controls = ttk.Frame(sched_frame)
        sched_controls.pack(fill=tk.X)
        
        ttk.Label(sched_controls, text="Daily at:").grid(row=0, column=0, padx=5)
        self.daily_time_var = tk.StringVar(value="03:00")
        ttk.Entry(sched_controls, textvariable=self.daily_time_var, width=8).grid(row=0, column=1, padx=5)
        
        ttk.Label(sched_controls, text="Type:").grid(row=0, column=2, padx=5)
        self.daily_type_var = tk.StringVar(value="quick")
        ttk.Combobox(sched_controls, textvariable=self.daily_type_var,
                    values=["quick", "full"], width=10, state='readonly').grid(row=0, column=3, padx=5)
        
        self.scheduler_button = ttk.Button(sched_controls, text="Enable", command=self.toggle_scheduler, width=12)
        self.scheduler_button.grid(row=0, column=4, padx=5)
        
        self.scheduler_status = ttk.Label(sched_controls, text="Disabled", foreground="gray")
        self.scheduler_status.grid(row=0, column=5, padx=5)
        
        self.next_run_label = ttk.Label(sched_frame, text="Next run: N/A", font=('Arial', 9))
        self.next_run_label.pack(anchor=tk.W, pady=10)
    
    # Configuration methods
    def toggle_claude_config_visibility(self):
        """Toggle Claude key visibility in config"""
        self.claude_config_entry.config(show='' if self.claude_show_config.get() else '*')
    
    def save_claude_config(self):
        """Save Claude key from config tab"""
        key = self.claude_config_var.get().strip()
        if not key:
            messagebox.showerror("Error", "Please enter a valid API key")
            return
        
        env_file = Path('.env')
        set_key(env_file, 'ANTHROPIC_API_KEY', key)
        
        self.log("[OK] Claude API key saved")
        messagebox.showinfo("Saved", "Claude API key updated!")
    
    def add_bot_token(self, platform, name_var, token_var):
        """Add new bot token"""
        name = name_var.get().strip().upper()
        token = token_var.get().strip()
        
        if not name or not token:
            messagebox.showerror("Error", "Please provide both name and token")
            return
        
        env_key = f"{platform.upper()}_BOT_TOKEN_{name}"
        env_file = Path('.env')
        set_key(env_file, env_key, token)
        
        self.log(f"[OK] Added: {env_key}")
        messagebox.showinfo("Success", f"Bot added!\n\n{env_key}\n\nRestart GUI to see it in the Bots tab.")
        
        name_var.set('')
        token_var.set('')
    
    def remove_bot_token(self, bot_config):
        """Remove a bot token"""
        response = messagebox.askyesno(
            "Confirm",
            f"Remove {bot_config['display_name']}?\n\n"
            f"This will delete the token from .env"
        )
        
        if not response:
            return
        
        # Read .env
        env_file = Path('.env')
        with open(env_file, 'r') as f:
            lines = f.readlines()
        
        # Remove the line with this token
        key_to_remove = bot_config['token_env_key']
        new_lines = [line for line in lines if not line.startswith(f"{key_to_remove}=")]
        
        # Write back
        with open(env_file, 'w') as f:
            f.writelines(new_lines)
        
        self.log(f"[OK] Removed: {key_to_remove}")
        messagebox.showinfo("Removed", f"{bot_config['display_name']} removed.\n\nRestart GUI to update display.")
    
    # Bot control methods
    def start_bot(self, bot_config):
        """Start a bot"""
        bot_id = bot_config['id']
        
        if bot_id in self.running_bots:
            messagebox.showinfo("Already Running", f"{bot_config['display_name']} is already running!")
            return
        
        # Check support
        if bot_config.get('status') != 'active':
            messagebox.showerror("Not Supported", f"{bot_config['platform_name']} is not yet supported.")
            return
        
        self.log(f"Starting {bot_config['display_name']}...")
        
        # Update UI
        if bot_id in self.bot_status:
            self.bot_status[bot_id]['icon'].config(foreground="orange")
            self.bot_status[bot_id]['text'].config(text="Starting...", foreground="orange")
        if bot_id in self.bot_buttons:
            self.bot_buttons[bot_id]['start'].config(state=tk.DISABLED)
            self.bot_buttons[bot_id]['stop'].config(state=tk.NORMAL)
        
        def run_bot():
            try:
                bot = BotLauncher.launch_bot(bot_config)
                self.running_bots[bot_id] = {'bot': bot, 'config': bot_config}
                
                if bot_id in self.bot_status:
                    self.bot_status[bot_id]['icon'].config(foreground="green")
                    self.bot_status[bot_id]['text'].config(text="Running", foreground="green")
                
                self.log(f"[OK] {bot_config['display_name']} started")
                bot.run()
            except Exception as e:
                self.log(f"[ERROR] Failed: {e}")
                if bot_id in self.bot_status:
                    self.bot_status[bot_id]['icon'].config(foreground="red")
                    self.bot_status[bot_id]['text'].config(text="Error", foreground="red")
                if bot_id in self.bot_buttons:
                    self.bot_buttons[bot_id]['start'].config(state=tk.NORMAL)
                    self.bot_buttons[bot_id]['stop'].config(state=tk.DISABLED)
                if bot_id in self.running_bots:
                    del self.running_bots[bot_id]
        
        threading.Thread(target=run_bot, daemon=True).start()
    
    def stop_bot(self, bot_config):
        """Stop a bot"""
        bot_id = bot_config['id']
        
        if bot_id not in self.running_bots:
            return
        
        # Try to stop the bot gracefully
        bot_instance = self.running_bots[bot_id].get('bot')
        if bot_instance and hasattr(bot_instance, 'stop'):
            try:
                bot_instance.stop()
            except:
                pass
        
        del self.running_bots[bot_id]
        
        if bot_id in self.bot_status:
            self.bot_status[bot_id]['icon'].config(foreground="red")
            self.bot_status[bot_id]['text'].config(text="Stopped", foreground="gray")
        if bot_id in self.bot_buttons:
            self.bot_buttons[bot_id]['start'].config(state=tk.NORMAL)
            self.bot_buttons[bot_id]['stop'].config(state=tk.DISABLED)
        
        self.log(f"[OK] {bot_config['display_name']} stopped (may take a few seconds)")
    
    # Update methods
    def quick_update(self):
        """Quick update"""
        if messagebox.askyesno("Quick Update", "Scrape website for fresh data?\n\nTime: ~5-10 min"):
            self.log("Starting quick update...")
            threading.Thread(target=self._run_update, args=('quick',), daemon=True).start()
    
    def full_update(self):
        """Full update"""
        if messagebox.askyesno("Full Update", "Scrape all sources?\n\nTime: ~20 min"):
            self.log("Starting full update...")
            threading.Thread(target=self._run_update, args=('full',), daemon=True).start()
    
    def blog_update(self):
        """Blog update"""
        if messagebox.askyesno("Blog Update", "Scrape blog?\n\nTime: ~3-5 min"):
            self.log("Starting blog update...")
            threading.Thread(target=self._run_update, args=('blog',), daemon=True).start()
    
    def docs_update(self):
        """Docs update"""
        if messagebox.askyesno("Docs Update", "Scrape docs?\n\nTime: ~3-5 min"):
            self.log("Starting docs update...")
            threading.Thread(target=self._run_update, args=('docs',), daemon=True).start()
    
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
                messagebox.showinfo("Success", f"Update completed!")
            else:
                messagebox.showerror("Failed", "Update failed")
        except Exception as e:
            self.log(f"[ERROR] {e}")
            messagebox.showerror("Error", str(e))
    
    def update_last_update_display(self):
        """Update timestamps"""
        last_updates = self.scraper.get_last_update_info()
        
        text = []
        for source, timestamp in last_updates.items():
            if timestamp:
                from datetime import datetime
                try:
                    dt = datetime.fromisoformat(timestamp)
                    time_str = dt.strftime('%Y-%m-%d %H:%M')
                    text.append(f"{source.capitalize()}: {time_str}")
                except:
                    text.append(f"{source.capitalize()}: {timestamp}")
        
        self.last_update_label.config(text="\n".join(text) if text else "No updates yet")
    
    def toggle_scheduler(self):
        """Toggle scheduler"""
        if not self.scheduler_enabled:
            self.scraper.update_schedule({
                'enabled': True,
                'daily_time': self.daily_time_var.get(),
                'daily_type': self.daily_type_var.get()
            })
            
            self.scheduler.load_config()
            self.scheduler.start()
            
            self.scheduler_enabled = True
            self.scheduler_button.config(text="Disable")
            self.scheduler_status.config(text="Active", foreground="green")
            self.log("[OK] Scheduler enabled")
        else:
            self.scheduler.stop()
            self.scraper.update_schedule({'enabled': False})
            
            self.scheduler_enabled = False
            self.scheduler_button.config(text="Enable")
            self.scheduler_status.config(text="Disabled", foreground="gray")
            self.log("Scheduler disabled")
    
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
        queue_handler = QueueHandler(self.log_queue)
        queue_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        logger.addHandler(queue_handler)
    
    def update_logs(self):
        """Update logs"""
        try:
            while True:
                msg = self.log_queue.get_nowait()
                self.log_text.insert(tk.END, msg + '\n')
                self.log_text.see(tk.END)
        except queue.Empty:
            pass
        
        if self.scheduler_enabled:
            next_run = self.scheduler.get_next_run()
            if next_run:
                from datetime import datetime
                self.next_run_label.config(text=f"Next run: {next_run.strftime('%Y-%m-%d %H:%M')}")
        
        self.root.after(100, self.update_logs)
    
    def clear_logs(self):
        """Clear logs"""
        self.log_text.delete(1.0, tk.END)
    
    def log(self, message):
        """Log message"""
        self.log_queue.put(message)


def main():
    """Main entry"""
    root = tk.Tk()
    app = BotManagerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

