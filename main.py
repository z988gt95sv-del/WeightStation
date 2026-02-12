import tkinter as tk
from tkinter import ttk, messagebox
from InfoSet import create_info_frame
from AddCargo import CargoInputFrame, CustomerFrame
from NoPad import NumericKeypad
import sqlite3
import os
import re
import threading
import gc
from datetime import datetime, timedelta
import sys

# PyInstaller 應用路徑修復
# 當應用由 PyInstaller 打包執行時，需要將工作目錄設置為資源目錄
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    # PyInstaller 打包的應用
    os.chdir(sys._MEIPASS)
    print(f"[PyInstaller] 工作目錄已設置為: {os.getcwd()}")

# 宣告可擴充式陣列（全域，供其他模組匯入使用）
CustomerID = []  # 儲存客戶ID（文字格式）
ItemValue = {}  # 儲存項目名稱和價格：{"項目名稱": 價格(float)}
StockInHand = []  # 儲存與 stockinhand.db 相同欄位結構的紀錄陣列 (list of dict)
_data_loaded = False  # 標記是否已初始化過資料
today = datetime.now().strftime("%Y-%m-%d")  # 目前選擇的日期（全域）
checkout_click_count = {}  # 追蹤每筆資料的結帳點擊次數 {number: count}
active_threads = []  # 追蹤活躍的執行緒

# 資料庫載入函式
def load_customer_data():
    """從 CustomerID.db 載入客戶名稱至 CustomerID 陣列"""
    global CustomerID
    try:
        conn = sqlite3.connect("CustomerID.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM customers ORDER BY id")
        CustomerID = [row[0] for row in cursor.fetchall()]
        conn.close()
        print(f"✓ 已載入 {len(CustomerID)} 筆客戶資料: {CustomerID}")
    except sqlite3.OperationalError:
        print("✗ 無法連接 CustomerID.db，請先執行 create_databases.py")
        CustomerID = []

def load_item_data():
    """從 ItemValue.db 載入商品名稱與價格至 ItemValue 字典"""
    global ItemValue
    try:
        conn = sqlite3.connect("ItemValue.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name, price FROM items")
        ItemValue = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        print(f"✓ 已載入 {len(ItemValue)} 筆商品資料: {ItemValue}")
    except sqlite3.OperationalError:
        print("✗ 無法連接 ItemValue.db，請先執行 create_databases.py")
        ItemValue = {}


def init_data_once():
    """模組匯入時初始化資料，只執行一次。"""
    global _data_loaded
    if _data_loaded:
        return
    ensure_databases()
    load_customer_data()
    load_item_data()
    _data_loaded = True


def ensure_databases():
    """如果資料庫不存在，建立必要的表格"""
    if not os.path.exists("CustomerID.db"):
        conn = sqlite3.connect("CustomerID.db")
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
            """
        )
        conn.commit()
        conn.close()

    if not os.path.exists("ItemValue.db"):
        conn = sqlite3.connect("ItemValue.db")
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                price REAL NOT NULL
            )
            """
        )
        conn.commit()
        conn.close()

    if not os.path.exists("stockinhand.db"):
        conn = sqlite3.connect("stockinhand.db")
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS stockinhand (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inout INTEGER,
                date TEXT,
                number TEXT,
                name TEXT,
                carno TEXT,
                closeflag INTEGER,
                fluctuation INTEGER
            )
            """
        )
        # 創建品項詳情表
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS item_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stockinhand_id INTEGER,
                seq INTEGER,
                item TEXT,
                heavy FLOAT,
                empty FLOAT,
                grossw FLOAT,
                minus FLOAT,
                netw FLOAT,
                account FLOAT,
                total FLOAT,
                price FLOAT,
                FOREIGN KEY (stockinhand_id) REFERENCES stockinhand(id) ON DELETE CASCADE
            )
            """
        )
        conn.commit()
        conn.close()
    else:
        # 檢查並升級現有資料庫
        conn = sqlite3.connect("stockinhand.db")
        cursor = conn.cursor()
        
        # 檢查 stockinhand 表是否有 item 欄位（舊結構）
        cursor.execute("PRAGMA table_info(stockinhand)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "item" in columns:
            # 需要升級資料庫結構
            print("✓ 偵測到舊的資料庫結構，正在升級...")
            
            # 創建新的 stockinhand 表
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS stockinhand_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    inout INTEGER,
                    date TEXT,
                    number TEXT,
                    name TEXT,
                    carno TEXT,
                    closeflag INTEGER,
                    fluctuation INTEGER
                )
                """
            )
            
            # 創建 item_details 表
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS item_details (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stockinhand_id INTEGER,
                    seq INTEGER,
                    item TEXT,
                    heavy FLOAT,
                    empty FLOAT,
                    grossw FLOAT,
                    minus FLOAT,
                    netw FLOAT,
                    account FLOAT,
                    total FLOAT,
                    price FLOAT,
                    FOREIGN KEY (stockinhand_id) REFERENCES stockinhand(id) ON DELETE CASCADE
                )
                """
            )
            
            # 遷移舊資料
            cursor.execute(
                """
                SELECT id, inout, date, number, name, carno, item, heavy, empty, grossw, minus, netw, account, total, price, closeflag, fluctuation
                FROM stockinhand
                """
            )
            old_records = cursor.fetchall()
            
            for record in old_records:
                rid, inout, rdate, number, name, carno, item, heavy, empty, grossw, minus, netw, account, total, price, closeflag, fluctuation = record
                
                # 插入到新的 stockinhand 表
                cursor.execute(
                    """
                    INSERT INTO stockinhand_new (id, inout, date, number, name, carno, closeflag, fluctuation)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (rid, inout, rdate, number, name, carno, closeflag, fluctuation)
                )
                
                # 如果有品項資料，插入到 item_details 表
                if item:
                    cursor.execute(
                        """
                        INSERT INTO item_details (stockinhand_id, seq, item, heavy, empty, grossw, minus, netw, account, total, price)
                        VALUES (?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (rid, item, heavy, empty, grossw, minus, netw, account, total, price)
                    )
            
            # 刪除舊表並重命名
            cursor.execute("DROP TABLE stockinhand")
            cursor.execute("ALTER TABLE stockinhand_new RENAME TO stockinhand")
            
            conn.commit()
            print("✓ 資料庫升級完成")
        
        conn.close()


def cleanup_resources():
    """清理所有資源：執行緒、記憶體、資料庫連接等"""
    global CustomerID, ItemValue, StockInHand, checkout_click_count, active_threads, _data_loaded
    
    print("✓ 開始清理資源...")
    
    # 停止所有活躍的執行緒
    for thread_info in active_threads:
        if 'stop_event' in thread_info:
            thread_info['stop_event'].set()
        if 'serial' in thread_info:
            try:
                thread_info['serial'].close()
                print("✓ 已關閉序列埠連接")
            except Exception:
                pass
    
    # 等待執行緒結束（最多等待 1 秒）
    for thread_info in active_threads:
        if 'thread' in thread_info:
            thread_info['thread'].join(timeout=1.0)
    
    active_threads.clear()
    
    # 清空全域變數
    CustomerID.clear()
    ItemValue.clear()
    StockInHand.clear()
    checkout_click_count.clear()
    _data_loaded = False
    
    print("✓ 已清空全域資料")
    
    # 強制執行垃圾回收
    gc.collect()
    print("✓ 已執行垃圾回收")
    print("✓ 資源清理完成")


def create_app():
    """建立主視窗並回傳 root，匯入時不會直接啟動 GUI。"""
    root = tk.Tk()
    root.title("Left-Right Frame Layout")
    root.geometry("1200x800")

    def configure_toplevel(win, on_close=None):
        """統一處理子視窗關閉與記憶體釋放。"""
        if on_close is None:
            on_close = win.destroy
        win.protocol("WM_DELETE_WINDOW", on_close)
        win.bind("<Destroy>", lambda e, w=win: gc.collect() if e.widget is w else None)
    
    def on_closing():
        """視窗關閉時的回調函數"""
        if messagebox.askokcancel("確認退出", "確定要關閉程式嗎？"):
            cleanup_resources()
            root.destroy()
    
    # 設置視窗關閉協議
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.title("Left-Right Frame Layout")
    root.geometry("1200x800")

    # 創建左邊 frame（寬度為右邊的 9 倍）
    left_frame = tk.Frame(root, bg="lightblue")
    left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # 在左邊 frame 內部分為上下兩部分（50:50 比例）
    top_frame = tk.Frame(left_frame, bg="lightblue")
    top_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

    # 在 top_frame 內分為左右兩部分（左側可擴展，右側固定寬度）
    top_left_frame = tk.Frame(top_frame, bg="lightgreen")
    top_left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    top_right_frame = tk.Frame(top_frame, bg="lightsteelblue", width=450, height=250)
    top_right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False)
    top_right_frame.pack_propagate(False)  # 防止內容改變 frame 大小

    # 根據 ItemValue 建立商品按鈕
    def create_item_buttons(on_click_callback=None):
        """根據 ItemValue 字典動態生成商品按鈕"""
        # 清除舊按鈕
        for widget in top_right_frame.winfo_children():
            widget.destroy()
        
        items = list(ItemValue.keys())
        # 固定按鈕尺寸
        button_width = 100  # 固定寬度（像素）
        button_height = 75  # 固定高度（像素）
        padding = 5  # 按鈕間距
        
        for idx, item_name in enumerate(items):
            row = idx // 4  # 每行4個按鈕
            col = idx % 4   # 列索引 (0-3)
            
            # 計算按鈕的絕對位置
            x = col * (button_width + padding) + padding
            y = row * (button_height + padding) + padding
            
            cmd = (lambda name=item_name: on_click_callback(name)) if on_click_callback else None
            
            btn = tk.Button(
                top_right_frame,
                text=item_name,
                font=("Arial", 12),
                bg="lightblue",
                relief=tk.RAISED,
                bd=2,
                command=cmd,
                width=12,
                height=2
            )
            btn.place(x=x, y=y, width=button_width, height=button_height)
    
    # 首次載入時建立按鈕
    top_right_frame.after(100, create_item_buttons)

    bottom_frame = tk.Frame(left_frame, bg="lightyellow")
    bottom_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, padx=10, pady=10)

    # bottom frame 左上角 toggle switch
    toggle_var = tk.BooleanVar(value=False)

    def update_toggle():
        if toggle_var.get():
            toggle_button.config(text="ON", bg="#4caf50", activebackground="#4caf50", fg="white")
        else:
            toggle_button.config(text="OFF", bg="#dddddd", activebackground="#dddddd", fg="black")

    toggle_button = tk.Checkbutton(
        bottom_frame,
        text="OFF",
        variable=toggle_var,
        onvalue=True,
        offvalue=False,
        indicatoron=False,
        width=14,
        height=2,
        command=update_toggle,
        bg="#dddddd",
        fg="black",
        selectcolor="#4caf50",
        font=("Arial", 12, "bold"),
    )
    toggle_button.place(x=10, y=10, anchor="nw")
    update_toggle()

    # 在 toggle_button 旁邊添加[新增品項]和[刪除品項]按鈕
    def on_add_item():
        """新增一筆空白品項到選中的交易記錄"""
        selection = top_left_tree.selection()
        if not selection:
            messagebox.showinfo("提示", "請先選擇左上表格資料")
            return
        
        item = selection[0]
        values = top_left_tree.item(item, "values")
        if not values:
            messagebox.showinfo("提示", "請先選擇左上表格資料")
            return
        
        selected_number = values[0]
        selected_record = None
        for record in StockInHand:
            if record.get("number") == selected_number:
                selected_record = record
                break
        
        if not selected_record:
            messagebox.showerror("錯誤", "找不到選取的資料")
            return
        
        # 檢查 closeflag，如果為 1 則不允許新增品項
        if selected_record.get('closeflag') == 1:
            messagebox.showwarning("提示", "該筆資料已結帳，已被鎖定，無法新增品項")
            return
        
        # 計算新品項的序列號
        seq = len(selected_record.get("items", [])) + 1
        
        try:
            conn = sqlite3.connect("stockinhand.db")
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO item_details (stockinhand_id, seq, item, price, heavy, empty, grossw, minus, netw, account, total)
                VALUES (?, ?, '', 0, 0, 0, 0, 0, 0, 0, 0)
                """,
                (selected_record.get("id"), seq)
            )
            conn.commit()
            new_item_id = cursor.lastrowid
            conn.close()
        except sqlite3.OperationalError as e:
            messagebox.showerror("錯誤", f"新增失敗: {e}")
            return
        
        # 新增到記憶體中
        selected_record["items"].append((new_item_id, seq, "", 0, 0, 0, 0, 0, 0, 0, 0))
        
        # 重新繪製表格並重新選擇
        render_stockinhand_tree()
        for tree_item in top_left_tree.get_children():
            if top_left_tree.item(tree_item, "values")[0] == selected_number:
                top_left_tree.selection_set(tree_item)
                top_left_tree.see(tree_item)
                on_top_left_tree_select(None)
                break
    
    btn_add_item = tk.Button(
        bottom_frame,
        text="新增品項",
        width=14,
        height=2,
        bg="black",
        fg="white",
        font=("Arial", 12, "bold"),
        command=on_add_item
    )
    btn_add_item.place(x=130, y=10, anchor="nw")

    btn_del_item = tk.Button(
        bottom_frame,
        text="刪除品項",
        width=14,
        height=2,
        bg="black",
        fg="white",
        font=("Arial", 12, "bold"),
        command=lambda: delete_selected_item()
    )
    btn_del_item.place(x=250, y=10, anchor="nw")

    def delete_selected_item():
        """刪除下方表格所選取的品項"""
        global StockInHand
        
        table_selection = tree.selection()
        if not table_selection:
            messagebox.showinfo("提示", "請先選擇要刪除的品項")
            return
        
        selection = top_left_tree.selection()
        if not selection:
            messagebox.showinfo("提示", "請先選擇左上表格資料")
            return
        
        item = selection[0]
        values = top_left_tree.item(item, "values")
        if not values:
            messagebox.showinfo("提示", "請先選擇左上表格資料")
            return
        
        selected_number = values[0]
        selected_record = None
        for record in StockInHand:
            if record.get("number") == selected_number:
                selected_record = record
                break
        
        if not selected_record:
            messagebox.showerror("錯誤", "找不到選取的資料")
            return
        
        # 檢查 closeflag，如果為 1 則不允許刪除品項
        if selected_record.get('closeflag') == 1:
            messagebox.showwarning("提示", "該筆資料已結帳，已被鎖定，無法刪除品項")
            return
        
        # 取得 table_frame 中選中的行索引
        item_index = 0
        for idx, tree_item in enumerate(tree.get_children()):
            if tree_item == table_selection[0]:
                item_index = idx
                break
        
        items = selected_record.get("items", [])
        if item_index >= len(items):
            messagebox.showerror("錯誤", "找不到選中的品項")
            return
        
        selected_item = items[item_index]
        item_id = selected_item[0]
        item_name = selected_item[2]
        
        confirm = messagebox.askyesno(
            "確認刪除",
            f"確定要刪除品項 {item_name if item_name else '(空白)'} 嗎？",
            icon='warning',
            default=messagebox.NO
        )
        
        if not confirm:
            return
        
        try:
            conn = sqlite3.connect("stockinhand.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM item_details WHERE id = ?", (item_id,))
            conn.commit()
            conn.close()
        except sqlite3.OperationalError as e:
            messagebox.showerror("錯誤", f"刪除失敗: {e}")
            return
        
        # 從記憶體中移除
        selected_record["items"].pop(item_index)
        
        render_stockinhand_tree()
        
        # 重新選擇同一行
        for tree_item in top_left_tree.get_children():
            if top_left_tree.item(tree_item, "values")[0] == selected_number:
                top_left_tree.selection_set(tree_item)
                top_left_tree.see(tree_item)
                on_top_left_tree_select(None)
                break

    # bottom frame 表格（類似 Excel 的欄位）
    table_frame = ttk.Frame(bottom_frame)
    table_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=(50, 10))

    columns = ("品項", "價格", "重車", "空車", "貨重", "扣重", "淨重", "小計")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=5)
    
    # 在此處先定義 tree，供後續的事件處理器使用
    selected_cell_column = None  # 追蹤用戶點擊的列

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=90, anchor="center")
    
    # 配置交替行背景色
    tree.tag_configure('evenrow', background='#E8F4F8')
    tree.tag_configure('oddrow', background='#FFFFFF')

    # 將欄位標題與內容字體調為原本的 2 倍，並加大列高避免裁切
    style = ttk.Style()
    style.configure("Treeview.Heading", font=("Arial", 18))
    style.configure("Treeview", font=("Arial", 20), rowheight=20)

    # 添加左側垂直滾動條
    table_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    table_scrollbar.pack(side=tk.LEFT, fill=tk.Y)
    tree.configure(yscrollcommand=table_scrollbar.set)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # 佈局使用 place 的 toggle 不會受 pack 影響，這裡用 pack 讓表格貼齊寬度

    def on_tree_click(event):
        """處理表格單擊事件，記錄點擊的列"""
        nonlocal selected_cell_column
        item = tree.identify_row(event.y)
        col = tree.identify_column(event.x)
        
        if item and col:
            col_index = int(col.replace('#', '')) - 1
            if 0 <= col_index < len(columns):
                col_name = columns[col_index]
                if col_name in ("品項", "價格", "重車", "空車", "扣重"):
                    # 先選擇該行
                    tree.selection_set(item)
                    selected_cell_column = col_name
                    print(f"選中列: {col_name}")
    
    def on_tree_double_click(event):
        """處理表格雙擊事件，直接執行修改"""
        nonlocal selected_cell_column
        item = tree.identify_row(event.y)
        col = tree.identify_column(event.x)
        
        if item and col:
            col_index = int(col.replace('#', '')) - 1
            if 0 <= col_index < len(columns):
                col_name = columns[col_index]
                if col_name in ("品項", "價格", "重車", "空車", "扣重"):
                    # 先選擇該行並設定 selected_cell_column
                    tree.selection_set(item)
                    selected_cell_column = col_name
                    print(f"雙擊列: {col_name}")
                    
                    # 根據欄位類型執行對應的修改功能
                    if col_name == "品項":
                        open_edit_item()
                    else:
                        open_edit_numeric()
    
    tree.bind("<Button-1>", on_tree_click)
    tree.bind("<Double-Button-1>", on_tree_double_click)

    # 設置按鈕行為：開啟 InfoSet 為模態視窗，期間停用主視窗操作
    def open_info_set():
        infoset_win = tk.Toplevel(root)
        infoset_win.title("資訊設置")
        infoset_win.geometry("700x550")
        result = create_info_frame(infoset_win)
        configure_toplevel(infoset_win)
        infoset_win.transient(root)  # 置於主視窗之上
        infoset_win.grab_set()       # 取得輸入焦點，成為模態
        infoset_win.focus_set()
        root.wait_window(infoset_win)  # 等待關閉後才恢復主視窗
        
        # 關閉 InfoSet 後重新從資料庫載入資料並更新商品按鈕
        load_item_data()
        load_customer_data()
        create_item_buttons()
        print("✓ 已重新載入資料並更新商品按鈕")

    def open_add_cargo():
        """開啟 AddCargo 視窗為模態視窗"""
        # 確保資料已加載
        init_data_once()
        print(f"DEBUG: 打開 AddCargo 前，CustomerID = {CustomerID}")
        
        # 檢查日期是否為當日
        system_date = datetime.now().strftime("%Y-%m-%d")
        if today != system_date:
            # 創建自定義對話框
            date_check_win = tk.Toplevel(root)
            date_check_win.title("提示")
            date_check_win.geometry("500x300")
            date_check_win.resizable(False, False)
            date_check_win.transient(root)
            date_check_win.grab_set()
            
            # 置中顯示
            date_check_win.update_idletasks()
            x = root.winfo_x() + (root.winfo_width() - date_check_win.winfo_width()) // 2
            y = root.winfo_y() + (root.winfo_height() - date_check_win.winfo_height()) // 2
            date_check_win.geometry(f"+{x}+{y}")
            
            # 主容器
            main_container = tk.Frame(date_check_win, bg="white")
            main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
            
            # 上層容器（把文字推高）
            upper_container = tk.Frame(main_container, bg="white")
            upper_container.pack(fill=tk.BOTH, expand=True)
            
            # 警告文字
            warning_label = tk.Label(
                upper_container,
                text="新增資料非當日日期",
                font=("Arial", 28, "bold"),
                fg="red",
                bg="white"
            )
            warning_label.pack(pady=20, expand=True)
            
            # 按鈕容器（置底置中）
            button_container = tk.Frame(main_container, bg="white")
            button_container.pack(fill=tk.X, pady=10)
            
            # 內部容器用來置中按鈕
            inner_button_frame = tk.Frame(button_container, bg="white")
            inner_button_frame.pack(expand=True)
            
            def on_continue():
                date_check_win.destroy()
                # 執行新增動作
                _open_add_cargo_impl()
            
            def on_cancel():
                date_check_win.destroy()
            
            # 繼續按鈕
            continue_btn = tk.Button(
                inner_button_frame,
                text="繼續",
                font=("Arial", 16, "bold"),
                width=12,
                height=2,
                bg="#4caf50",
                fg="white",
                command=on_continue
            )
            continue_btn.pack(side=tk.LEFT, padx=15)
            
            # 取消按鈕
            cancel_btn = tk.Button(
                inner_button_frame,
                text="取消",
                font=("Arial", 16, "bold"),
                width=12,
                height=2,
                bg="#f44336",
                fg="white",
                command=on_cancel
            )
            cancel_btn.pack(side=tk.LEFT, padx=15)
            
            root.wait_window(date_check_win)
        else:
            # 日期為當日，直接執行新增
            _open_add_cargo_impl()
    
    def _open_add_cargo_impl():
        """實際的新增 AddCargo 視窗邏輯"""
        add_cargo_win = tk.Toplevel(root)
        add_cargo_win.title("貨物輸入系統")
        add_cargo_win.geometry("1024x768")
        add_cargo_win.resizable(False, False)
        
        # 定義關閉視窗的回調函數
        def on_cancel_close():
            add_cargo_win.destroy()

        configure_toplevel(add_cargo_win, on_close=on_cancel_close)
        
        # 設置標籤頁樣式
        style = ttk.Style()
        style.configure('TNotebook.Tab', 
                        font=('Arial', 24, 'bold'),
                        padding=[60, 20])
        
        # 建立 Notebook（標籤頁容器）
        notebook = ttk.Notebook(add_cargo_win)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # 第一個標籤頁：車牌輸入
        cargo_frame = tk.Frame(notebook)
        cargo_frame.pack(fill=tk.BOTH, expand=True)
        cargo_app = CargoInputFrame(cargo_frame, on_cancel_callback=on_cancel_close)
        notebook.add(cargo_frame, text="車牌")
        
        # 第二個標籤頁：廠商選擇
        customer_frame = tk.Frame(notebook)
        customer_frame.pack(fill=tk.BOTH, expand=True)
        customer_app = CustomerFrame(customer_frame, CustomerID, on_cancel_callback=on_cancel_close)
        notebook.add(customer_frame, text="廠商")

        def on_confirm_save_and_close():
            add_stockinhand_record(cargo_app, customer_app)
            add_cargo_win.destroy()

        cargo_app.on_confirm_callback = on_confirm_save_and_close
        customer_app.on_confirm_callback = on_confirm_save_and_close
        
        add_cargo_win.transient(root)  # 置於主視窗之上
        add_cargo_win.grab_set()       # 取得輸入焦點，成為模態
        add_cargo_win.focus_set()
        root.wait_window(add_cargo_win)  # 等待關閉後才恢復主視窗

    # 創建右邊 frame（寬度為左邊的 1/9）
    right_frame = tk.Frame(root, bg="lightcoral", width=90)
    right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False)
    right_frame.pack_propagate(False)

    # 右側按鈕區域加入垂直捲動
    right_canvas = tk.Canvas(right_frame, borderwidth=0, highlightthickness=0)
    right_scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=right_canvas.yview)
    right_buttons_frame = tk.Frame(right_canvas, bg="lightcoral")
    right_buttons_frame_id = right_canvas.create_window((0, 0), window=right_buttons_frame, anchor="nw")

    right_canvas.configure(yscrollcommand=right_scrollbar.set)
    right_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    right_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _on_right_buttons_configure(event):
        right_canvas.configure(scrollregion=right_canvas.bbox("all"))

    def _on_right_canvas_configure(event):
        right_canvas.itemconfig(right_buttons_frame_id, width=event.width)

    def _on_right_mousewheel(event):
        # macOS MouseWheel delta is in event.delta
        right_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _bind_right_mousewheel(event):
        right_canvas.bind_all("<MouseWheel>", _on_right_mousewheel)

    def _unbind_right_mousewheel(event):
        right_canvas.unbind_all("<MouseWheel>")

    right_buttons_frame.bind("<Configure>", _on_right_buttons_configure)
    right_canvas.bind("<Configure>", _on_right_canvas_configure)
    right_canvas.bind("<Enter>", _bind_right_mousewheel)
    right_canvas.bind("<Leave>", _unbind_right_mousewheel)
    right_buttons_frame.bind("<Enter>", _bind_right_mousewheel)
    right_buttons_frame.bind("<Leave>", _unbind_right_mousewheel)

    # 在左邊上半部左側 frame 添加日期欄位（最左上）
    global today
    date_label = tk.Label(top_left_frame, text=today, bg="lightgreen", font=("Arial", 16), anchor="w", cursor="hand2")
    date_label.pack(fill=tk.X, padx=10, pady=10)
    
    def open_date_picker():
        """開啟日期選擇對話框"""
        global today
        
        date_win = tk.Toplevel(root)
        date_win.title("選擇日期")
        date_win.geometry("300x150")
        date_win.resizable(False, False)
        configure_toplevel(date_win)
        
        # 日期輸入框
        tk.Label(date_win, text="請輸入日期 (YYYY-MM-DD):", font=("Arial", 14)).pack(pady=10)
        date_input_frame = tk.Frame(date_win)
        date_input_frame.pack(pady=10)

        def change_days(delta):
            try:
                current_date = datetime.strptime(date_entry.get().strip(), "%Y-%m-%d")
                new_date = current_date + timedelta(days=delta)
                today_date = datetime.now().date()
                if new_date.date() > today_date:
                    new_date = datetime.combine(today_date, datetime.min.time())
                date_entry.delete(0, tk.END)
                date_entry.insert(0, new_date.strftime("%Y-%m-%d"))
            except ValueError:
                messagebox.showerror("錯誤", "日期格式不正確，請使用 YYYY-MM-DD 格式")

        tk.Button(
            date_input_frame,
            text="◀",
            font=("Arial", 14),
            width=3,
            command=lambda: change_days(-1),
        ).pack(side=tk.LEFT, padx=5)

        date_entry = tk.Entry(date_input_frame, font=("Arial", 16), justify="center", width=12)
        date_entry.insert(0, today)
        date_entry.pack(side=tk.LEFT, padx=5)
        date_entry.focus()

        tk.Button(
            date_input_frame,
            text="▶",
            font=("Arial", 14),
            width=3,
            command=lambda: change_days(1),
        ).pack(side=tk.LEFT, padx=5)
        
        def confirm_date():
            global today
            new_date = date_entry.get().strip()
            # 簡單驗證日期格式
            try:
                parsed_date = datetime.strptime(new_date, "%Y-%m-%d")
                today_date = datetime.now().date()
                if parsed_date.date() > today_date:
                    parsed_date = datetime.combine(today_date, datetime.min.time())
                today = parsed_date.strftime("%Y-%m-%d")
                date_label.config(text=today)
                load_today_records()
                date_win.destroy()
            except ValueError:
                messagebox.showerror("錯誤", "日期格式不正確，請使用 YYYY-MM-DD 格式")
        
        # 確定和取消按鈕
        btn_frame = tk.Frame(date_win)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="確定", font=("Arial", 12), bg="#4caf50", fg="white",
                  width=10, command=confirm_date).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="取消", font=("Arial", 12), bg="#f44336", fg="white",
                  width=10, command=date_win.destroy).pack(side=tk.LEFT, padx=5)
        
        # 綁定 Enter 鍵
        date_entry.bind("<Return>", lambda e: confirm_date())
        
        date_win.transient(root)
        date_win.grab_set()
        date_win.focus_set()
        root.wait_window(date_win)
    
    # 綁定點擊事件
    date_label.bind("<Button-1>", lambda e: open_date_picker())

    # 在日期下方插入工作表
    top_left_table_frame = ttk.Frame(top_left_frame)
    top_left_table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    top_left_columns = ("編號", "車牌", "廠商", "交易額")
    top_left_tree = ttk.Treeview(top_left_table_frame, columns=top_left_columns, show="headings", height=8)

    for col in top_left_columns:
        top_left_tree.heading(col, text=col)
        top_left_tree.column(col, width=100, anchor="center")
    
    # 配置交替行背景色
    top_left_tree.tag_configure('evenrow', background='#F0F0F0')
    top_left_tree.tag_configure('oddrow', background='#FFFFFF')
    # 配置已結帳行的紅色字體
    top_left_tree.tag_configure('closeflag_row', background='#FFE0E0', foreground='#FF0000', font=("Arial", 20, "bold"))

    # 設置工作表字體
    style = ttk.Style()
    style.configure("Treeview.Heading", font=("Arial", 20))
    style.configure("Treeview", font=("Arial", 20), rowheight=25)

    # 添加左側垂直滾動條
    top_left_scrollbar = ttk.Scrollbar(top_left_table_frame, orient="vertical", command=top_left_tree.yview)
    top_left_scrollbar.pack(side=tk.LEFT, fill=tk.Y)
    top_left_tree.configure(yscrollcommand=top_left_scrollbar.set)
    top_left_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def on_top_left_tree_select(event):
        """當點選 top_left_tree 的一行時，顯示詳細資料到 table_frame 的樹"""
        nonlocal selected_cell_column
        
        selection = top_left_tree.selection()
        if not selection:
            return
        
        # 重置 selected_cell_column
        selected_cell_column = None
        
        # 獲取選中行的值
        item = selection[0]
        values = top_left_tree.item(item, 'values')
        if not values:
            return
        
        # 第一個值是 number
        selected_number = values[0]
        
        # 在 StockInHand 中找到對應的記錄
        selected_record = None
        for record in StockInHand:
            if record.get("number") == selected_number:
                selected_record = record
                break
        
        if not selected_record:
            return
        
        # 清空 table_frame 中的 tree
        for tree_item in tree.get_children():
            tree.delete(tree_item)
        
        # 顯示所有品項
        items = selected_record.get("items", [])
        for idx, item_row in enumerate(items):
            item_id, seq, item_name, heavy, empty, grossw, minus, netw, account, total, price = item_row
            
            # 計算淨重：貨重 - 扣重
            grossw_val = grossw if grossw else 0.0
            minus_val = minus if minus else 0.0
            netw_val = grossw_val - minus_val
            
            # 小計 = 淨重 × 價格
            price_val = price if price else 0.0
            account_val = netw_val * price_val
            
            # 插入記錄的詳細資料
            tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
            tree.insert(
                "",
                "end",
                values=(
                    item_name or "",
                    f"{price_val:,.3f}".rstrip('0').rstrip('.') if price_val else "0",
                    f"{round(heavy):,}" if heavy else "0",
                    f"{round(empty):,}" if empty else "0",
                    f"{round(grossw_val):,}" if grossw_val else "0",
                    f"{minus_val:,.1f}".rstrip('0').rstrip('.') if minus_val else "0",
                    f"{netw_val:,.1f}".rstrip('0').rstrip('.') if netw_val else "0",
                    f"{round(account_val):,}",
                ),
                tags=(tag,)
            )
    
    # 綁定 top_left_tree 的點擊事件
    top_left_tree.bind("<<TreeviewSelect>>", on_top_left_tree_select)

    def on_top_left_tree_double_click(event):
        """雙擊僅選取，不觸發其他行為"""
        item = top_left_tree.identify_row(event.y)
        if item:
            top_left_tree.selection_set(item)
        return "break"

    top_left_tree.bind("<Double-Button-1>", on_top_left_tree_double_click)

    def render_stockinhand_tree():
        """依 StockInHand 內容更新左上表格"""
        # 先清除所有選取狀態，防止選取狀態錯亂
        top_left_tree.selection_remove(top_left_tree.selection())
        
        # 刪除所有項目
        for item in top_left_tree.get_children():
            top_left_tree.delete(item)

        # 重新插入所有項目
        for idx, record in enumerate(StockInHand):
            tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
            # 如果 closeflag=1，添加紅色字體標籤
            if record.get('closeflag') == 1:
                tag = 'closeflag_row'
            top_left_tree.insert(
                "",
                "end",
                values=(
                    record.get("number"),
                    record.get("carno"),
                    record.get("name"),
                    f"{round(record.get('total', 0.0)):,}",
                ),
                tags=(tag,)
            )

    # 載入今天的交易記錄
    def load_today_records():
        """從 stockinhand.db 載入今天的交易記錄到 StockInHand，並依 number 降冪顯示"""
        global StockInHand
        try:
            conn = sqlite3.connect("stockinhand.db")
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, inout, date, number, name, carno, closeflag, fluctuation
                FROM stockinhand
                WHERE date = ?
                """,
                (today,),
            )
            rows = cursor.fetchall()
            conn.close()

            # 將查詢結果轉成 dict 並存入全域陣列
            StockInHand = []
            for row in rows:
                (
                    rid,
                    inout,
                    rdate,
                    number,
                    name,
                    carno,
                    closeflag,
                    fluctuation,
                ) = row
                
                # 加載該交易的所有品項
                conn = sqlite3.connect("stockinhand.db")
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, seq, item, heavy, empty, grossw, minus, netw, account, total, price
                    FROM item_details
                    WHERE stockinhand_id = ?
                    ORDER BY seq
                    """,
                    (rid,)
                )
                item_rows = cursor.fetchall()
                conn.close()
                
                # 計算總交易額（所有品項的 淨重 × 價格 加總）
                total_account = 0.0
                for item_row in item_rows:
                    grossw_val = item_row[5] if item_row[5] else 0.0  # grossw
                    minus_val = item_row[6] if item_row[6] else 0.0  # minus
                    netw_val = grossw_val - minus_val  # 動態計算淨重
                    price_val = item_row[10] if item_row[10] else 0.0  # price
                    total_account += netw_val * price_val
                
                record = {
                    "id": rid,
                    "inout": inout,
                    "date": rdate,
                    "number": number,
                    "name": name,
                    "carno": carno,
                    "items": item_rows,  # 存儲品項列表
                    "total": total_account,
                    "closeflag": closeflag,
                    "fluctuation": fluctuation,
                }
                StockInHand.append(record)

            # 依 number 降冪排序
            StockInHand.sort(key=lambda r: r.get("number") or "", reverse=True)

            render_stockinhand_tree()

            print(f"✓ 已載入 {len(StockInHand)} 筆今日交易記錄 ({today})，並完成排序")
        except sqlite3.OperationalError as e:
            print(f"✗ 無法連接 stockinhand.db: {e}")

    def add_stockinhand_record(cargo_frame_app, customer_frame_app):
        """新增一筆 stockinhand 記錄，寫入陣列與資料庫"""
        global StockInHand

        entry1, entry2 = cargo_frame_app.get_entry_values()
        entry1 = (entry1 or "").strip()
        entry2 = (entry2 or "").strip()

        if entry1 and entry2:
            carno = f"{entry1}-{entry2}"
        elif entry1:
            carno = entry1
        elif entry2:
            carno = entry2
        else:
            carno = ""

        display_text = (customer_frame_app.get_display_text() or "").strip()
        if not display_text or display_text == "未選擇客戶":
            name = ""
        elif display_text.startswith("已選擇:"):
            name = display_text.replace("已選擇:", "", 1).strip()
        else:
            name = display_text

        def to_int(value):
            try:
                return int(str(value))
            except Exception:
                return 0

        max_num = 0
        for record in StockInHand:
            max_num = max(max_num, to_int(record.get("number")))
        next_number = str(max_num + 1).zfill(3)

        new_record = {
            "id": None,
            "inout": 0,
            "date": today,
            "number": next_number,
            "name": name,
            "carno": carno,
            "items": [],
            "total": 0.0,
            "closeflag": 0,
            "fluctuation": 0,
        }

        try:
            conn = sqlite3.connect("stockinhand.db")
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO stockinhand (
                    inout, date, number, name, carno,
                    closeflag, fluctuation
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    new_record["inout"],
                    new_record["date"],
                    new_record["number"],
                    new_record["name"],
                    new_record["carno"],
                    new_record["closeflag"],
                    new_record["fluctuation"],
                ),
            )
            new_record["id"] = cursor.lastrowid
            conn.commit()
            conn.close()
        except sqlite3.OperationalError as e:
            print(f"✗ 無法寫入 stockinhand.db: {e}")
            return

        # 自動為新交易創建第一個空白品項
        try:
            conn = sqlite3.connect("stockinhand.db")
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO item_details (stockinhand_id, seq, item, price, heavy, empty, grossw, minus, netw, account, total)
                VALUES (?, 1, '', 0, 0, 0, 0, 0, 0, 0, 0)
                """,
                (new_record["id"],)
            )
            conn.commit()
            first_item_id = cursor.lastrowid
            conn.close()
            # 添加到記憶體中
            new_record["items"].append((first_item_id, 1, "", 0, 0, 0, 0, 0, 0, 0, 0))
        except sqlite3.OperationalError as e:
            print(f"✗ 無法為新交易創建品項: {e}")
        
        StockInHand.append(new_record)
        StockInHand.sort(key=lambda r: r.get("number") or "", reverse=True)
        render_stockinhand_tree()

    def update_stockinhand_record(selected_record, cargo_frame_app, customer_frame_app):
        """更新車牌與廠商資料"""
        global StockInHand

        entry1, entry2 = cargo_frame_app.get_entry_values()
        entry1 = (entry1 or "").strip()
        entry2 = (entry2 or "").strip()

        if entry1 and entry2:
            carno = f"{entry1}-{entry2}"
        elif entry1:
            carno = entry1
        elif entry2:
            carno = entry2
        else:
            carno = ""

        display_text = (customer_frame_app.get_display_text() or "").strip()
        if not display_text or display_text == "未選擇客戶":
            name = ""
        elif display_text.startswith("已選擇:"):
            name = display_text.replace("已選擇:", "", 1).strip()
        else:
            name = display_text

        try:
            conn = sqlite3.connect("stockinhand.db")
            cursor = conn.cursor()
            if selected_record.get("id") is not None:
                cursor.execute(
                    "UPDATE stockinhand SET name = ?, carno = ? WHERE id = ?",
                    (name, carno, selected_record.get("id")),
                )
            else:
                cursor.execute(
                    "UPDATE stockinhand SET name = ?, carno = ? WHERE number = ? AND date = ?",
                    (name, carno, selected_record.get("number"), selected_record.get("date")),
                )
            conn.commit()
            conn.close()
        except sqlite3.OperationalError as e:
            messagebox.showerror("錯誤", f"更新失敗: {e}")
            return

        for record in StockInHand:
            if record.get("number") == selected_record.get("number"):
                record["name"] = name
                record["carno"] = carno
                break

        render_stockinhand_tree()

    def delete_selected_record():
        """刪除左上表格所選取的交易記錄"""
        global StockInHand
        
        selection = top_left_tree.selection()
        if not selection:
            messagebox.showinfo("提示", "請先選擇要刪除的資料")
            return

        item = selection[0]
        values = top_left_tree.item(item, "values")
        if not values:
            messagebox.showinfo("提示", "請先選擇要刪除的資料")
            return

        selected_number = values[0]
        selected_record = None
        for record in StockInHand:
            if record.get("number") == selected_number:
                selected_record = record
                break

        if not selected_record:
            messagebox.showerror("錯誤", "找不到選取的資料")
            return
        
        # 檢查 closeflag，如果為 1 則不允許刪除
        if selected_record.get('closeflag') == 1:
            messagebox.showwarning("提示", "該筆資料已結帳，已被鎖定，無法刪除")
            return
        
        # 顯示確認對話框，預設選項為「否」
        confirm = messagebox.askyesno(
            "確認刪除",
            f"確定要刪除編號 {selected_number} 的記錄嗎？\n車牌：{selected_record.get('carno', '')}\n廠商：{selected_record.get('name', '')}",
            icon='warning',
            default=messagebox.NO
        )
        
        if not confirm:
            return

        try:
            conn = sqlite3.connect("stockinhand.db")
            cursor = conn.cursor()
            if selected_record.get("id") is not None:
                cursor.execute("DELETE FROM stockinhand WHERE id = ?", (selected_record.get("id"),))
            else:
                cursor.execute(
                    "DELETE FROM stockinhand WHERE number = ? AND date = ?",
                    (selected_record.get("number"), selected_record.get("date")),
                )
            conn.commit()
            conn.close()
        except sqlite3.OperationalError as e:
            messagebox.showerror("錯誤", f"刪除失敗: {e}")
            return

        StockInHand = [r for r in StockInHand if r.get("number") != selected_number]
        render_stockinhand_tree()

        for tree_item in tree.get_children():
            tree.delete(tree_item)

    def open_edit_cargo():
        """選取左上表格後，開啟 AddCargo 修改車牌與廠商"""
        selection = top_left_tree.selection()
        if not selection:
            messagebox.showinfo("提示", "請先選擇左上表格資料")
            return

        if tree.selection():
            messagebox.showinfo("提示", "請先取消下方表格選取")
            return

        item = selection[0]
        values = top_left_tree.item(item, "values")
        if not values:
            messagebox.showinfo("提示", "請先選擇左上表格資料")
            return

        selected_number = values[0]
        selected_record = None
        for record in StockInHand:
            if record.get("number") == selected_number:
                selected_record = record
                break

        if not selected_record:
            messagebox.showerror("錯誤", "找不到選取的資料")
            return
        
        # 檢查 closeflag，如果為 1 則不允許編輯
        if selected_record.get('closeflag') == 1:
            messagebox.showwarning("提示", "該筆資料已結帳，已被鎖定，無法修改")
            return

        add_cargo_win = tk.Toplevel(root)
        add_cargo_win.title("修改車牌/廠商")
        add_cargo_win.geometry("1024x768")
        add_cargo_win.resizable(False, False)

        def on_cancel_close():
            add_cargo_win.destroy()

        configure_toplevel(add_cargo_win, on_close=on_cancel_close)

        style = ttk.Style()
        style.configure('TNotebook.Tab', font=('Arial', 24, 'bold'), padding=[60, 20])

        notebook = ttk.Notebook(add_cargo_win)
        notebook.pack(fill=tk.BOTH, expand=True)

        cargo_frame = tk.Frame(notebook)
        cargo_frame.pack(fill=tk.BOTH, expand=True)
        cargo_app = CargoInputFrame(cargo_frame, on_cancel_callback=on_cancel_close)
        notebook.add(cargo_frame, text="車牌")

        customer_frame = tk.Frame(notebook)
        customer_frame.pack(fill=tk.BOTH, expand=True)
        customer_app = CustomerFrame(customer_frame, CustomerID, on_cancel_callback=on_cancel_close)
        notebook.add(customer_frame, text="廠商")

        carno = selected_record.get("carno") or ""
        if "-" in carno:
            car_parts = carno.split("-", 1)
            cargo_app.set_entry_values(car_parts[0], car_parts[1])
        else:
            cargo_app.set_entry_values(carno, "")

        customer_app.set_selected_customer(selected_record.get("name") or "")

        def on_confirm_save_and_close():
            update_stockinhand_record(selected_record, cargo_app, customer_app)
            add_cargo_win.destroy()

        cargo_app.on_confirm_callback = on_confirm_save_and_close
        customer_app.on_confirm_callback = on_confirm_save_and_close

        add_cargo_win.transient(root)
        add_cargo_win.grab_set()
        add_cargo_win.focus_set()
        root.wait_window(add_cargo_win)

    def open_edit_numeric():
        """選取下方表格的數值欄位後，開啟 NoPad 修改數值"""
        nonlocal selected_cell_column
        
        if not selected_cell_column:
            messagebox.showinfo("提示", "請先點擊要修改的數值欄位（價格、重車、空車或扣重）")
            return
        
        selection = top_left_tree.selection()
        if not selection:
            messagebox.showinfo("提示", "請先選擇左上表格資料")
            return
        
        item = selection[0]
        values = top_left_tree.item(item, "values")
        if not values:
            messagebox.showinfo("提示", "請先選擇左上表格資料")
            return
        
        selected_number = values[0]
        selected_record = None
        for record in StockInHand:
            if record.get("number") == selected_number:
                selected_record = record
                break
        
        if not selected_record:
            messagebox.showerror("錯誤", "找不到選取的資料")
            return
        
        # 檢查 closeflag，如果為 1 則不允許編輯
        if selected_record.get('closeflag') == 1:
            messagebox.showwarning("提示", "該筆資料已結帳，已被鎖定，無法修改")
            return
        
        # 取得 table_frame 中選中的行索引
        table_selection = tree.selection()
        if not table_selection:
            messagebox.showinfo("提示", "請先選擇表格中的品項")
            return
        
        # 取得點擊的行是第幾個品項
        item_index = 0
        for idx, tree_item in enumerate(tree.get_children()):
            if tree_item == table_selection[0]:
                item_index = idx
                break
        
        items = selected_record.get("items", [])
        if item_index >= len(items):
            messagebox.showerror("錯誤", "找不到選中的品項")
            return
        
        selected_item = items[item_index]
        item_id, seq, item_name, heavy, empty, grossw, minus, netw, account, total, price = selected_item
        
        field_map = {
            "價格": "price",
            "重車": "heavy",
            "空車": "empty",
            "扣重": "minus"
        }
        field_key = field_map.get(selected_cell_column)
        
        if not field_key:
            messagebox.showerror("錯誤", "不支持的欄位")
            return
        
        # 取得目前值
        current_value_map = {
            "price": price,
            "heavy": heavy,
            "empty": empty,
            "minus": minus
        }
        current_value = current_value_map.get(field_key, 0.0)

        def apply_numeric_update(float_value):
            nonlocal selected_cell_column
            try:
                # 將 heavy, empty 四舍五入到整數
                if field_key in ("heavy", "empty"):
                    float_value = round(float_value)
            except ValueError:
                messagebox.showerror("錯誤", "請輸入有效的數值")
                return

            try:
                conn = sqlite3.connect("stockinhand.db")
                cursor = conn.cursor()
                cursor.execute(
                    f"UPDATE item_details SET {field_key} = ? WHERE id = ?",
                    (float_value, item_id)
                )
                conn.commit()
                conn.close()
            except sqlite3.OperationalError as e:
                messagebox.showerror("錯誤", f"更新失敗: {e}")
                return

            # 更新記憶體中的值
            heavy_val = heavy if field_key != "heavy" else float_value
            empty_val = empty if field_key != "empty" else float_value
            minus_val = minus if field_key != "minus" else float_value
            price_val = price if field_key != "price" else float_value

            # 自動計算 grossw
            global active_threads
            
            grossw_val = heavy_val - empty_val
            if grossw_val < 0:
                grossw_val = 0.0
            grossw_val = round(grossw_val)

            # 更新資料庫中的 grossw
            if field_key in ("heavy", "empty"):
                try:
                    conn = sqlite3.connect("stockinhand.db")
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE item_details SET grossw = ? WHERE id = ?",
                        (grossw_val, item_id)
                    )
                    conn.commit()
                    conn.close()
                except sqlite3.OperationalError as e:
                    print(f"✗ 更新 grossw 失败: {e}")

            # 更新記憶體中的項目
            items[item_index] = (item_id, seq, item_name, heavy_val, empty_val, grossw_val, minus_val, netw, account, total, price_val)

            # 重新計算交易的總額
            total_account = 0.0
            for item_row in items:
                item_grossw = item_row[5] if item_row[5] else 0.0
                item_minus = item_row[6] if item_row[6] else 0.0
                item_netw = item_grossw - item_minus
                item_price = item_row[10] if item_row[10] else 0.0
                total_account += item_netw * item_price
            selected_record["total"] = total_account

            # 保存當前選中的編號以便重新選擇
            selected_number = selected_record.get("number")
            render_stockinhand_tree()

            # 重新選擇同一行
            for tree_item in top_left_tree.get_children():
                if top_left_tree.item(tree_item, "values")[0] == selected_number:
                    top_left_tree.selection_set(tree_item)
                    top_left_tree.see(tree_item)
                    on_top_left_tree_select(None)
                    break

            selected_cell_column = None

        def open_rs232_dialog():
            nonlocal selected_cell_column
            try:
                import serial
                from serial.tools import list_ports
            except ImportError as e:
                messagebox.showerror("錯誤", f"未安裝 pyserial，無法讀取 RS232\n請執行：pip install pyserial")
                return

            port = os.environ.get("WEIGHTSTATION_SERIAL_PORT")
            baud = int(os.environ.get("WEIGHTSTATION_SERIAL_BAUD", "9600"))
            
            if not port:
                ports = [p.device for p in list_ports.comports()]
                if not ports:
                    messagebox.showerror("錯誤", "找不到可用的序列埠\n請確認 RS232 設備已連接")
                    return
                port = ports[0]
                print(f"自動選擇序列埠: {port}")

            rs_win = tk.Toplevel(root)
            rs_win.title(f"RS232 讀值 - {selected_cell_column}")
            rs_win.geometry("480x260")
            rs_win.resizable(False, False)
            configure_toplevel(rs_win)

            value_var = tk.StringVar(value="0")
            status_var = tk.StringVar(value=f"連線中：{port} @ {baud}")

            tk.Label(rs_win, textvariable=status_var, font=("Arial", 12)).pack(pady=(10, 5))
            tk.Label(rs_win, textvariable=value_var, font=("Arial", 36, "bold"), fg="#2E7D32").pack(pady=(5, 15))

            # 初始化變數
            stop_event = threading.Event()
            latest_value = {"value": 0.0}

            def parse_value(text):
                """從文本中提取數值，支持多種數字格式"""
                # 預處理：移除 ASCII 範圍外的特殊字符（保留空格、數字、符號）
                # 這樣 "006\xb830" 會變成 "006830"
                cleaned_text = ''.join(c if (c.isdigit() or c in '+-. \n\r') else '' for c in text)
                
                # 策略1：先嘗試匹配較長的連續數字（最多10位）
                long_match = re.search(r'[\s+]?([+-]?\d{4,10})(?:[^\d]|$)', cleaned_text)
                if long_match:
                    try:
                        val = float(long_match.group(1))
                        if val < 1000000:
                            return val
                    except:
                        pass
                
                # 策略2：匹配標準 6 位數字格式
                match_6digits = re.search(r'[\s]?([+-]?\d{6})(?:[^\d]|$)', cleaned_text)
                if match_6digits:
                    try:
                        return float(match_6digits.group(1))
                    except:
                        pass
                
                # 策略3：找出所有數字片段並智能組合
                matches = re.findall(r'[-+]?\d{1,10}(?:\.\d+)?', cleaned_text)
                if not matches:
                    return None
                
                values = []
                for m in matches:
                    try:
                        v = float(m)
                        values.append(v)
                    except:
                        continue
                
                if not values:
                    return None
                
                if len(values) == 1:
                    return values[0]
                
                # 嘗試組合相鄰數字
                if len(matches) >= 2:
                    combined = ''.join([m.lstrip('+') for m in matches if m.replace('+', '').replace('-', '').replace('.', '').isdigit()])
                    try:
                        combined_val = float(combined)
                        if combined_val < 1000000:
                            return combined_val
                    except:
                        pass
                
                non_zero_values = [v for v in values if v != 0.0]
                if non_zero_values:
                    return max(non_zero_values)
                
                return values[-1]

            def reader_thread(ser):
                """逐字節讀取 RS232 數據，直到完整接收"""
                buffer = b""
                last_valid_value = None
                
                while not stop_event.is_set():
                    try:
                        # 一次讀取多個位元組以提高效率
                        data = ser.read(max(1, ser.in_waiting or 1))
                        if not data:
                            continue
                        
                        buffer += data
                        
                        # 檢查是否有完整的一行（以換行符結束）
                        if b'\n' in buffer:
                            lines = buffer.split(b'\n')
                            # 最後一個可能是不完整的，保留在 buffer 中
                            buffer = lines[-1]
                            
                            # 處理完整的行
                            for line in lines[:-1]:
                                try:
                                    # 關鍵修復：磅秤使用帶奇偶校驗位的 RS232 傳輸
                                    # 需要移除每個位元組的最高位（奇偶校驗位）再提取數字
                                    # 例如：0xb8 (10111000) & 0x7F = 0x38 ('8')
                                    ascii_clean = ''.join(
                                        chr(b & 0x7F) if ((b & 0x7F) in range(48, 58) or (b & 0x7F) in [43, 45, 46]) else ''
                                        for b in line
                                    )
                                    
                                    # 如果提取到數字，使用清理後的結果
                                    if ascii_clean and any(c.isdigit() for c in ascii_clean):
                                        text = ascii_clean
                                    else:
                                        # 備用：嘗試解碼並解析
                                        text = line.decode('utf-8', errors='ignore').strip()
                                    
                                    if text:
                                        # 從文本中提取數字
                                        val = parse_value(text)
                                        if val is not None:
                                            # 過濾明顯錯誤的讀數
                                            # 如果當前有效值 > 0，突然變成 0，可能是數據分割錯誤
                                            if val == 0.0 and last_valid_value is not None and last_valid_value > 0.0:
                                                continue
                                            
                                            # 更新顯示值
                                            latest_value["value"] = val
                                            last_valid_value = val
                                            rs_win.after(0, lambda v=val: value_var.set(str(v)))
                                except Exception as e:
                                    continue
                        
                        # 防止緩衝區無限增長
                        if len(buffer) > 1000:
                            buffer = buffer[-100:]
                            
                    except Exception as e:
                        print(f"RS232 讀取錯誤: {e}")
                        break

            try:
                ser = serial.Serial(port, baudrate=baud, timeout=1)
            except Exception as e:
                messagebox.showerror("錯誤", f"無法開啟序列埠：{e}")
                rs_win.destroy()
                return

            t = threading.Thread(target=reader_thread, args=(ser,), daemon=True)
            t.start()
            
            # 追蹤執行緒和序列埠以便後續清理
            thread_info = {
                'thread': t,
                'stop_event': stop_event,
                'serial': ser
            }
            active_threads.append(thread_info)

            btn_frame = tk.Frame(rs_win)
            btn_frame.pack(pady=10)

            def on_confirm():
                stop_event.set()
                try:
                    ser.close()
                except Exception:
                    pass
                # 從追蹤列表中移除
                active_threads[:] = [t for t in active_threads if t.get('stop_event') != stop_event]
                apply_numeric_update(latest_value["value"])
                rs_win.destroy()

            def on_cancel():
                stop_event.set()
                try:
                    ser.close()
                except Exception:
                    pass
                # 從追蹤列表中移除
                active_threads[:] = [t for t in active_threads if t.get('stop_event') != stop_event]
                selected_cell_column = None
                rs_win.destroy()

            tk.Button(btn_frame, text="確認", font=("Arial", 14), width=10, bg="#4caf50", fg="white", command=on_confirm).pack(side=tk.LEFT, padx=10)
            tk.Button(btn_frame, text="取消", font=("Arial", 14), width=10, bg="#f44336", fg="white", command=on_cancel).pack(side=tk.LEFT, padx=10)

            def on_close():
                on_cancel()

            rs_win.protocol("WM_DELETE_WINDOW", on_close)
            rs_win.transient(root)
            rs_win.grab_set()
            rs_win.focus_set()
            root.wait_window(rs_win)

        def open_nopad_dialog():
            nopad_win = tk.Toplevel(root)
            nopad_win.title(f"修改{selected_cell_column}")
            nopad_win.geometry("600x700")
            nopad_win.resizable(False, False)
            configure_toplevel(nopad_win, on_close=on_nopad_cancel)

            def on_nopad_confirm(value):
                try:
                    float_value = float(value) if value and value != "0" else 0.0
                except ValueError:
                    messagebox.showerror("錯誤", "請輸入有效的數值")
                    return
                apply_numeric_update(float_value)
                nopad_win.destroy()

            def on_nopad_cancel():
                nonlocal selected_cell_column
                selected_cell_column = None
                nopad_win.destroy()

            keypad = NumericKeypad(nopad_win, on_confirm_callback=on_nopad_confirm, on_cancel_callback=on_nopad_cancel)
            # 設定初始值（包括 0 值也要顯示）
            if current_value is not None:
                keypad.input_value = str(current_value).rstrip('0').rstrip('.') if '.' in str(current_value) else str(current_value)
                keypad.update_display()
            else:
                # 如果沒有值，至少要初始化顯示
                keypad.update_display()

            nopad_win.transient(root)
            nopad_win.grab_set()
            nopad_win.focus_set()
            root.wait_window(nopad_win)

        # toggle 為 ON 且修改重車/空車時，使用 RS232 視窗
        if toggle_var.get() and field_key in ("heavy", "empty"):
            open_rs232_dialog()
        else:
            open_nopad_dialog()
    
    def open_edit_item():
        """選取下方表格的品項欄位後，高亮商品區域並允許選擇"""
        nonlocal selected_cell_column
        
        selection = top_left_tree.selection()
        if not selection:
            messagebox.showinfo("提示", "請先選擇左上表格資料")
            return
        
        item = selection[0]
        values = top_left_tree.item(item, "values")
        if not values:
            messagebox.showinfo("提示", "請先選擇左上表格資料")
            return
        
        selected_number = values[0]
        selected_record = None
        for record in StockInHand:
            if record.get("number") == selected_number:
                selected_record = record
                break
        
        if not selected_record:
            messagebox.showerror("錯誤", "找不到選取的資料")
            return
        
        # 檢查 closeflag，如果為 1 則不允許編輯
        if selected_record.get('closeflag') == 1:
            messagebox.showwarning("提示", "該筆資料已結帳，已被鎖定，無法修改")
            return
        
        # 取得 table_frame 中選中的行索引
        table_selection = tree.selection()
        if not table_selection:
            messagebox.showinfo("提示", "請先選擇表格中的品項")
            return
        
        # 取得點擊的行是第幾個品項
        item_index = 0
        for idx, tree_item in enumerate(tree.get_children()):
            if tree_item == table_selection[0]:
                item_index = idx
                break
        
        items = selected_record.get("items", [])
        if item_index >= len(items):
            messagebox.showerror("錯誤", "找不到選中的品項")
            return
        
        selected_item = items[item_index]
        item_id, seq, item_name, heavy, empty, grossw, minus, netw, account, total, price = selected_item
        
        # 保存原始背景色
        original_bg = top_right_frame.cget("bg")
        
        # 高亮 top_right_frame
        top_right_frame.config(bg="#FFD700", relief=tk.RIDGE, bd=5)
        
        def on_item_selected(new_item_name):
            """當選擇商品時更新記錄"""
            new_price = ItemValue.get(new_item_name, 0.0)
            
            try:
                conn = sqlite3.connect("stockinhand.db")
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE item_details SET item = ?, price = ? WHERE id = ?",
                    (new_item_name, new_price, item_id)
                )
                conn.commit()
                conn.close()
            except sqlite3.OperationalError as e:
                messagebox.showerror("錯誤", f"更新失敗: {e}")
                restore_normal_state()
                return
            
            # 更新記憶體中的記錄
            items[item_index] = (item_id, seq, new_item_name, heavy, empty, grossw, minus, netw, account, total, new_price)
            
            # 重新計算交易的總額
            total_account = 0.0
            for item_row in items:
                item_grossw = item_row[5] if item_row[5] else 0.0
                item_minus = item_row[6] if item_row[6] else 0.0
                item_netw = item_grossw - item_minus
                item_price = item_row[10] if item_row[10] else 0.0
                total_account += item_netw * item_price
            selected_record["total"] = total_account
            
            render_stockinhand_tree()
            
            # 重新選擇同一行
            for tree_item in top_left_tree.get_children():
                if top_left_tree.item(tree_item, "values")[0] == selected_number:
                    top_left_tree.selection_set(tree_item)
                    top_left_tree.see(tree_item)
                    on_top_left_tree_select(None)
                    break
            
            restore_normal_state()
        
        def restore_normal_state():
            """恢復正常狀態"""
            nonlocal selected_cell_column
            top_right_frame.config(bg=original_bg, relief=tk.FLAT, bd=0)
            create_item_buttons()
            selected_cell_column = None
            root.unbind("<Button-1>")
        
        def on_click_outside(event):
            """點擊其他區域取消選擇"""
            x, y = event.x_root, event.y_root
            fx, fy = top_right_frame.winfo_rootx(), top_right_frame.winfo_rooty()
            fw, fh = top_right_frame.winfo_width(), top_right_frame.winfo_height()
            
            if not (fx <= x <= fx + fw and fy <= y <= fy + fh):
                restore_normal_state()
        
        create_item_buttons(on_item_selected)
        root.bind("<Button-1>", on_click_outside)
    
    # 延遲載入資料以確保視窗完全初始化
    top_left_frame.after(200, load_today_records)

    # 在右邊 frame 添加 5 個正方形按鈕
    button_width = 10  # 按鈕邊長（以字元為單位，對應約 100px）
    button_height = 5  # 按鈕高度（以行為單位，與寬相同形成正方形）

    def on_checkout_click():
        """結帳按鈕的回調：設置 closeflag 為 1 或根據點擊次數重置"""
        global checkout_click_count
        
        selection = top_left_tree.selection()
        if not selection:
            messagebox.showinfo("提示", "請先選擇左上表格資料")
            return

        item = selection[0]
        values = top_left_tree.item(item, "values")
        if not values:
            messagebox.showinfo("提示", "請先選擇左上表格資料")
            return

        selected_number = values[0]
        selected_record = None
        for record in StockInHand:
            if record.get("number") == selected_number:
                selected_record = record
                break

        if not selected_record:
            messagebox.showerror("錯誤", "找不到選取的資料")
            return
        
        # 如果 closeflag 已是 1，計算連續點擊次數
        if selected_record.get('closeflag') == 1:
            if selected_number not in checkout_click_count:
                checkout_click_count[selected_number] = 1
            else:
                checkout_click_count[selected_number] += 1
            
            # 如果點擊次數達到 2 次，取消結帳
            if checkout_click_count[selected_number] >= 2:
                selected_record['closeflag'] = 0
                checkout_click_count[selected_number] = 0
                
                # 更新資料庫
                try:
                    conn = sqlite3.connect("stockinhand.db")
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE stockinhand SET closeflag = ? WHERE id = ?",
                        (0, selected_record.get("id"))
                    )
                    conn.commit()
                    conn.close()
                except sqlite3.OperationalError as e:
                    messagebox.showerror("錯誤", f"取消結帳失敗: {e}")
                    return
                
                render_stockinhand_tree()
                messagebox.showinfo("提示", f"編號 {selected_number} 已取消結帳，可正常操作")
            else:
                remaining_clicks = 2 - checkout_click_count[selected_number]
                messagebox.showinfo("提示", f"該筆資料已結帳\n再點擊 {remaining_clicks} 次可取消結帳")
        else:
            # 第一次點擊或之前已取消，設置 closeflag 為 1
            selected_record['closeflag'] = 1
            checkout_click_count[selected_number] = 0
            
            # 更新資料庫
            try:
                conn = sqlite3.connect("stockinhand.db")
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE stockinhand SET closeflag = ? WHERE id = ?",
                    (1, selected_record.get("id"))
                )
                conn.commit()
                conn.close()
            except sqlite3.OperationalError as e:
                messagebox.showerror("錯誤", f"結帳失敗: {e}")
                return
            
            render_stockinhand_tree()
            messagebox.showinfo("提示", f"編號 {selected_number} 已結帳，該筆資料已被鎖定")

    labels = ["新增", "修改", "結帳", "刪除", "設置"]
    colors = ["#BFE8FF", "#FFD6E7", "#BFE8FF", "#FFD6E7", "#BFE8FF"]
    modify_btn = None
    checkout_btn = None
    for i in range(5):
        if labels[i] == "設置":
            cmd = open_info_set
        elif labels[i] == "新增":
            cmd = open_add_cargo
        elif labels[i] == "修改":
            cmd = None
        elif labels[i] == "結帳":
            cmd = None
        elif labels[i] == "刪除":
            cmd = delete_selected_record
        else:
            cmd = None
        btn = tk.Button(
            right_buttons_frame,
            text=labels[i],
            height=button_height,
            bg=colors[i],
            fg="black",
            font=("Arial", 18, "bold"),
            command=cmd,
        )
        btn.pack(pady=0, fill=tk.X)
        
        if labels[i] == "修改":
            modify_btn = btn
        elif labels[i] == "結帳":
            checkout_btn = btn
    
    # 添加列印按鈕
    def on_print_click():
        """列印按鈕的回調"""
        messagebox.showinfo("提示", "列印功能待實現")
    
    print_btn = tk.Button(
        right_buttons_frame,
        text="列印",
        height=button_height,
        bg="#BFE8FF",
        fg="black",
        font=("Arial", 18, "bold"),
        command=on_print_click,
    )
    print_btn.pack(pady=0, fill=tk.X)

    
    def on_modify_button_click():
        """修改按鈕的動態回調：檢查是否有選中的列來決定打開修改車牌、修改數值或修改品項"""
        if selected_cell_column == "品項":
            open_edit_item()
        elif selected_cell_column:
            open_edit_numeric()
        else:
            open_edit_cargo()
    
    if modify_btn:
        modify_btn.config(command=on_modify_button_click)
    
    if checkout_btn:
        checkout_btn.config(command=on_checkout_click)

    return root


def main():
    """載入資料後啟動 GUI。"""
    init_data_once()
    app = create_app()
    app.mainloop()


if __name__ == "__main__":
    init_data_once()
    main()