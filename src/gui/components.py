"""Reusable GUI components"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable

from src.gui.styles import STYLES


class LabeledEntry:
    """Entry field with label"""
    
    def __init__(self, parent, label_text: str, width: int = 50, **kwargs):
        self.frame = tk.Frame(parent, bg=STYLES['label']['bg'])
        self.label = tk.Label(self.frame, text=label_text, **STYLES['label'])
        self.entry = tk.Entry(self.frame, width=width, **STYLES['entry'])
        
        self.label.pack(anchor='w', pady=(0, 5))
        self.entry.pack(fill='x')
    
    def pack(self, **kwargs):
        """Pack the component"""
        self.frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """Grid the component"""
        self.frame.grid(**kwargs)
    
    def get(self) -> str:
        """Get entry value"""
        return self.entry.get()
    
    def set(self, value: str):
        """Set entry value"""
        self.entry.delete(0, tk.END)
        self.entry.insert(0, value)
    
    def clear(self):
        """Clear entry"""
        self.entry.delete(0, tk.END)
    
    def disable(self):
        """Disable entry"""
        self.entry.config(state='disabled')
    
    def enable(self):
        """Enable entry"""
        self.entry.config(state='normal')


class LabeledCombobox:
    """Combobox with label"""
    
    def __init__(self, parent, label_text: str, values: list, width: int = 20, **kwargs):
        self.frame = tk.Frame(parent, bg=STYLES['label']['bg'])
        self.label = tk.Label(self.frame, text=label_text, **STYLES['label'])
        self.combobox = ttk.Combobox(self.frame, values=values, width=width, state='readonly')
        self.combobox.current(0)  # Set default to first value
        
        self.label.pack(anchor='w', pady=(0, 5))
        self.combobox.pack(fill='x')
    
    def pack(self, **kwargs):
        """Pack the component"""
        self.frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """Grid the component"""
        self.frame.grid(**kwargs)
    
    def get(self) -> str:
        """Get selected value"""
        return self.combobox.get()
    
    def set(self, value: str):
        """Set selected value"""
        self.combobox.set(value)
    
    def disable(self):
        """Disable combobox"""
        self.combobox.config(state='disabled')
    
    def enable(self):
        """Enable combobox"""
        self.combobox.config(state='readonly')


class LabeledSpinbox:
    """Spinbox with label"""
    
    def __init__(self, parent, label_text: str, from_: int = 1, to: int = 100, 
                 default: int = 10, width: int = 10, **kwargs):
        self.frame = tk.Frame(parent, bg=STYLES['label']['bg'])
        self.label = tk.Label(self.frame, text=label_text, **STYLES['label'])
        self.spinbox = tk.Spinbox(
            self.frame,
            from_=from_,
            to=to,
            width=width,
            **STYLES['entry']
        )
        self.spinbox.delete(0, tk.END)
        self.spinbox.insert(0, str(default))
        
        self.label.pack(anchor='w', pady=(0, 5))
        self.spinbox.pack(fill='x')
    
    def pack(self, **kwargs):
        """Pack the component"""
        self.frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """Grid the component"""
        self.frame.grid(**kwargs)
    
    def get(self) -> int:
        """Get spinbox value as integer"""
        try:
            return int(self.spinbox.get())
        except ValueError:
            return 10  # Default value if invalid
    
    def set(self, value: int):
        """Set spinbox value"""
        self.spinbox.delete(0, tk.END)
        self.spinbox.insert(0, str(value))
    
    def disable(self):
        """Disable spinbox"""
        self.spinbox.config(state='disabled')
    
    def enable(self):
        """Enable spinbox"""
        self.spinbox.config(state='normal')


class StyledButton:
    """Styled button component"""
    
    def __init__(self, parent, text: str, style: str = 'primary', command: Optional[Callable] = None, **kwargs):
        self.button = tk.Button(
            parent,
            text=text,
            command=command,
            **STYLES[f'button_{style}'],
            **kwargs
        )
    
    def pack(self, **kwargs):
        """Pack the button"""
        self.button.pack(**kwargs)
    
    def grid(self, **kwargs):
        """Grid the button"""
        self.button.grid(**kwargs)
    
    def disable(self):
        """Disable button"""
        self.button.config(state='disabled')
    
    def enable(self):
        """Enable button"""
        self.button.config(state='normal')
    
    def bind(self, event, handler):
        """Bind event to button"""
        self.button.bind(event, handler)


class ScrollableText:
    """Scrollable text area"""
    
    def __init__(self, parent, height: int = 15, width: int = 80):
        self.frame = tk.Frame(parent, bg=STYLES['label']['bg'])
        
        # Text widget with scrollbar
        self.text = tk.Text(
            self.frame,
            height=height,
            width=width,
            font=STYLES['label']['font'],
            bg='white',
            fg=STYLES['label']['fg'],
            relief='solid',
            borderwidth=1,
            wrap=tk.WORD
        )
        
        scrollbar = tk.Scrollbar(self.frame, orient='vertical', command=self.text.yview)
        self.text.configure(yscrollcommand=scrollbar.set)
        
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def pack(self, **kwargs):
        """Pack the component"""
        # Set default values only if not provided in kwargs
        if 'fill' not in kwargs:
            kwargs['fill'] = tk.BOTH
        if 'expand' not in kwargs:
            kwargs['expand'] = True
        self.frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """Grid the component"""
        self.frame.grid(**kwargs, sticky='nsew')
    
    def insert(self, text: str):
        """Insert text"""
        self.text.insert(tk.END, text + '\n')
        self.text.see(tk.END)
    
    def clear(self):
        """Clear text"""
        self.text.delete(1.0, tk.END)
    
    def get(self) -> str:
        """Get all text"""
        return self.text.get(1.0, tk.END)
    
    def disable(self):
        """Disable text widget"""
        self.text.config(state='disabled')
    
    def enable(self):
        """Enable text widget"""
        self.text.config(state='normal')

