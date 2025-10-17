"""
Auto Finance Bot Manager - Clean Professional GUI
Modern, intuitive interface for managing multi-platform bots
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


class ModernGUI:
    """Clean, professional bot manager interface"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Auto Finance Bot Manager")
        self.root.geometry("1100x750")
        self.root.minsize(900, 600)
        
        # Style
        self.setup_style()
        
        # State
        self.running_bots = {}
        self.log_queue = queue.Queue()
        self.scraper = SelectiveScraper()
        self.scheduler = UpdateScheduler()
        self.conversation_storage = ConversationStorage()
        
        # Handle close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Build UI
        self.build_ui()
        self.setup_logging()
        self.update_logs()
    
    def setup_style(self):
        """Setup modern styling"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Colors
        self.colors = {
            'bg': '#f0f0f0',
            'fg': '#2c3e50',
            'accent': '#3498db',
            'success': '#27ae60',
            'warning': '#f39c12',
            'danger': '#e74c3c',
            'card_bg': '#ffffff'
        }
        
        # Configure styles
        style.configure('Card.TFrame', background=self.colors['card_bg'], relief='flat')
        style.configure('Title.TLabel', font=('Segoe UI', 16, 'bold'), foreground=self.colors['fg'])
        style.configure('Subtitle.TLabel', font=('Segoe UI', 11, 'bold'), foreground=self.colors['fg'])
        style.configure('Body.TLabel', font=('Segoe UI', 9), foreground=self.colors['fg'])
        style.configure('Success.TLabel', foreground=self.colors['success'], font=('Segoe UI', 9, 'bold'))
        style.configure('Warning.TLabel', foreground=self.colors['warning'], font=('Segoe UI', 9, 'bold'))
        
        self.root.configure(bg=self.colors['bg'])
    
    def build_ui(self):
        """Build main UI"""
        # Header
        header = ttk.Frame(self.root)
        header.pack(fill=tk.X, padx=20, pady=15)
        
        ttk.Label(header, text="Auto Finance Bot Manager", style='Title.TLabel').pack(side=tk.LEFT)
        
        # Status indicator in header
        self.header_status = ttk.Label(header, text="● No bots running", foreground='gray', font=('Segoe UI', 9))
        self.header_status.pack(side=tk.RIGHT)
        
        # Main content area with sidebar
        content = ttk.Frame(self.root)
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Sidebar (left)
        sidebar = ttk.Frame(content, width=220)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))
        sidebar.pack_propagate(False)
        
        # Main panel (right)
        self.main_panel = ttk.Frame(content)
        self.main_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create all view frames once
        self.bots_frame = ttk.Frame(self.main_panel)
        self.conversations_frame = ttk.Frame(self.main_panel)
        self.analytics_frame = ttk.Frame(self.main_panel)
        self.settings_frame = ttk.Frame(self.main_panel)
        self.updates_frame = ttk.Frame(self.main_panel)
        self.prompt_frame = ttk.Frame(self.main_panel)
        
        # Build all views
        self.build_bots_view()
        self.build_conversations_view()
        self.build_analytics_view()
        self.build_settings_view()
        self.build_updates_view()
        self.build_prompt_view()
        
        # Build sidebar
        self.build_sidebar(sidebar)
        
        # Show default view
        self.show_view(self.bots_frame)
    
    def build_sidebar(self, parent):
        """Build navigation sidebar"""
        # Title
        ttk.Label(parent, text="Navigation", style='Subtitle.TLabel').pack(pady=(0, 15))
        
        # Navigation buttons
        nav_buttons = [
            ("🤖 Bots", lambda: self.show_view(self.bots_frame)),
            ("📚 Conversations", lambda: [self.show_view(self.conversations_frame), self.refresh_conversations()]),
            ("📊 Analytics", lambda: [self.show_view(self.analytics_frame), self.refresh_analytics()]),
            ("⚙️ Settings", lambda: self.show_view(self.settings_frame)),
            ("🔄 Updates", lambda: [self.show_view(self.updates_frame), self.refresh_update_history()]),
            ("📝 Prompt", lambda: self.show_view(self.prompt_frame))
        ]
        
        self.nav_buttons = {}
        for i, (text, command) in enumerate(nav_buttons):
            btn = ttk.Button(
                parent,
                text=text,
                command=command,
                width=22
            )
            btn.pack(pady=2, fill=tk.X)
            self.nav_buttons[text] = btn
        
        # Spacer
        ttk.Frame(parent, height=30).pack()
        
        # Quick actions
        ttk.Label(parent, text="Quick Actions", style='Subtitle.TLabel').pack(pady=(0, 10))
        
        ttk.Button(parent, text="🔄 Quick Update", command=self.quick_update, width=22).pack(pady=2, fill=tk.X)
        ttk.Button(parent, text="🛑 Stop All Bots", command=self.stop_all_bots, width=22).pack(pady=2, fill=tk.X)
    
    def show_view(self, frame_to_show):
        """Show specific view (hide others)"""
        for frame in [self.bots_frame, self.conversations_frame, self.analytics_frame,
                     self.settings_frame, self.updates_frame, self.prompt_frame]:
            frame.pack_forget()
        
        frame_to_show.pack(fill=tk.BOTH, expand=True)
    
    def build_bots_view(self):
        """Build bots control view (once)"""
        parent = self.bots_frame
        
        # Title
        title_frame = ttk.Frame(parent)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(title_frame, text="Platform Bots", style='Title.TLabel').pack(side=tk.LEFT)
        
        # Model selector
        model_frame = ttk.Frame(title_frame)
        model_frame.pack(side=tk.RIGHT)
        
        ttk.Label(model_frame, text="AI Model:", font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=5)
        
        self.selected_model_var = tk.StringVar(value=os.getenv('BOT_MODEL', 'claude-sonnet-4-20250514'))
        
        model_combo = ttk.Combobox(
            model_frame,
            textvariable=self.selected_model_var,
            values=["claude-sonnet-4-20250514", "claude-3-5-haiku-20241022", "gpt-4o", "gpt-4o-mini"],
            state='readonly',
            width=28
        )
        model_combo.pack(side=tk.LEFT)
        model_combo.bind('<<ComboboxSelected>>', self.on_model_changed)
        
        # Get bots by platform
        all_bots = PlatformConfig.get_available_bots()
        
        platforms = {}
        for bot in all_bots:
            if bot['platform'] not in platforms:
                platforms[bot['platform']] = []
            platforms[bot['platform']].append(bot)
        
        # Create card for each platform
        for platform_key, bots in platforms.items():
            self.create_platform_card(parent, platform_key, bots)
        
        # Logs
        log_card = ttk.LabelFrame(parent, text="Activity Logs", padding=15)
        log_card.pack(fill=tk.BOTH, expand=True, pady=(15, 0))
        
        self.log_text = scrolledtext.ScrolledText(log_card, wrap=tk.WORD, height=10, font=('Consolas', 9), bg='#1e1e1e', fg='#d4d4d4')
        self.log_text.pack(fill=tk.BOTH, expand=True)
    
    def create_platform_card(self, parent, platform_key, bots):
        """Create a clean card for platform bots"""
        platform_info = PlatformConfig.get_platform_info(platform_key)
        
        card = ttk.LabelFrame(parent, text=f"{platform_info['name']} ({len(bots)})", padding=15)
        card.pack(fill=tk.X, pady=(0, 15))
        
        for bot in bots:
            bot_frame = ttk.Frame(card)
            bot_frame.pack(fill=tk.X, pady=8)
            
            # Left: Bot info
            info_frame = ttk.Frame(bot_frame)
            info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # Bot name
            ttk.Label(info_frame, text=bot['bot_name'].upper(), font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT, padx=(0, 15))
            
            # Status
            bot_id = bot['id']
            if not hasattr(self, 'bot_status'):
                self.bot_status = {}
            
            status_frame = ttk.Frame(info_frame)
            status_frame.pack(side=tk.LEFT)
            
            # Check if bot is actually running
            is_running = bot_id in self.running_bots
            
            status_dot = ttk.Label(
                status_frame, 
                text="●", 
                font=('Arial', 14), 
                foreground='#27ae60' if is_running else '#e74c3c'
            )
            status_dot.pack(side=tk.LEFT, padx=2)
            
            status_text = ttk.Label(
                status_frame, 
                text="Online" if is_running else "Offline", 
                foreground='#27ae60' if is_running else 'gray', 
                font=('Segoe UI', 9)
            )
            status_text.pack(side=tk.LEFT, padx=5)
            
            self.bot_status[bot_id] = {'dot': status_dot, 'text': status_text}
            
            # Right: Buttons
            btn_frame = ttk.Frame(bot_frame)
            btn_frame.pack(side=tk.RIGHT)
            
            start_btn = ttk.Button(
                btn_frame, 
                text="▶ Start", 
                command=lambda b=bot: self.start_bot(b), 
                width=10,
                state=tk.DISABLED if is_running else tk.NORMAL
            )
            start_btn.pack(side=tk.LEFT, padx=3)
            
            stop_btn = ttk.Button(
                btn_frame, 
                text="■ Stop", 
                command=lambda b=bot: self.stop_bot(b), 
                width=10, 
                state=tk.NORMAL if is_running else tk.DISABLED
            )
            stop_btn.pack(side=tk.LEFT, padx=3)
            
            if not hasattr(self, 'bot_buttons'):
                self.bot_buttons = {}
            self.bot_buttons[bot_id] = {'start': start_btn, 'stop': stop_btn}
    
    def build_settings_view(self):
        """Build settings/configuration view (once)"""
        parent = self.settings_frame
        
        ttk.Label(parent, text="Configuration", style='Title.TLabel').pack(anchor=tk.W, pady=(0, 20))
        
        # API Keys section
        api_card = ttk.LabelFrame(parent, text="API Keys", padding=20)
        api_card.pack(fill=tk.X, pady=(0, 15))
        
        # Claude
        self.create_api_key_field(api_card, "Claude (Anthropic)", "ANTHROPIC_API_KEY", row=0)
        
        # OpenAI
        self.create_api_key_field(api_card, "OpenAI", "OPENAI_API_KEY", row=1)
        
        # Platform tokens
        platforms = ['Telegram', 'Discord', 'Slack']
        for i, platform in enumerate(platforms):
            self.create_platform_token_section(platform, i)
    
    def create_api_key_field(self, parent, label, env_key, row):
        """Create API key input field"""
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=10)
        parent.columnconfigure(0, weight=1)
        
        ttk.Label(frame, text=f"{label}:", font=('Segoe UI', 9, 'bold'), width=15).pack(side=tk.LEFT)
        
        var = tk.StringVar(value=os.getenv(env_key, ''))
        entry = ttk.Entry(frame, textvariable=var, width=50, show='*')
        entry.pack(side=tk.LEFT, padx=10)
        
        show_var = tk.BooleanVar()
        ttk.Checkbutton(frame, text="Show", variable=show_var, 
                       command=lambda: entry.config(show='' if show_var.get() else '*')).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(frame, text="Save", command=lambda: self.save_api_key(env_key, var.get()), width=8).pack(side=tk.LEFT)
    
    def create_platform_token_section(self, platform_name, index):
        """Create section for platform tokens"""
        card = ttk.LabelFrame(self.main_panel, text=f"{platform_name} Bots", padding=15)
        card.pack(fill=tk.X, pady=(0, 10))
        
        # Show existing
        all_bots = PlatformConfig.get_available_bots()
        platform_bots = [b for b in all_bots if b['platform_name'] == platform_name]
        
        if platform_bots:
            for bot in platform_bots:
                bot_row = ttk.Frame(card)
                bot_row.pack(fill=tk.X, pady=5)
                
                ttk.Label(bot_row, text=f"✓ {bot['bot_name'].capitalize()}", foreground='green').pack(side=tk.LEFT, padx=10)
                ttk.Label(bot_row, text=bot['token'][:25] + '...', foreground='gray', font=('Courier', 8)).pack(side=tk.LEFT)
        
        # Add new
        add_frame = ttk.Frame(card)
        add_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(add_frame, text="Add new:", font=('Segoe UI', 9)).grid(row=0, column=0, sticky=tk.W)
        
        name_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=name_var, width=12).grid(row=0, column=1, padx=5)
        
        token_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=token_var, width=40).grid(row=0, column=2, padx=5)
        
        ttk.Button(add_frame, text="+ Add", 
                  command=lambda: self.add_bot_token(platform_name.lower(), name_var, token_var)).grid(row=0, column=3, padx=5)
    
    def build_updates_view(self):
        """Build data updates view (once)"""
        parent = self.updates_frame
        
        ttk.Label(parent, text="Data Updates", style='Title.TLabel').pack(anchor=tk.W, pady=(0, 20))
        
        # Update buttons grid
        update_card = ttk.LabelFrame(parent, text="Manual Updates", padding=20)
        update_card.pack(fill=tk.X, pady=(0, 15))
        
        grid = ttk.Frame(update_card)
        grid.pack()
        
        updates = [
            ("Quick Update", "Website only\n~5-10 minutes", self.quick_update),
            ("Full Update", "All sources\n~20 minutes", self.full_update),
            ("Blog Only", "Blog posts\n~3-5 minutes", self.blog_update),
            ("Docs Only", "Documentation\n~3-5 minutes", self.docs_update)
        ]
        
        for i, (title, desc, cmd) in enumerate(updates):
            row, col = i // 2, i % 2
            
            btn_frame = ttk.Frame(grid)
            btn_frame.grid(row=row, column=col, padx=10, pady=10)
            
            ttk.Button(btn_frame, text=title, command=cmd, width=18).pack()
            ttk.Label(btn_frame, text=desc, foreground='gray', font=('Segoe UI', 8), justify=tk.CENTER).pack(pady=(5, 0))
        
        # Last update info
        info_card = ttk.LabelFrame(parent, text="Update History", padding=15)
        info_card.pack(fill=tk.X, pady=(0, 15))
        
        self.last_update_label = ttk.Label(info_card, text="Loading...", font=('Segoe UI', 9))
        self.last_update_label.pack(anchor=tk.W)
        self.update_last_update_display()
        
        # Scheduler
        sched_card = ttk.LabelFrame(parent, text="Automated Scheduler", padding=15)
        sched_card.pack(fill=tk.X)
        
        sched_ctrl = ttk.Frame(sched_card)
        sched_ctrl.pack(fill=tk.X)
        
        ttk.Label(sched_ctrl, text="Daily at:").grid(row=0, column=0, padx=5, sticky=tk.W)
        self.daily_time_var = tk.StringVar(value="03:00")
        ttk.Entry(sched_ctrl, textvariable=self.daily_time_var, width=8).grid(row=0, column=1, padx=5)
        
        ttk.Label(sched_ctrl, text="Type:").grid(row=0, column=2, padx=5)
        self.daily_type_var = tk.StringVar(value="quick")
        ttk.Combobox(sched_ctrl, textvariable=self.daily_type_var, values=["quick", "full"], 
                    width=10, state='readonly').grid(row=0, column=3, padx=5)
        
        self.scheduler_btn = ttk.Button(sched_ctrl, text="Enable", command=self.toggle_scheduler, width=10)
        self.scheduler_btn.grid(row=0, column=4, padx=10)
        
        self.scheduler_status = ttk.Label(sched_ctrl, text="Disabled", foreground='gray')
        self.scheduler_status.grid(row=0, column=5, padx=5)
    
    def build_prompt_view(self):
        """Build system prompt editor (once)"""
        parent = self.prompt_frame
        
        ttk.Label(parent, text="Bot Personality", style='Title.TLabel').pack(anchor=tk.W, pady=(0, 10))
        ttk.Label(parent, text="Customize how your bot responds", foreground='gray').pack(anchor=tk.W, pady=(0, 20))
        
        # Presets
        preset_card = ttk.LabelFrame(parent, text="Personality Presets", padding=15)
        preset_card.pack(fill=tk.X, pady=(0, 15))
        
        preset_frame = ttk.Frame(preset_card)
        preset_frame.pack(fill=tk.X)
        
        self.prompt_preset_var = tk.StringVar(value="default")
        
        presets = [
            ("Default", "Casual, concise, friendly"),
            ("Technical", "Detailed, precise, expert"),
            ("Beginner", "Simple, patient, teaching"),
            ("Marketing", "Enthusiastic, persuasive")
        ]
        
        for i, (name, desc) in enumerate(presets):
            btn = ttk.Button(
                preset_frame,
                text=f"{name}\n{desc}",
                command=lambda n=name.lower().replace(' ', '_'): self.apply_preset(n),
                width=20
            )
            btn.grid(row=0, column=i, padx=5)
        
        # Editor
        editor_card = ttk.LabelFrame(parent, text="Custom Prompt Editor", padding=15)
        editor_card.pack(fill=tk.BOTH, expand=True)
        
        self.prompt_text = scrolledtext.ScrolledText(editor_card, wrap=tk.WORD, height=18, font=('Consolas', 10))
        self.prompt_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Load current
        self.load_current_prompt()
        
        # Buttons
        btn_frame = ttk.Frame(editor_card)
        btn_frame.pack()
        
        ttk.Button(btn_frame, text="💾 Save Prompt", command=self.save_custom_prompt, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="↺ Reset to Default", command=self.load_current_prompt, width=15).pack(side=tk.LEFT, padx=5)
    
    def build_conversations_view(self):
        """Build conversations browser (once)"""
        parent = self.conversations_frame
        
        ttk.Label(parent, text="Conversation History", style='Title.TLabel').pack(anchor=tk.W, pady=(0, 10))
        
        # Search bar
        search_frame = ttk.Frame(parent)
        search_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(search_frame, text="Search:", font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=5)
        self.conv_search_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.conv_search_var, width=40).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="🔍 Search", command=self.search_conversations).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="↺ Refresh", command=self.load_conversations).pack(side=tk.LEFT, padx=5)
        
        # Content area (split view)
        content = ttk.Frame(parent)
        content.pack(fill=tk.BOTH, expand=True)
        
        # Left: Users list
        users_card = ttk.LabelFrame(content, text="Users", padding=10, width=250)
        users_card.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        users_card.pack_propagate(False)
        
        self.users_listbox = tk.Listbox(users_card, font=('Segoe UI', 9))
        self.users_listbox.pack(fill=tk.BOTH, expand=True)
        self.users_listbox.bind('<<ListboxSelect>>', self.on_user_selected)
        
        # Right: Conversations
        convos_card = ttk.LabelFrame(content, text="Conversations", padding=10)
        convos_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.convos_text = scrolledtext.ScrolledText(convos_card, wrap=tk.WORD, font=('Segoe UI', 9))
        self.convos_text.pack(fill=tk.BOTH, expand=True)
        
        # Actions
        actions = ttk.Frame(parent)
        actions.pack(fill=tk.X, pady=(15, 0))
        
        ttk.Button(actions, text="📤 Export All", command=self.export_all_conversations).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions, text="🎓 Export for Fine-tuning", command=self.export_finetuning).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions, text="📊 View Analytics", command=lambda: self.show_view(self.analytics_frame)).pack(side=tk.LEFT, padx=5)
        
        # Initial load
        self.refresh_conversations()
    
    def refresh_conversations(self):
        """Refresh conversation list"""
        if hasattr(self, 'users_listbox'):
            self.load_conversations()
    
    def load_conversations(self):
        """Load users list"""
        self.users_listbox.delete(0, tk.END)
        
        users = self.conversation_storage.get_all_users()
        for user in users:
            display = f"{user['username']} ({user['total_questions']} msgs)"
            self.users_listbox.insert(tk.END, display)
            self.users_listbox.user_data = users  # Store full data
    
    def on_user_selected(self, event):
        """Load selected user's conversations"""
        selection = self.users_listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        if not hasattr(self.users_listbox, 'user_data'):
            return
        
        user = self.users_listbox.user_data[idx]
        convos = self.conversation_storage.get_user_conversations(user['user_id'], limit=100)
        
        # Display conversations
        self.convos_text.delete(1.0, tk.END)
        self.convos_text.insert(tk.END, f"=== {user['username']}'s Conversations ===\n")
        self.convos_text.insert(tk.END, f"Total: {len(convos)} conversations\n")
        self.convos_text.insert(tk.END, f"Platform: {user['platform']}\n\n")
        
        for i, convo in enumerate(convos, 1):
            self.convos_text.insert(tk.END, f"\n[{convo['timestamp']}] ({convo['chat_type']})\n")
            self.convos_text.insert(tk.END, f"Q: {convo['question']}\n")
            self.convos_text.insert(tk.END, f"A: {convo['answer']}\n")
            if convo['model']:
                self.convos_text.insert(tk.END, f"Model: {convo['model']} | Tokens: {convo['tokens_used'] or 'N/A'}\n")
            self.convos_text.insert(tk.END, "-" * 80 + "\n")
    
    def search_conversations(self):
        """Search conversations by keyword"""
        keyword = self.conv_search_var.get().strip()
        if not keyword:
            self.load_conversations()
            return
        
        results = self.conversation_storage.search_conversations(keyword, limit=100)
        
        self.convos_text.delete(1.0, tk.END)
        self.convos_text.insert(tk.END, f"=== Search Results for '{keyword}' ===\n")
        self.convos_text.insert(tk.END, f"Found: {len(results)} conversations\n\n")
        
        for result in results:
            self.convos_text.insert(tk.END, f"\n[{result['timestamp']}] {result['username']} ({result['platform']})\n")
            self.convos_text.insert(tk.END, f"Q: {result['question']}\n")
            self.convos_text.insert(tk.END, f"A: {result['answer'][:200]}...\n")
            self.convos_text.insert(tk.END, "-" * 80 + "\n")
    
    def export_all_conversations(self):
        """Export all conversations"""
        try:
            output_file = self.conversation_storage.export_to_json()
            self.log(f"[OK] Exported to {output_file}")
            messagebox.showinfo("Exported", f"All conversations exported to:\n{output_file}")
        except Exception as e:
            self.log(f"[ERROR] Export failed: {e}")
            messagebox.showerror("Error", f"Export failed: {e}")
    
    def export_finetuning(self):
        """Export for fine-tuning"""
        try:
            output_file = self.conversation_storage.export_for_finetuning()
            self.log(f"[OK] Exported for fine-tuning to {output_file}")
            messagebox.showinfo("Exported", f"Fine-tuning data exported to:\n{output_file}\n\nUse this with OpenAI fine-tuning!")
        except Exception as e:
            self.log(f"[ERROR] Export failed: {e}")
            messagebox.showerror("Error", f"Export failed: {e}")
    
    def build_analytics_view(self):
        """Build analytics dashboard (once)"""
        parent = self.analytics_frame
        
        ttk.Label(parent, text="Analytics Dashboard", style='Title.TLabel').pack(anchor=tk.W, pady=(0, 10))
        
        # Content container that will be refreshed
        self.analytics_content = ttk.Frame(parent)
        self.analytics_content.pack(fill=tk.BOTH, expand=True)
        
        self.refresh_analytics()
    
    def refresh_analytics(self):
        """Refresh analytics data"""
        # Clear and rebuild analytics content
        if hasattr(self, 'analytics_content'):
            for widget in self.analytics_content.winfo_children():
                widget.destroy()
            
            # Get fresh analytics
            analytics = self.conversation_storage.get_analytics()
            
            # Stats cards
            stats_grid = ttk.Frame(self.analytics_content)
        stats_grid.pack(fill=tk.X, pady=(0, 20))
        
        stats = [
            ("Total Conversations", str(analytics['total_conversations']), "#3498db"),
            ("Unique Users", str(analytics['unique_users']), "#27ae60"),
            ("Total Tokens", f"{analytics['total_tokens_used']:,}", "#9b59b6"),
            ("Last 24h", str(analytics['conversations_24h']), "#e67e22")
        ]
        
        for i, (label, value, color) in enumerate(stats):
            card = ttk.Frame(stats_grid, relief='solid', borderwidth=1)
            card.grid(row=0, column=i, padx=10, pady=10, sticky=(tk.W, tk.E))
            stats_grid.columnconfigure(i, weight=1)
            
            ttk.Label(card, text=value, font=('Segoe UI', 24, 'bold'), foreground=color).pack(pady=(15, 5))
            ttk.Label(card, text=label, font=('Segoe UI', 9), foreground='gray').pack(pady=(0, 15))
        
            # Most active user
            if analytics['most_active_user']:
                active_card = ttk.LabelFrame(self.analytics_content, text="Most Active User", padding=15)
            active_card.pack(fill=tk.X, pady=(0, 15))
            
            ttk.Label(
                active_card,
                text=f"{analytics['most_active_user']} - {analytics['most_active_count']} questions",
                font=('Segoe UI', 11, 'bold')
            ).pack()
        
            # Platform breakdown
            platform_card = ttk.LabelFrame(self.analytics_content, text="By Platform", padding=15)
        platform_card.pack(fill=tk.X, pady=(0, 15))
        
        for platform, count in analytics.get('by_platform', {}).items():
            ttk.Label(
                platform_card,
                text=f"{platform.capitalize()}: {count} conversations",
                font=('Segoe UI', 10)
            ).pack(anchor=tk.W, pady=2)
        
            # Top questions
            top_card = ttk.LabelFrame(self.analytics_content, text="Top Questions", padding=15)
        top_card.pack(fill=tk.BOTH, expand=True)
        
        top_questions = self.conversation_storage.get_top_questions(limit=10)
        
        for i, q in enumerate(top_questions, 1):
            question_text = q['question'][:80] + ('...' if len(q['question']) > 80 else '')
            ttk.Label(
                top_card,
                text=f"{i}. {question_text} ({q['count']}x)",
                font=('Segoe UI', 9)
            ).pack(anchor=tk.W, pady=3)
    
    # Bot control methods
    def start_bot(self, bot_config):
        """Start a bot"""
        bot_id = bot_config['id']
        
        if bot_id in self.running_bots:
            messagebox.showinfo("Already Running", f"{bot_config['display_name']} is already running!")
            return
        
        if bot_config.get('status') != 'active':
            messagebox.showerror("Not Supported", f"{bot_config['platform_name']} support is in progress.")
            return
        
        self.log(f"Starting {bot_config['display_name']}...")
        
        # Update UI
        if bot_id in self.bot_status:
            self.bot_status[bot_id]['dot'].config(foreground='#f39c12')
            self.bot_status[bot_id]['text'].config(text="Starting...", foreground='#f39c12')
        if bot_id in self.bot_buttons:
            self.bot_buttons[bot_id]['start'].config(state=tk.DISABLED)
            self.bot_buttons[bot_id]['stop'].config(state=tk.NORMAL)
        
        def run_bot():
            try:
                bot = BotLauncher.launch_bot(bot_config)
                self.running_bots[bot_id] = {'bot': bot, 'config': bot_config}
                
                # Update UI on main thread
                def update_ui_success():
                    if bot_id in self.bot_status:
                        self.bot_status[bot_id]['dot'].config(foreground='#27ae60')
                        self.bot_status[bot_id]['text'].config(text="Online", foreground='#27ae60')
                    self.update_header_status()
                
                self.root.after(0, update_ui_success)
                self.log(f"[OK] {bot_config['display_name']} started")
                bot.run()
            except Exception as e:
                self.log(f"[ERROR] {e}")
                
                # Update UI on main thread
                def update_ui_error():
                    if bot_id in self.bot_status:
                        self.bot_status[bot_id]['dot'].config(foreground='#e74c3c')
                        self.bot_status[bot_id]['text'].config(text="Error", foreground='#e74c3c')
                    if bot_id in self.bot_buttons:
                        self.bot_buttons[bot_id]['start'].config(state=tk.NORMAL)
                        self.bot_buttons[bot_id]['stop'].config(state=tk.DISABLED)
                    if bot_id in self.running_bots:
                        del self.running_bots[bot_id]
                
                self.root.after(0, update_ui_error)
        
        threading.Thread(target=run_bot, daemon=False).start()
    
    def stop_bot(self, bot_config):
        """Stop a bot"""
        bot_id = bot_config['id']
        
        if bot_id not in self.running_bots:
            return
        
        self.log(f"Stopping {bot_config['display_name']}...")
        
        def stop_in_bg():
            try:
                bot_instance = self.running_bots[bot_id].get('bot')
                if bot_instance and hasattr(bot_instance, 'stop'):
                    bot_instance.stop()
                
                if bot_id in self.running_bots:
                    del self.running_bots[bot_id]
                
                # Update UI on main thread
                def update_ui():
                    if bot_id in self.bot_status:
                        self.bot_status[bot_id]['dot'].config(foreground='#e74c3c')
                        self.bot_status[bot_id]['text'].config(text="Offline", foreground='gray')
                    if bot_id in self.bot_buttons:
                        self.bot_buttons[bot_id]['start'].config(state=tk.NORMAL)
                        self.bot_buttons[bot_id]['stop'].config(state=tk.DISABLED)
                    self.update_header_status()
                
                self.root.after(0, update_ui)
                self.log(f"[OK] {bot_config['display_name']} stopped")
            except Exception as e:
                self.log(f"[ERROR] Stop failed: {e}")
        
        threading.Thread(target=stop_in_bg, daemon=True).start()
    
    def stop_all_bots(self):
        """Stop all running bots"""
        if not self.running_bots:
            messagebox.showinfo("No Bots", "No bots are currently running.")
            return
        
        for bot_id in list(self.running_bots.keys()):
            bot_config = self.running_bots[bot_id]['config']
            self.stop_bot(bot_config)
    
    def update_header_status(self):
        """Update header status indicator"""
        count = len(self.running_bots)
        if count == 0:
            self.header_status.config(text="● No bots running", foreground='gray')
        elif count == 1:
            self.header_status.config(text="● 1 bot running", foreground='#27ae60')
        else:
            self.header_status.config(text=f"● {count} bots running", foreground='#27ae60')
    
    # Utility methods
    def save_api_key(self, key_name, value):
        """Save API key to .env"""
        if not value.strip():
            messagebox.showerror("Error", "Key cannot be empty!")
            return
        
        set_key(Path('.env'), key_name, value.strip())
        self.log(f"[OK] Saved {key_name}")
        messagebox.showinfo("Saved", f"{key_name} updated successfully!")
    
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
        messagebox.showinfo("Success", f"Bot added! Restart GUI to see it.")
        
        name_var.set('')
        token_var.set('')
    
    def on_model_changed(self, event=None):
        """Handle model change"""
        model = self.selected_model_var.get()
        set_key(Path('.env'), 'BOT_MODEL', model)
        self.log(f"Model changed to: {model}")
        messagebox.showinfo("Model Changed", f"Model: {model}\n\nRestart bots for changes to take effect.")
    
    def load_current_prompt(self):
        """Load current prompt"""
        prompt_file = Path("system_prompts.json")
        if prompt_file.exists():
            with open(prompt_file, 'r') as f:
                prompts = json.load(f)
                self.prompt_text.delete(1.0, tk.END)
                self.prompt_text.insert(1.0, prompts.get('default', ''))
    
    def apply_preset(self, preset_name):
        """Apply a preset personality"""
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
        
        self.log("[OK] Prompt saved!")
        messagebox.showinfo("Saved", "System prompt saved!\n\nRestart bots for changes to take effect.")
    
    # Update methods
    def quick_update(self):
        """Quick update"""
        if messagebox.askyesno("Quick Update", "Scrape website for fresh APYs/TVLs?\n\nTime: ~5-10 minutes"):
            self.log("Starting quick update...")
            threading.Thread(target=self._run_update, args=('quick',), daemon=True).start()
    
    def full_update(self):
        """Full update"""
        if messagebox.askyesno("Full Update", "Scrape all sources?\n\nTime: ~20 minutes"):
            self.log("Starting full update...")
            threading.Thread(target=self._run_update, args=('full',), daemon=True).start()
    
    def blog_update(self):
        """Blog update"""
        if messagebox.askyesno("Blog Update", "Scrape blog posts?\n\nTime: ~3-5 minutes"):
            self.log("Starting blog update...")
            threading.Thread(target=self._run_update, args=('blog',), daemon=True).start()
    
    def docs_update(self):
        """Docs update"""
        if messagebox.askyesno("Docs Update", "Scrape documentation?\n\nTime: ~3-5 minutes"):
            self.log("Starting docs update...")
            threading.Thread(target=self._run_update, args=('docs',), daemon=True).start()
    
    def _run_update(self, update_type):
        """Run update in background"""
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
                messagebox.showerror("Failed", "Update failed. Check logs.")
        except Exception as e:
            self.log(f"[ERROR] {e}")
            messagebox.showerror("Error", str(e))
    
    def update_last_update_display(self):
        """Update last update timestamps"""
        last_updates = self.scraper.get_last_update_info()
        
        text = []
        for source, timestamp in last_updates.items():
            if timestamp:
                from datetime import datetime
                try:
                    dt = datetime.fromisoformat(timestamp)
                    time_str = dt.strftime('%Y-%m-%d %H:%M')
                    text.append(f"• {source.capitalize()}: {time_str}")
                except:
                    text.append(f"• {source.capitalize()}: {timestamp}")
        
        if hasattr(self, 'last_update_label'):
            self.last_update_label.config(text="\n".join(text) if text else "No updates yet")
    
    def refresh_update_history(self):
        """Refresh update history display"""
        self.update_last_update_display()
    
    def toggle_scheduler(self):
        """Toggle scheduler"""
        # Implementation same as before
        pass
    
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
        """Update logs from queue"""
        # Keep log history
        if not hasattr(self, 'log_history'):
            self.log_history = []
        
        try:
            while True:
                msg = self.log_queue.get_nowait()
                self.log_history.append(msg)
                
                if hasattr(self, 'log_text') and self.log_text.winfo_exists():
                    self.log_text.insert(tk.END, msg + '\n')
                    self.log_text.see(tk.END)
        except queue.Empty:
            pass
        
        self.root.after(100, self.update_logs)
    
    def log(self, message):
        """Add log message"""
        self.log_queue.put(message)
    
    def on_closing(self):
        """Handle window close"""
        if self.running_bots:
            response = messagebox.askyesno(
                "Bots Running",
                f"{len(self.running_bots)} bot(s) running.\n\nStop all and close?"
            )
            if not response:
                return
            
            self.stop_all_bots()
            self.root.after(1000, self.root.destroy)
        else:
            self.root.destroy()


def main():
    """Main entry"""
    root = tk.Tk()
    app = ModernGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()


