import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import google.generativeai as genai
import threading
import re
import os
from typing import Optional

class AICodeEditor:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AI Code Editor - Gemini Flash 2.0")
        self.root.geometry("1200x800")
        self.root.configure(bg='#2b2b2b')
        
        # Initialize Gemini
        self.model = None
        self.api_key = ""
        
        # Current file path
        self.current_file = None
        
        # Setup UI
        self.setup_ui()
        
        # Syntax highlighting colors
        self.syntax_colors = {
            'keyword': '#569cd6',
            'string': '#ce9178',
            'comment': '#6a9955',
            'function': '#dcdcaa',
            'number': '#b5cea8',
            'operator': '#ffffff'
        }
        
        # Python keywords for syntax highlighting
        self.keywords = [
            'def', 'class', 'if', 'elif', 'else', 'for', 'while', 'try', 'except',
            'finally', 'with', 'import', 'from', 'as', 'return', 'yield', 'lambda',
            'and', 'or', 'not', 'in', 'is', 'True', 'False', 'None', 'pass',
            'break', 'continue', 'global', 'nonlocal', 'async', 'await'
        ]
        
    def setup_ui(self):
        # Main menu
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Open", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As", command=self.save_as_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # AI menu
        ai_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="AI", menu=ai_menu)
        ai_menu.add_command(label="Setup API Key", command=self.setup_api_key)
        ai_menu.add_command(label="Generate Code", command=self.show_ai_dialog)
        ai_menu.add_command(label="Explain Code", command=self.explain_code)
        ai_menu.add_command(label="Fix Code", command=self.fix_code)
        ai_menu.add_command(label="Optimize Code", command=self.optimize_code)
        
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Toolbar
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(toolbar, text="New", command=self.new_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Open", command=self.open_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Save", command=self.save_file).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        ttk.Button(toolbar, text="AI Generate", command=self.show_ai_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Explain", command=self.explain_code).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Fix Code", command=self.fix_code).pack(side=tk.LEFT, padx=2)
        
        # Status label
        self.status_label = ttk.Label(toolbar, text="Ready | No API key configured")
        self.status_label.pack(side=tk.RIGHT, padx=10)
        
        # Create paned window for split view
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # Left frame for code editor
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=2)
        
        # Code editor with line numbers
        editor_frame = ttk.Frame(left_frame)
        editor_frame.pack(fill=tk.BOTH, expand=True)
        
        # Line numbers
        self.line_numbers = tk.Text(
            editor_frame,
            width=4,
            bg='#3c3c3c',
            fg='#858585',
            font=('Consolas', 10),
            state=tk.DISABLED,
            wrap=tk.NONE,
            relief=tk.FLAT,
            borderwidth=0
        )
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        
        # Code text area
        self.code_text = scrolledtext.ScrolledText(
            editor_frame,
            wrap=tk.NONE,
            bg='#1e1e1e',
            fg='#d4d4d4',
            font=('Consolas', 11),
            insertbackground='white',
            selectbackground='#264f78',
            relief=tk.FLAT,
            borderwidth=0
        )
        self.code_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Right frame for AI chat/output
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=1)
        
        ttk.Label(right_frame, text="AI Assistant", font=('Arial', 12, 'bold')).pack(pady=5)
        
        # AI output area
        self.ai_output = scrolledtext.ScrolledText(
            right_frame,
            height=20,
            bg='#f8f8f8',
            fg='#333333',
            font=('Arial', 10),
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.ai_output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # AI input frame
        input_frame = ttk.Frame(right_frame)
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(input_frame, text="Ask AI:").pack(anchor=tk.W)
        
        self.ai_input = tk.Text(
            input_frame,
            height=3,
            font=('Arial', 10),
            wrap=tk.WORD
        )
        self.ai_input.pack(fill=tk.X, pady=(2, 5))
        
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Send", command=self.send_ai_query).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Clear", command=self.clear_ai_output).pack(side=tk.RIGHT)
        
        # Bind events
        self.code_text.bind('<KeyRelease>', self.on_text_change)
        self.code_text.bind('<Button-1>', self.on_text_change)
        self.ai_input.bind('<Control-Return>', lambda e: self.send_ai_query())
        
        # Keyboard shortcuts
        self.root.bind('<Control-n>', lambda e: self.new_file())
        self.root.bind('<Control-o>', lambda e: self.open_file())
        self.root.bind('<Control-s>', lambda e: self.save_file())
        
        # Initialize line numbers
        self.update_line_numbers()
        
    def setup_api_key(self):
        """Setup Gemini API key"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Setup Gemini API Key")
        dialog.geometry("400x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Enter your Gemini API Key:", font=('Arial', 10)).pack(pady=10)
        
        api_entry = ttk.Entry(dialog, width=50, show="*")
        api_entry.pack(pady=5)
        
        if self.api_key:
            api_entry.insert(0, self.api_key)
        
        def save_key():
            key = api_entry.get().strip()
            if key:
                try:
                    genai.configure(api_key=key)
                    self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
                    self.api_key = key
                    self.status_label.config(text="Ready | API key configured")
                    messagebox.showinfo("Success", "API key configured successfully!")
                    dialog.destroy()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to configure API key: {str(e)}")
            else:
                messagebox.showwarning("Warning", "Please enter a valid API key")
        
        ttk.Button(dialog, text="Save", command=save_key).pack(pady=10)
        
        api_entry.focus()
        
    def update_line_numbers(self):
        """Update line numbers"""
        self.line_numbers.config(state=tk.NORMAL)
        self.line_numbers.delete(1.0, tk.END)
        
        content = self.code_text.get(1.0, tk.END)
        lines = content.count('\n')
        
        line_numbers_string = '\n'.join(str(i) for i in range(1, lines + 1))
        self.line_numbers.insert(1.0, line_numbers_string)
        self.line_numbers.config(state=tk.DISABLED)
        
    def on_text_change(self, event=None):
        """Handle text changes"""
        self.update_line_numbers()
        self.highlight_syntax()
        
    def highlight_syntax(self):
        """Simple syntax highlighting for Python"""
        content = self.code_text.get(1.0, tk.END)
        
        # Clear existing tags
        for tag in self.syntax_colors:
            self.code_text.tag_delete(tag)
        
        # Configure tags
        for tag, color in self.syntax_colors.items():
            self.code_text.tag_configure(tag, foreground=color)
        
        # Highlight keywords
        for keyword in self.keywords:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            for match in re.finditer(pattern, content):
                start = f"1.0+{match.start()}c"
                end = f"1.0+{match.end()}c"
                self.code_text.tag_add('keyword', start, end)
        
        # Highlight strings
        string_pattern = r'(["\'])(?:(?=(\\?))\2.)*?\1'
        for match in re.finditer(string_pattern, content):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.code_text.tag_add('string', start, end)
        
        # Highlight comments
        comment_pattern = r'#.*$'
        for match in re.finditer(comment_pattern, content, re.MULTILINE):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.code_text.tag_add('comment', start, end)
        
        # Highlight numbers
        number_pattern = r'\b\d+\.?\d*\b'
        for match in re.finditer(number_pattern, content):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.code_text.tag_add('number', start, end)
            
    def new_file(self):
        """Create new file"""
        if messagebox.askokcancel("New File", "Clear current content?"):
            self.code_text.delete(1.0, tk.END)
            self.current_file = None
            self.root.title("AI Code Editor - Untitled")
            
    def open_file(self):
        """Open file"""
        file_path = filedialog.askopenfilename(
            title="Open File",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    self.code_text.delete(1.0, tk.END)
                    self.code_text.insert(1.0, content)
                    self.current_file = file_path
                    self.root.title(f"AI Code Editor - {os.path.basename(file_path)}")
                    self.highlight_syntax()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open file: {str(e)}")
                
    def save_file(self):
        """Save current file"""
        if self.current_file:
            try:
                content = self.code_text.get(1.0, tk.END)
                with open(self.current_file, 'w', encoding='utf-8') as file:
                    file.write(content)
                messagebox.showinfo("Success", "File saved successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {str(e)}")
        else:
            self.save_as_file()
            
    def save_as_file(self):
        """Save file as"""
        file_path = filedialog.asksaveasfilename(
            title="Save As",
            defaultextension=".py",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")]
        )
        if file_path:
            try:
                content = self.code_text.get(1.0, tk.END)
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(content)
                self.current_file = file_path
                self.root.title(f"AI Code Editor - {os.path.basename(file_path)}")
                messagebox.showinfo("Success", "File saved successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {str(e)}")
                
    def show_ai_dialog(self):
        """Show AI code generation dialog"""
        if not self.model:
            messagebox.showwarning("Warning", "Please setup your Gemini API key first!")
            self.setup_api_key()
            return
            
        dialog = tk.Toplevel(self.root)
        dialog.title("AI Code Generator")
        dialog.geometry("500x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Describe what code you want to generate:", font=('Arial', 10)).pack(pady=10)
        
        prompt_text = scrolledtext.ScrolledText(dialog, height=8, font=('Arial', 10))
        prompt_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        def generate_code():
            prompt = prompt_text.get(1.0, tk.END).strip()
            if prompt:
                dialog.destroy()
                self.generate_code_with_ai(prompt)
            else:
                messagebox.showwarning("Warning", "Please enter a description")
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Generate", command=generate_code).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        prompt_text.focus()
        
    def generate_code_with_ai(self, prompt):
        """Generate code using AI"""
        def ai_task():
            try:
                self.update_ai_output("🤖 Generating code...\n")
                
                # Create a comprehensive prompt for code generation
                full_prompt = f"""
Generate Python code based on this description: {prompt}

Requirements:
- Write clean, well-commented Python code
- Include docstrings for functions and classes
- Follow PEP 8 style guidelines
- Make the code production-ready
- Only return the code, no explanations

Code:
"""
                
                response = self.model.generate_content(full_prompt)
                generated_code = response.text
                
                # Clean up the response to extract just the code
                if "```python" in generated_code:
                    code_start = generated_code.find("```python") + 9
                    code_end = generated_code.find("```", code_start)
                    if code_end != -1:
                        generated_code = generated_code[code_start:code_end].strip()
                elif "```" in generated_code:
                    code_start = generated_code.find("```") + 3
                    code_end = generated_code.find("```", code_start)
                    if code_end != -1:
                        generated_code = generated_code[code_start:code_end].strip()
                
                # Insert generated code at cursor position
                cursor_pos = self.code_text.index(tk.INSERT)
                self.code_text.insert(cursor_pos, generated_code)
                self.highlight_syntax()
                
                self.update_ai_output(f"✅ Code generated successfully!\n\nPrompt: {prompt}\n\n")
                
            except Exception as e:
                self.update_ai_output(f"❌ Error generating code: {str(e)}\n")
        
        threading.Thread(target=ai_task, daemon=True).start()
        
    def explain_code(self):
        """Explain selected code or all code"""
        if not self.model:
            messagebox.showwarning("Warning", "Please setup your Gemini API key first!")
            return
            
        # Get selected text or all text
        try:
            selected_code = self.code_text.get(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            selected_code = self.code_text.get(1.0, tk.END).strip()
            
        if not selected_code:
            messagebox.showinfo("Info", "No code to explain")
            return
            
        def ai_task():
            try:
                self.update_ai_output("🤖 Analyzing code...\n")
                
                prompt = f"""
Explain this Python code in detail:

{selected_code}

Please provide:
1. Overall purpose and functionality
2. Step-by-step breakdown
3. Key concepts used
4. Potential improvements or issues
"""
                
                response = self.model.generate_content(prompt)
                explanation = response.text
                
                self.update_ai_output(f"📝 Code Explanation:\n\n{explanation}\n\n")
                
            except Exception as e:
                self.update_ai_output(f"❌ Error explaining code: {str(e)}\n")
        
        threading.Thread(target=ai_task, daemon=True).start()
        
    def fix_code(self):
        """Fix code issues"""
        if not self.model:
            messagebox.showwarning("Warning", "Please setup your Gemini API key first!")
            return
            
        try:
            selected_code = self.code_text.get(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            selected_code = self.code_text.get(1.0, tk.END).strip()
            
        if not selected_code:
            messagebox.showinfo("Info", "No code to fix")
            return
            
        def ai_task():
            try:
                self.update_ai_output("🤖 Analyzing and fixing code...\n")
                
                prompt = f"""
Analyze this Python code and fix any issues:

{selected_code}

Please:
1. Identify any syntax errors, logical errors, or potential bugs
2. Fix the issues
3. Improve code quality and efficiency
4. Return the corrected code with comments explaining the fixes

Original code with issues fixed:
"""
                
                response = self.model.generate_content(prompt)
                fixed_code = response.text
                
                self.update_ai_output(f"🔧 Code Analysis and Fixes:\n\n{fixed_code}\n\n")
                
            except Exception as e:
                self.update_ai_output(f"❌ Error fixing code: {str(e)}\n")
        
        threading.Thread(target=ai_task, daemon=True).start()
        
    def optimize_code(self):
        """Optimize code performance"""
        if not self.model:
            messagebox.showwarning("Warning", "Please setup your Gemini API key first!")
            return
            
        try:
            selected_code = self.code_text.get(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            selected_code = self.code_text.get(1.0, tk.END).strip()
            
        if not selected_code:
            messagebox.showinfo("Info", "No code to optimize")
            return
            
        def ai_task():
            try:
                self.update_ai_output("🤖 Optimizing code...\n")
                
                prompt = f"""
Optimize this Python code for better performance and readability:

{selected_code}

Please provide:
1. Optimized version of the code
2. Explanation of optimizations made
3. Performance improvements achieved
4. Best practices applied

Optimized code:
"""
                
                response = self.model.generate_content(prompt)
                optimized_code = response.text
                
                self.update_ai_output(f"⚡ Code Optimization:\n\n{optimized_code}\n\n")
                
            except Exception as e:
                self.update_ai_output(f"❌ Error optimizing code: {str(e)}\n")
        
        threading.Thread(target=ai_task, daemon=True).start()
        
    def send_ai_query(self):
        """Send custom query to AI"""
        if not self.model:
            messagebox.showwarning("Warning", "Please setup your Gemini API key first!")
            return
            
        query = self.ai_input.get(1.0, tk.END).strip()
        if not query:
            return
            
        # Get current code context
        current_code = self.code_text.get(1.0, tk.END).strip()
        
        def ai_task():
            try:
                self.update_ai_output(f"👤 You: {query}\n")
                self.update_ai_output("🤖 AI: Thinking...\n")
                
                # Include code context in the prompt
                context_prompt = f"""
Current code in editor:
{current_code if current_code else "No code in editor"}

User question: {query}

Please provide a helpful response considering the current code context.
"""
                
                response = self.model.generate_content(context_prompt)
                ai_response = response.text
                
                self.update_ai_output(f"🤖 AI: {ai_response}\n\n")
                
                # Clear input
                self.ai_input.delete(1.0, tk.END)
                
            except Exception as e:
                self.update_ai_output(f"❌ Error: {str(e)}\n")
        
        threading.Thread(target=ai_task, daemon=True).start()
        
    def update_ai_output(self, text):
        """Update AI output area"""
        self.ai_output.config(state=tk.NORMAL)
        self.ai_output.insert(tk.END, text)
        self.ai_output.see(tk.END)
        self.ai_output.config(state=tk.DISABLED)
        self.root.update_idletasks()
        
    def clear_ai_output(self):
        """Clear AI output area"""
        self.ai_output.config(state=tk.NORMAL)
        self.ai_output.delete(1.0, tk.END)
        self.ai_output.config(state=tk.DISABLED)
        
    def run(self):
        """Start the application"""
        self.root.mainloop()

if __name__ == "__main__":
    # Check if google-generativeai is installed
    try:
        import google.generativeai
    except ImportError:
        print("Please install the required package:")
        print("pip install google-generativeai")
        exit(1)
    
    app = AICodeEditor()
    app.run()
