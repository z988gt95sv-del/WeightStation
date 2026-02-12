import tkinter as tk
from tkinter import ttk

class CargoInputFrame:
    def __init__(self, parent, on_cancel_callback=None, on_confirm_callback=None):
        self.parent = parent
        self.on_cancel_callback = on_cancel_callback
        self.on_confirm_callback = on_confirm_callback
        
        # 主 Frame
        self.main_frame = tk.Frame(parent, bg="lightgray")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 追蹤當前焦點的輸入框（0 或 1）
        self.current_entry = 0
        
        # 建立 UI 元件
        self.create_input_section()
        self.create_number_buttons()
        self.create_keyboard()
        
        # 綁定鍵盤事件
        self.bind_keyboard_events()
        
    def create_input_section(self):
        """建立上方輸入區（輸入框 + 破折號 + 按鈕）"""
        input_frame = tk.Frame(self.main_frame, bg="lightgray", height=120)
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        input_frame.pack_propagate(False)
        
        # 驗證函數：禁止空白鍵
        def validate_no_space(char):
            """檢查輸入是否為空白，如果是則返回 False"""
            if char == ' ':
                return False
            return True
        
        # 第一個輸入框（寬度 30%）
        self.entry1 = tk.Entry(input_frame, font=("Arial", 36), justify="center", bd=2, relief=tk.SOLID)
        self.entry1.place(x=0, y=0, width=307, height=120)
        self.entry1.bind("<FocusIn>", lambda e: self.set_current_entry(0))
        self.entry1.bind("<space>", lambda e: "break")  # 禁止空白鍵輸入
        
        # 破折號
        dash_label = tk.Label(input_frame, text="-", font=("Arial", 48, "bold"), bg="lightgray")
        dash_label.place(x=307, y=0, width=40, height=120)
        
        # 第二個輸入框（寬度 30%）
        self.entry2 = tk.Entry(input_frame, font=("Arial", 36), justify="center", bd=2, relief=tk.SOLID)
        self.entry2.place(x=347, y=0, width=307, height=120)
        self.entry2.bind("<FocusIn>", lambda e: self.set_current_entry(1))
        self.entry2.bind("<space>", lambda e: "break")  # 禁止空白鍵輸入
        
        # 確認按鈕（寬度 15%）
        btn_confirm = tk.Button(
            input_frame,
            text="確認",
            font=("Arial", 20, "bold"),
            bg="#4caf50",
            fg="white",
            command=self.on_confirm
        )
        btn_confirm.place(x=654, y=0, width=154, height=120)
        
        # 取消按鈕（寬度 15%）
        btn_cancel = tk.Button(
            input_frame,
            text="取消",
            font=("Arial", 20, "bold"),
            bg="#f44336",
            fg="white",
            command=self.on_cancel
        )
        btn_cancel.place(x=808, y=0, width=154, height=120)
        
        # 預設焦點在第一個輸入框
        self.entry1.focus_set()
        
    def create_number_buttons(self):
        """建立數字按鈕列（0-9）"""
        number_frame = tk.Frame(self.main_frame, bg="lightgray", height=90)
        number_frame.pack(fill=tk.X, padx=5, pady=5)
        number_frame.pack_propagate(False)
        
        # 10 個數字按鈕，使用 pack 自動平均分配空間
        for i in range(10):
            btn = tk.Button(
                number_frame,
                text=str(i),
                font=("Arial", 24, "bold"),
                bg="#2196F3",
                fg="white",
                command=lambda num=str(i): self.insert_text(num)
            )
            btn.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=1)
    
    def create_keyboard(self):
        """建立虛擬英文鍵盤（含 Backspace 和 Clear）"""
        keyboard_frame = tk.Frame(self.main_frame, bg="lightgray")
        keyboard_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 鍵盤佈局（標準 QWERTY 鍵盤，加上 Backspace 和 Clear）
        keyboard_layout = [
            ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
            ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
            ['Z', 'X', 'C', 'V', 'B', 'N', 'M', 'SPACE'],
            ['BACKSPACE', 'CLEAR']
        ]
        
        for row_idx, row in enumerate(keyboard_layout):
            row_frame = tk.Frame(keyboard_frame, bg="lightgray")
            row_frame.pack(fill=tk.BOTH, expand=True, pady=2)
            
            for key in row:
                if key == 'BACKSPACE':
                    btn = tk.Button(
                        row_frame,
                        text="BACKSPACE",
                        font=("Arial", 14, "bold"),
                        bg="#FF9800",
                        fg="white",
                        command=self.backspace
                    )
                    btn.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)
                elif key == 'CLEAR':
                    btn = tk.Button(
                        row_frame,
                        text="CLEAR",
                        font=("Arial", 14, "bold"),
                        bg="#FF5722",
                        fg="white",
                        command=self.clear_all
                    )
                    btn.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)
                elif key == 'SPACE':
                    btn = tk.Button(
                        row_frame,
                        text="SPACE",
                        font=("Arial", 14, "bold"),
                        bg="#607D8B",
                        fg="white",
                        command=lambda: self.insert_text(' ')
                    )
                    btn.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)
                else:
                    btn = tk.Button(
                        row_frame,
                        text=key,
                        font=("Arial", 16, "bold"),
                        bg="#607D8B",
                        fg="white",
                        command=lambda k=key: self.insert_text(k)
                    )
                    btn.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)
    
    def bind_keyboard_events(self):
        """綁定鍵盤事件用於快捷鍵功能"""
        # 在 Entry 組件上綁定數字、字母和編輯鍵
        # 數字鍵 (0-9)
        for i in range(10):
            self.entry1.bind(str(i), self.on_number_key)
            self.entry2.bind(str(i), self.on_number_key)
        
        # 小數點
        self.entry1.bind('.', self.on_decimal_key)
        self.entry2.bind('.', self.on_decimal_key)
        
        # Entry 專屬鍵
        self.entry1.bind('<BackSpace>', self.on_backspace_key)
        self.entry2.bind('<BackSpace>', self.on_backspace_key)
        self.entry1.bind('<Delete>', self.on_delete_key)
        self.entry2.bind('<Delete>', self.on_delete_key)
        self.entry1.bind('<Tab>', self.on_tab_key)
        self.entry2.bind('<Tab>', self.on_tab_key)
        
        # 字母鍵 (A-Z)
        for char in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            self.entry1.bind(char.lower(), self.on_letter_key)
            self.entry1.bind(char, self.on_letter_key)
            self.entry2.bind(char.lower(), self.on_letter_key)
            self.entry2.bind(char, self.on_letter_key)
        
        # 全域快捷鍵 - 在 parent 層級綁定 Enter 和 Escape
        self.parent.bind('<Return>', self.on_return_key)
        self.parent.bind('<Escape>', self.on_escape_key)
    
    def on_number_key(self, event):
        """處理數字鍵 (0-9)"""
        if self.current_entry == 0:
            self.entry1.insert(tk.END, event.char)
        else:
            self.entry2.insert(tk.END, event.char)
        return 'break'
    
    def on_decimal_key(self, event):
        """處理小數點鍵"""
        if self.current_entry == 0:
            self.entry1.insert(tk.END, '.')
        else:
            self.entry2.insert(tk.END, '.')
        return 'break'
    
    def on_letter_key(self, event):
        """處理字母鍵"""
        if self.current_entry == 0:
            self.entry1.insert(tk.END, event.char)
        else:
            self.entry2.insert(tk.END, event.char)
        return 'break'
    
    def on_backspace_key(self, event):
        """處理 BackSpace 鍵"""
        self.backspace()
        return 'break'
    
    def on_delete_key(self, event):
        """處理 Delete 鍵"""
        self.clear_all()
        return 'break'
    
    def on_return_key(self, event):
        """處理 Return 鍵（確認）"""
        self.on_confirm()
        return 'break'
    
    def on_escape_key(self, event):
        """處理 Escape 鍵（取消）"""
        self.on_cancel()
        return 'break'
    
    def on_tab_key(self, event):
        """處理 Tab 鍵（切換輸入框）"""
        if self.current_entry == 0:
            self.current_entry = 1
            self.entry2.focus_set()
        else:
            self.current_entry = 0
            self.entry1.focus_set()
        return 'break'
    
    def set_current_entry(self, entry_num):
        """設定當前焦點的輸入框"""
        self.current_entry = entry_num
    
    def insert_text(self, text):
        """插入文字到當前焦點的輸入框（禁止空白鍵）"""
        # 禁止插入空白鍵
        if text == ' ':
            return
        
        if self.current_entry == 0:
            self.entry1.insert(tk.END, text)
        else:
            self.entry2.insert(tk.END, text)
    
    def backspace(self):
        """刪除當前焦點輸入框的最後一個字元"""
        if self.current_entry == 0:
            current_text = self.entry1.get()
            if current_text:
                self.entry1.delete(0, tk.END)
                self.entry1.insert(0, current_text[:-1])
        else:
            current_text = self.entry2.get()
            if current_text:
                self.entry2.delete(0, tk.END)
                self.entry2.insert(0, current_text[:-1])
    
    def clear_all(self):
        """清空當前焦點輸入框的所有內容"""
        if self.current_entry == 0:
            self.entry1.delete(0, tk.END)
        else:
            self.entry2.delete(0, tk.END)
    
    def on_confirm(self):
        """確認按鈕的回調函數"""
        if self.on_confirm_callback:
            self.on_confirm_callback()
        else:
            value1 = self.entry1.get()
            value2 = self.entry2.get()
            print(f"確認輸入: {value1} - {value2}")
    
    def on_cancel(self):
        """取消按鈕的回調函數"""
        if self.on_cancel_callback:
            self.on_cancel_callback()
        print("已取消輸入")

    def get_entry_values(self):
        """取得車牌輸入框內容"""
        return self.entry1.get(), self.entry2.get()

    def set_entry_values(self, value1, value2):
        """設定車牌輸入框內容"""
        self.entry1.delete(0, tk.END)
        self.entry2.delete(0, tk.END)
        if value1:
            self.entry1.insert(0, value1)
        if value2:
            self.entry2.insert(0, value2)
        self.set_current_entry(0)
        self.entry1.focus_set()


class CustomerFrame:
    def __init__(self, parent, customer_id_list=None, on_cancel_callback=None, on_confirm_callback=None):
        """建立廠商選擇頁面"""
        self.parent = parent
        self.customer_id_list = customer_id_list if customer_id_list else []
        self.on_cancel_callback = on_cancel_callback
        self.on_confirm_callback = on_confirm_callback
        
        # 主 Frame
        self.main_frame = tk.Frame(parent, bg="lightgray")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 選中的廠商
        self.selected_customer = None
        
        # 存儲所有廠商按鈕的引用
        self.customer_buttons = {}
        
        # 建立按鈕行（確認和取消按鈕）
        self.create_button_row()
        
        # 建立廠商按鈕
        self.create_customer_buttons()
        
        # 綁定鍵盤事件
        self.bind_keyboard_events()
    
    def create_button_row(self):
        """在右上角建立確認和取消按鈕"""
        button_frame = tk.Frame(self.main_frame, bg="lightgray", height=120)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        button_frame.pack_propagate(False)
        
        # 顯示框（寬度 55%）
        self.display_frame = tk.Label(
            button_frame,
            text="未選擇客戶",
            font=("Arial", 48, "bold"),
            bg="white",
            fg="black",
            relief=tk.SOLID,
            bd=2,
            anchor="w",
            padx=10
        )
        self.display_frame.place(x=0, y=0, width=564, height=120)
        
        # 確認按鈕（寬度 15%）
        btn_confirm = tk.Button(
            button_frame,
            text="確認",
            font=("Arial", 20, "bold"),
            bg="#4caf50",
            fg="white",
            command=self.on_confirm
        )
        btn_confirm.place(x=574, y=0, width=154, height=120)
        
        # 取消按鈕（寬度 15%）
        btn_cancel = tk.Button(
            button_frame,
            text="取消",
            font=("Arial", 20, "bold"),
            bg="#f44336",
            fg="white",
            command=self.on_cancel
        )
        btn_cancel.place(x=728, y=0, width=154, height=120)
    
    def create_customer_buttons(self):
        """根據 CustomerID 陣列建立廠商按鈕（Toggle 模式）"""
        print(f"DEBUG: create_customer_buttons 中，self.customer_id_list = {self.customer_id_list}")
        
        if not self.customer_id_list:
            label = tk.Label(
                self.main_frame,
                text="無廠商資料",
                font=("Arial", 24),
                bg="lightgray"
            )
            label.pack(expand=True)
            return
        
        # 建立滾動區域
        canvas = tk.Canvas(self.main_frame, bg="lightgray")
        scrollbar = tk.Scrollbar(self.main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="lightgray")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 計算按鈕佈局（每行 4 個按鈕）
        buttons_per_row = 4
        button_width = 1024 // buttons_per_row - 10
        button_height = 80
        
        for idx, customer_name in enumerate(self.customer_id_list):
            row = idx // buttons_per_row
            col = idx % buttons_per_row
            
            btn = tk.Button(
                scrollable_frame,
                text=customer_name,
                width=20,
                height=3,
                font=("Arial", 14, "bold"),
                bg="#90CAF9",
                fg="black",
                relief=tk.RAISED,
                bd=3,
                command=lambda name=customer_name: self.on_customer_toggle(name)
            )
            btn.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            
            # 存儲按鈕引用
            self.customer_buttons[customer_name] = btn
        
        # 配置列的權重，使按鈕均勻分布
        for i in range(buttons_per_row):
            scrollable_frame.grid_columnconfigure(i, weight=1)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def bind_keyboard_events(self):
        """綁定鍵盤事件 - Enter 確認，Escape 取消"""
        # 在 parent 層級綁定全域快捷鍵
        self.parent.bind('<Return>', self.on_return_key)
        self.parent.bind('<Escape>', self.on_escape_key)
    
    def on_return_key(self, event):
        """處理 Return 鍵（確認）"""
        self.on_confirm()
        return 'break'
    
    def on_escape_key(self, event):
        """處理 Escape 鍵（取消）"""
        self.on_cancel()
        return 'break'
    
    def on_customer_toggle(self, customer_name):
        """切換廠商按鈕的選擇狀態"""
        # 如果點擊的是已選中的按鈕，取消選擇
        if self.selected_customer == customer_name:
            self.selected_customer = None
            self.customer_buttons[customer_name].config(bg="#90CAF9", fg="black", relief=tk.RAISED)
            self.display_frame.config(text="未選擇客戶")
            print(f"已取消選擇: {customer_name}")
        else:
            # 如果之前有選擇的按鈕，恢復其樣式
            if self.selected_customer is not None:
                self.customer_buttons[self.selected_customer].config(bg="#90CAF9", fg="black", relief=tk.RAISED)
            
            # 選擇新的按鈕
            self.selected_customer = customer_name
            self.customer_buttons[customer_name].config(bg="#2196F3", fg="white", relief=tk.SUNKEN)
            self.display_frame.config(text=f"已選擇: {customer_name}")
            print(f"已選擇廠商: {customer_name}")
    
    def on_confirm(self):
        """確認按鈕的回調函數"""
        if self.on_confirm_callback:
            self.on_confirm_callback()
        elif self.selected_customer:
            print(f"確認選擇廠商: {self.selected_customer}")
        else:
            print("請先選擇廠商")
    
    def on_cancel(self):
        """取消按鈕的回調函數"""
        # 恢復之前選中按鈕的樣式
        if self.selected_customer is not None:
            self.customer_buttons[self.selected_customer].config(bg="#90CAF9", fg="black", relief=tk.RAISED)
        
        self.selected_customer = None
        self.display_frame.config(text="未選擇客戶")
        
        if self.on_cancel_callback:
            self.on_cancel_callback()
        print("已取消選擇")

    def get_display_text(self):
        """取得顯示框內容"""
        return self.display_frame.cget("text")

    def set_selected_customer(self, customer_name):
        """設定預選廠商"""
        if self.selected_customer is not None and self.selected_customer in self.customer_buttons:
            self.customer_buttons[self.selected_customer].config(bg="#90CAF9", fg="black", relief=tk.RAISED)

        self.selected_customer = None

        if not customer_name:
            self.display_frame.config(text="未選擇客戶")
            return

        if customer_name in self.customer_buttons:
            self.selected_customer = customer_name
            self.customer_buttons[customer_name].config(bg="#2196F3", fg="white", relief=tk.SUNKEN)
            self.display_frame.config(text=f"已選擇: {customer_name}")
        else:
            self.display_frame.config(text="未選擇客戶")


def main():
    root = tk.Tk()
    root.title("貨物輸入系統")
    root.geometry("1024x768")
    root.resizable(False, False)
    
    # 設置標籤頁樣式
    style = ttk.Style()
    style.configure('TNotebook.Tab', 
                    font=('Arial', 24, 'bold'),
                    padding=[60, 20])  # 寬度放大3倍 (20*3=60), 高度放大2倍 (10*2=20)
    
    # 建立 Notebook（標籤頁容器）
    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True)
    
    # 第一個標籤頁：車牌輸入
    cargo_frame = tk.Frame(notebook)
    cargo_frame.pack(fill=tk.BOTH, expand=True)
    cargo_app = CargoInputFrame(cargo_frame)
    notebook.add(cargo_frame, text="車牌")
    
    # 第二個標籤頁：廠商選擇
    customer_frame = tk.Frame(notebook)
    customer_frame.pack(fill=tk.BOTH, expand=True)
    customer_app = CustomerFrame(customer_frame)
    notebook.add(customer_frame, text="廠商")
    
    root.mainloop()


if __name__ == "__main__":
    main()

