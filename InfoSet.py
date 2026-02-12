import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import sqlite3

def create_info_frame(parent):
    """
    建立一個 frame，頂部包含下拉式選單
    
    參數:
        parent: 父容器
    """
    # 定義驗證函式：只允許數字和小數點，小數點後最多三位
    def validate_decimal_input(P):
        """驗證輸入是否為最多三位小數的數字"""
        if P == "":  # 允許空字符串
            return True
        
        # 只允許一個小數點
        if P.count('.') > 1:
            return False
        
        # 檢查是否包含小數點
        if '.' in P:
            parts = P.split('.')
            # 整數部分可以是空或數字
            if parts[0] and not parts[0].isdigit():
                return False
            # 小數部分可以是空（正在輸入）或最多三位數字
            if parts[1]:
                if not parts[1].isdigit() or len(parts[1]) > 3:
                    return False
        else:
            # 沒有小數點，檢查是否全是數字
            if not P.isdigit():
                return False
        
        return True
    
    # 建立主 frame
    main_frame = tk.Frame(parent)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # 建立頂部 frame 放下拉式選單
    top_frame = tk.Frame(main_frame)
    top_frame.pack(fill=tk.X, padx=5, pady=5)
    
    # 添加標籤
    label = tk.Label(top_frame, text="選擇類型:", font=("Arial", 16))
    label.pack(side=tk.LEFT, padx=5)
    
    # 建立下拉式選單 (Combobox)
    options = ["客戶", "品項"]
    combo_box = ttk.Combobox(top_frame, values=options, state="readonly", width=20, font=("Arial", 16), height=20)
    combo_box.pack(side=tk.LEFT, padx=5)
    combo_box.set("品項")  # 預設值
    
    # 配置下拉選單的字體樣式
    style = ttk.Style()
    style.configure('TCombobox', font=('Arial', 16))
    
    # 設定下拉選單內容的字體（使用 option_add 來控制彈出式選單的字體）
    parent.option_add('*TCombobox*Listbox.font', ('Arial', 20))
    
    # 建立第二個下拉式選單 (dataCombo)
    dataCombo = ttk.Combobox(top_frame, state="readonly", width=20, font=("Arial", 16), height=20)
    dataCombo.pack(side=tk.LEFT, padx=5)
    
    # 建立內容 frame (用於放置其他元件)
    content_frame = tk.Frame(main_frame)
    content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # 建立置中容器
    center_container = tk.Frame(content_frame)
    center_container.place(relx=0.5, rely=0.5, anchor="center")
    
    # 在 center_container 中添加兩個輸入欄位
    # 名稱欄位
    name_frame = tk.Frame(center_container)
    name_frame.pack(pady=15)
    
    name_label = tk.Label(name_frame, text="名稱:", width=10, anchor="e", font=("Arial", 16))
    name_label.pack(side=tk.LEFT, padx=5)
    
    name_entry = tk.Entry(name_frame, font=("Arial", 16), width=30)
    name_entry.config(bd=2, relief=tk.SOLID)
    name_entry.pack(side=tk.LEFT, padx=5, ipady=8)
    
    # 數值欄位
    value_frame = tk.Frame(center_container)
    value_frame.pack(pady=15)
    
    value_label = tk.Label(value_frame, text="數值:", width=10, anchor="e", font=("Arial", 16))
    value_label.pack(side=tk.LEFT, padx=5)
    
    # 註冊驗證函式並應用到 value_entry
    vcmd = (parent.register(validate_decimal_input), '%P')
    value_entry = tk.Entry(value_frame, font=("Arial", 16), width=30,
                           validate='key', validatecommand=vcmd)
    value_entry.config(bd=2, relief=tk.SOLID)
    value_entry.pack(side=tk.LEFT, padx=5, ipady=8)
    
    # 定義 dataCombo 值變化的回調函式
    def on_data_combo_change(event):
        """監聽 dataCombo 的值變化，於品項模式載入名稱與價格。"""
        selected_item = dataCombo.get()
        selected_type = combo_box.get()

        if selected_type == "品項" and selected_item:
            import main as app  # 延遲匯入以避免循環匯入
            price = app.ItemValue.get(selected_item)
            name_entry.delete(0, tk.END)
            name_entry.insert(0, selected_item)
            value_entry.delete(0, tk.END)
            value_entry.insert(0, str(price) if price is not None else "")
            print(f"✓ 已載入商品: {selected_item}, 價格: {price}")
        elif selected_type == "客戶" and selected_item:
            name_entry.delete(0, tk.END)
            name_entry.insert(0, selected_item)
            value_entry.delete(0, tk.END)
            print(f"✓ 已載入客戶: {selected_item}")
    
    # 綁定 dataCombo 的值變化事件
    dataCombo.bind("<<ComboboxSelected>>", on_data_combo_change)
    
    # 定義 combo_box 值變化的回調函式
    def on_combo_change(event):
        """監聽 combo_box 的值變化，動態更新 dataCombo"""
        selected_type = combo_box.get()
        print(f"✓ combo_box 值已變化: {selected_type}")

        # 清空輸入欄位
        name_entry.delete(0, tk.END)
        value_entry.delete(0, tk.END)

        import main as app  # 延遲匯入，取得全域 CustomerID/ItemValue

        if selected_type == "客戶":
            dataCombo['values'] = app.CustomerID
            print(f"  已載入客戶資料: {app.CustomerID}")
        elif selected_type == "品項":
            items = list(app.ItemValue.keys())
            dataCombo['values'] = items
            print(f"  已載入商品資料: {items}")

        dataCombo.current(0) if dataCombo['values'] else None
    
    # 綁定 combo_box 的值變化事件
    combo_box.bind("<<ComboboxSelected>>", on_combo_change)
    
    # 程式啟動時預設載入品項資料（combo_box 預設為「品項」）
    # 使用 after 確保視窗完全初始化後才載入資料
    def init_combo_data():
        """初始化 combo 資料"""
        import main as app
        app.load_item_data()  # 重新載入確保資料最新
        app.load_customer_data()  # 重新載入確保資料最新
        on_combo_change(None)
        print("✓ InfoSet 視窗已初始化並載入資料")
    
    parent.after(100, init_combo_data)

    # 資料庫同步：先清空再寫入當前記憶體資料
    def save_all_to_db_and_close():
        import main as app

        try:
            conn_cust = sqlite3.connect("CustomerID.db")
            cur_cust = conn_cust.cursor()
            cur_cust.execute("DELETE FROM customers")
            cur_cust.executemany("INSERT INTO customers (name) VALUES (?)",
                                 [(name,) for name in app.CustomerID])
            conn_cust.commit()
            conn_cust.close()
            print(f"✓ 已同步 {len(app.CustomerID)} 筆客戶至 CustomerID.db")
        except sqlite3.OperationalError as e:
            messagebox.showerror("錯誤", f"寫入 CustomerID.db 失敗: {e}")

        try:
            conn_item = sqlite3.connect("ItemValue.db")
            cur_item = conn_item.cursor()
            cur_item.execute("DELETE FROM items")
            cur_item.executemany("INSERT INTO items (name, price) VALUES (?, ?)",
                                 [(n, float(p)) for n, p in app.ItemValue.items()])
            conn_item.commit()
            conn_item.close()
            print(f"✓ 已同步 {len(app.ItemValue)} 筆品項至 ItemValue.db")
        except sqlite3.OperationalError as e:
            messagebox.showerror("錯誤", f"寫入 ItemValue.db 失敗: {e}")

        parent.destroy()
    
    # 建立底部 frame 放 buttons
    bottom_frame = tk.Frame(main_frame)
    bottom_frame.pack(fill=tk.X, padx=5, pady=5)
    
    # 建立三個 buttons，寬度各為 1/3
    button_width = 15  # 設置按鈕寬度，確保 3 個按鈕能均勻分配
    button_height = 3  # 按鈕高度放大3倍
    
    def on_btn_add_click():
        """btn_add 按鈕的回調函式"""
        selected_type = combo_box.get()
        name_value = name_entry.get().strip()

        if selected_type == "客戶":
            # 檢查名稱欄位是否為空
            if not name_value:
                messagebox.showwarning("警告", "客戶名稱不能為空白")
                return
            
            # 檢查是否有相同名稱
            import main as app
            if name_value in app.CustomerID:
                messagebox.showwarning("警告", "已有相同名稱")
                return
            
            # 將新客戶名稱加入陣列
            app.CustomerID.append(name_value)
            messagebox.showinfo("成功", f"已新增客戶: {name_value}")
            print(f"✓ 已新增客戶: {name_value}")
            
            # 更新 dataCombo
            dataCombo['values'] = app.CustomerID
            name_entry.delete(0, tk.END)
            value_entry.delete(0, tk.END)

        elif selected_type == "品項":
            # 檢查名稱欄位是否為空
            if not name_value:
                messagebox.showwarning("警告", "品項名稱不能為空白")
                return

            # 檢查是否有相同名稱
            import main as app
            if name_value in app.ItemValue:
                messagebox.showwarning("警告", "已有相同名稱")
                return

            # 檢查價格欄位是否為空
            price_value = value_entry.get().strip()
            if not price_value:
                messagebox.showwarning("警告", "請輸入價格")
                return

            # 將新品項加入陣列
            try:
                price_float = float(price_value)
                app.ItemValue[name_value] = price_float
                messagebox.showinfo("成功", f"已新增品項: {name_value}, 價格: {price_float}")
                print(f"✓ 已新增品項: {name_value}, 價格: {price_float}")

                # 更新 dataCombo
                items = list(app.ItemValue.keys())
                dataCombo['values'] = items
                name_entry.delete(0, tk.END)
                value_entry.delete(0, tk.END)
            except ValueError:
                messagebox.showerror("錯誤", "價格必須為數字")
    
    def on_btn_edit_click():
        """btn_edit 按鈕的回調函式（品項模式）"""
        selected_type = combo_box.get()
        
        if selected_type == "品項":
            name_value = name_entry.get().strip()
            
            # 1. name_entry為空白則無作用
            if not name_value:
                return
            
            import main as app
            
            # 2. name_entry不符合itemvalue{}內的任何name欄時，跳出[無該品項]
            if name_value not in app.ItemValue:
                messagebox.showwarning("警告", "無該品項")
                return
            
            value_value = value_entry.get().strip()
            
            # 3. value_entry為空白時，顯示[請輸入價格]
            if not value_value:
                messagebox.showwarning("警告", "請輸入價格")
                return
            
            # 4. 將value_entry的值，覆蓋至itemvalue{}中的name欄相同之price值
            try:
                price_float = float(value_value)
                app.ItemValue[name_value] = price_float
                messagebox.showinfo("成功", f"已修改品項: {name_value}, 新價格: {price_float}")
                print(f"✓ 已修改品項: {name_value}, 新價格: {price_float}")
                
                # 清空輸入欄位
                name_entry.delete(0, tk.END)
                value_entry.delete(0, tk.END)
            except ValueError:
                messagebox.showerror("錯誤", "價格必須為數字")
    
    btn_add = tk.Button(bottom_frame, text="新增", width=button_width, height=button_height, font=("Arial", 16), command=on_btn_add_click)
    btn_add.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=2)
    
    btn_edit = tk.Button(bottom_frame, text="修改", width=button_width, height=button_height, font=("Arial", 16), command=on_btn_edit_click)
    btn_edit.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=2)

    def on_btn_delete_click():
        """btn_delete 按鈕的回調函式"""
        selected_type = combo_box.get()
        name_value = name_entry.get().strip()

        import main as app

        if not name_value:
            return  # 空白時不動作

        if selected_type == "品項":
            if name_value not in app.ItemValue:
                messagebox.showwarning("警告", "無該品項")
                return

            # 刪除品項並更新 UI
            del app.ItemValue[name_value]
            items = list(app.ItemValue.keys())
            dataCombo['values'] = items
            name_entry.delete(0, tk.END)
            value_entry.delete(0, tk.END)
            messagebox.showinfo("成功", f"已刪除品項: {name_value}")
            print(f"✓ 已刪除品項: {name_value}")

        elif selected_type == "客戶":
            if name_value not in app.CustomerID:
                messagebox.showwarning("警告", "無此客戶")
                return

            # 刪除客戶並更新 UI
            app.CustomerID.remove(name_value)
            dataCombo['values'] = app.CustomerID
            name_entry.delete(0, tk.END)
            value_entry.delete(0, tk.END)
            messagebox.showinfo("成功", f"已刪除客戶: {name_value}")
            print(f"✓ 已刪除客戶: {name_value}")

    btn_delete = tk.Button(bottom_frame, text="刪除", width=button_width, height=button_height, font=("Arial", 16), command=on_btn_delete_click)
    btn_delete.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=2)

    # 關閉視窗時先同步資料庫
    parent.protocol("WM_DELETE_WINDOW", save_all_to_db_and_close)
    
    return main_frame, combo_box, content_frame, btn_add, btn_edit, btn_delete, dataCombo, name_entry, value_entry


if __name__ == "__main__":
    # 測試
    root = tk.Tk()
    root.title("資訊設置")
    root.geometry("700x550")
    
    result = create_info_frame(root)
    main_frame, combo_box, content_frame, btn_add, btn_edit, btn_delete, dataCombo, name_entry, value_entry = result
    
    root.mainloop()