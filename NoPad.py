import tkinter as tk

class NumericKeypad:
    def __init__(self, parent, on_confirm_callback=None, on_cancel_callback=None):
        """
        建立數字鍵盤版面
        
        參數:
            parent: 父容器
            on_confirm_callback: 確定按鈕的回調函數
            on_cancel_callback: 取消按鈕的回調函數
        """
        self.parent = parent
        self.on_confirm_callback = on_confirm_callback
        self.on_cancel_callback = on_cancel_callback
        
        # 儲存輸入的數字
        self.input_value = "0"
        
        # 主 Frame
        self.main_frame = tk.Frame(parent, bg="lightgray")
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 建立 UI 元件
        self.create_display_section()
        self.create_keypad()
        
        # 綁定鍵盤事件
        self.bind_keyboard_events()
    
    def create_display_section(self):
        """建立顯示區域和確定/取消按鈕"""
        display_frame = tk.Frame(self.main_frame, bg="lightgray", height=100)
        display_frame.pack(fill=tk.BOTH, expand=False, padx=5, pady=5)
        display_frame.pack_propagate(False)  # 禁止自動調整大小
        
        # 顯示數字的標籤
        self.display_label = tk.Label(
            display_frame,
            text="0",
            font=("Arial", 48, "bold"),
            bg="white",
            fg="black",
            relief=tk.SOLID,
            bd=2,
            anchor="e",
            padx=20
        )
        self.display_label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 確定按鈕
        btn_confirm = tk.Button(
            display_frame,
            text="確定",
            font=("Arial", 20, "bold"),
            bg="#4caf50",
            fg="white",
            width=8,
            height=3,
            command=self.on_confirm
        )
        btn_confirm.pack(side=tk.LEFT, padx=5)
        
        # 取消按鈕
        btn_cancel = tk.Button(
            display_frame,
            text="取消",
            font=("Arial", 20, "bold"),
            bg="#f44336",
            fg="white",
            width=8,
            height=3,
            command=self.on_cancel
        )
        btn_cancel.pack(side=tk.LEFT, padx=5)
    
    def create_keypad(self):
        """建立數字鍵盤"""
        keypad_frame = tk.Frame(self.main_frame, bg="lightgray")
        keypad_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 數字鍵盤佈局 (3x3 + 0 + .)
        keypad_layout = [
            ['7', '8', '9'],
            ['4', '5', '6'],
            ['1', '2', '3'],
            ['0', '.']
        ]
        
        for row_idx, row in enumerate(keypad_layout):
            row_frame = tk.Frame(keypad_frame, bg="lightgray")
            row_frame.pack(fill=tk.BOTH, expand=True, pady=2)
            
            for col_idx, key in enumerate(row):
                if key == '.':
                    btn = tk.Button(
                        row_frame,
                        text=key,
                        font=("Arial", 24, "bold"),
                        bg="#FF9800",
                        fg="white",
                        command=lambda k=key: self.on_decimal_click()
                    )
                    btn.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)
                else:
                    btn = tk.Button(
                        row_frame,
                        text=key,
                        font=("Arial", 24, "bold"),
                        bg="#2196F3",
                        fg="white",
                        command=lambda k=key: self.on_number_click(k)
                    )
                    btn.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)
        
        # 添加功能按鈕列
        function_frame = tk.Frame(keypad_frame, bg="lightgray")
        function_frame.pack(fill=tk.BOTH, expand=True, pady=2)
        
        # 退格按鈕
        btn_backspace = tk.Button(
            function_frame,
            text="退格",
            font=("Arial", 18, "bold"),
            bg="#FF9800",
            fg="white",
            command=self.on_backspace
        )
        btn_backspace.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)
        
        # 清空按鈕
        btn_clear = tk.Button(
            function_frame,
            text="清空",
            font=("Arial", 18, "bold"),
            bg="#FF5722",
            fg="white",
            command=self.on_clear
        )
        btn_clear.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)
    
    def on_number_click(self, number):
        """當點擊數字按鈕時"""
        # 如果輸入值為 "0"，則替換為新數字
        if self.input_value == "0":
            self.input_value = number
        else:
            self.input_value += number
        
        self.update_display()
    
    def on_decimal_click(self):
        """當點擊小數點按鈕時"""
        # 如果已經有小數點，則不再添加
        if "." not in self.input_value:
            # 如果輸入值為空或為 "0"，則設為 "0."
            if self.input_value == "0" or self.input_value == "":
                self.input_value = "0."
            else:
                self.input_value += "."
        
        self.update_display()
    
    def on_backspace(self):
        """退格：刪除最後一個數字"""
        if self.input_value:
            self.input_value = self.input_value[:-1]
            if not self.input_value:
                self.input_value = "0"
        
        self.update_display()
    
    def on_clear(self):
        """清空所有輸入"""
        self.input_value = "0"
        self.update_display()
    
    def bind_keyboard_events(self):
        """綁定鍵盤事件用於輸入數字和小數點"""
        # 綁定到 parent 和 main_frame 以確保正確接收事件
        self.parent.bind('<BackSpace>', self.on_backspace_key)
        self.parent.bind('<Delete>', self.on_delete_key)
        self.parent.bind('<Return>', self.on_return_key)
        self.parent.bind('<Escape>', self.on_escape_key)
        self.parent.bind('<KeyPress>', self.on_key_press)
        
        # 給予父窗口焦點
        self.parent.focus_set()
    
    def on_key_press(self, event):
        """處理鍵盤按鍵事件"""
        # 處理數字鍵（0-9）
        if event.char in '0123456789':
            self.on_number_click(event.char)
        # 處理小數點
        elif event.char == '.':
            self.on_decimal_click()
    
    def on_backspace_key(self, event):
        """處理 BackSpace 鍵"""
        self.on_backspace()
        return 'break'  # 阻止事件進一步傳播
    
    def on_delete_key(self, event):
        """處理 Delete 鍵"""
        self.on_clear()
        return 'break'
    
    def on_return_key(self, event):
        """處理 Enter 鍵"""
        self.on_confirm()
        return 'break'
    
    def on_escape_key(self, event):
        """處理 Escape 鍵"""
        self.on_cancel()
        return 'break'
    
    def update_display(self):
        """更新顯示"""
        self.display_label.config(text=self.input_value)
    
    def on_confirm(self):
        """確定按鈕的回調函數"""
        if self.on_confirm_callback:
            self.on_confirm_callback(self.input_value)
        print(f"確定輸入: {self.input_value}")
    
    def on_cancel(self):
        """取消按鈕的回調函數"""
        if self.on_cancel_callback:
            self.on_cancel_callback()
        print("已取消輸入")
    
    def get_value(self):
        """取得輸入的數值"""
        return self.input_value


def main():
    """測試用"""
    root = tk.Tk()
    root.title("數字鍵盤")
    root.geometry("600x700")
    
    def on_confirm(value):
        print(f"輸入的數值: {value}")
    
    def on_cancel():
        print("已取消")
    
    keypad = NumericKeypad(root, on_confirm_callback=on_confirm, on_cancel_callback=on_cancel)
    
    root.mainloop()


if __name__ == "__main__":
    main()
