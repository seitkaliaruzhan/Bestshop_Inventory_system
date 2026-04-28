import customtkinter as ctk
import pyodbc
from tkinter import messagebox

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class BestShopApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Best Shop - Управление магазином")
        self.geometry("1000x750")

        # Строка подключения
        self.conn_str = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=localhost;" 
            "DATABASE=BestShopDB;"
            "Trusted_Connection=yes;"
            "TrustServerCertificate=yes;"
        )
        
        self.setup_ui()
        # загружаем данные
        self.load_all_data()

    def setup_ui(self):
        # 1. Заголовок
        self.label = ctk.CTkLabel(self, text="Панель управления Best Shop", font=("Arial", 28, "bold"))
        self.label.pack(pady=15)

        # 2. ВЕРХНЯЯ ПАНЕЛЬ (Поиск и Фильтр категорий)
        top_frame = ctk.CTkFrame(self)
        top_frame.pack(pady=10, padx=20, fill="x")

        self.search_entry = ctk.CTkEntry(top_frame, placeholder_text="Поиск товара...", width=300)
        self.search_entry.pack(side="left", padx=10, pady=10)

        search_btn = ctk.CTkButton(top_frame, text="Найти (Stored Proc)", command=self.call_search_procedure)
        search_btn.pack(side="left", padx=10)

        self.category_combo = ctk.CTkComboBox(top_frame, 
                                            values=["Все категории", "Электроника", "Аксессуары"],
                                            command=lambda _: self.load_all_data())
        self.category_combo.pack(side="left", padx=10)

        # 3. ПАНЕЛЬ НАСТРОЕК (Radiobuttons и Checkbox)
        settings_frame = ctk.CTkFrame(self)
        settings_frame.pack(pady=5, padx=20, fill="x")

        self.sort_var = ctk.StringVar(value="ProductName")
        ctk.CTkLabel(settings_frame, text="Сортировка:").pack(side="left", padx=10)
        
        ctk.CTkRadioButton(settings_frame, text="По имени", variable=self.sort_var, 
                           value="ProductName", command=self.load_all_data).pack(side="left", padx=5)
        ctk.CTkRadioButton(settings_frame, text="По цене", variable=self.sort_var, 
                           value="Price", command=self.load_all_data).pack(side="left", padx=5)

        self.in_stock_var = ctk.BooleanVar(value=False)
        self.stock_check = ctk.CTkCheckBox(settings_frame, text="Только в наличии", 
                                          variable=self.in_stock_var, command=self.load_all_data)
        self.stock_check.pack(side="right", padx=20) # ТЕПЕРЬ ОН ОТОБРАЖАЕТСЯ

        # 4. ОБЛАСТЬ ВЫВОДА (Grid View)
        self.display_area = ctk.CTkTextbox(self, width=950, height=350, font=("Courier New", 13))
        self.display_area.pack(pady=10, padx=20)

        # 5. ПАНЕЛЬ НАВИГАЦИИ (Navigator)
        nav_frame = ctk.CTkFrame(self)
        nav_frame.pack(pady=5)
        
        ctk.CTkButton(nav_frame, text="<<", width=50, 
                      command=lambda: self.display_area.yview_scroll(-1, "units")).grid(row=0, column=0, padx=5)
        ctk.CTkButton(nav_frame, text=">>", width=50, 
                      command=lambda: self.display_area.yview_scroll(1, "units")).grid(row=0, column=1, padx=5)

        # 6. НИЖНЯЯ ПАНЕЛЬ (Calculated Fields)
        self.stats_label = ctk.CTkLabel(self, text="Загрузка статистики...", font=("Arial", 14, "italic"))
        self.stats_label.pack(pady=10)

        refresh_btn = ctk.CTkButton(self, text="ПОКАЗАТЬ ВСЕ (VIEW)", command=self.load_all_data, fg_color="green")
        refresh_btn.pack(pady=10)

    def load_all_data(self, *args):
        """Динамическая загрузка данных с фильтрами и сортировкой"""
        try:
            conn = pyodbc.connect(self.conn_str)
            cursor = conn.cursor()
            
            query = "SELECT * FROM vw_ProductDetails WHERE 1=1"
            params = []

            selected_cat = self.category_combo.get()
            if selected_cat != "Все категории":
                query += " AND CategoryName = ?"
                params.append(selected_cat)

            if self.in_stock_var.get():
                query += " AND StockCount > 0"

            query += f" ORDER BY {self.sort_var.get()} ASC"

            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            self.display_area.delete("1.0", "end")
            header = f"{'ID':<5} | {'Название':<25} | {'Категория':<15} | {'Цена':<10} | {'Склад':<5}\n"
            self.display_area.insert("end", header)
            self.display_area.insert("end", "-"*75 + "\n")
            
            total_items = 0
            total_sum = 0.0

            for row in rows:
                self.display_area.insert("end", f"{row[0]:<5} | {row[1]:<25} | {row[2]:<15} | {row[3]:<10.2f} | {row[4]:<5}\n")
                total_items += 1
                total_sum += (float(row[3]) * int(row[4]))
            
            self.stats_label.configure(
                text=f"Найдено: {total_items} позиций | Общая стоимость на складе: {total_sum:,.2f} тг."
            )
            
            conn.close()
        except Exception as e:
            messagebox.showerror("Ошибка БД", f"Не удалось загрузить данные: {e}")

    def call_search_procedure(self):
        """Поиск через Хранимую Процедуру с защитой от пустых данных"""
        search_term = self.search_entry.get()
        if not search_term:
            self.load_all_data()
            return

        try:
            conn = pyodbc.connect(self.conn_str)
            cursor = conn.cursor()
            cursor.execute("{CALL sp_FindProducts (?)}", (search_term,))
            rows = cursor.fetchall()
            
            self.display_area.delete("1.0", "end")
            self.display_area.insert("end", f"Результаты поиска через процедуру для: '{search_term}'\n")
            self.display_area.insert("end", "-"*75 + "\n")

            for row in rows:
                p_id = row[0] if row[0] is not None else 0
                p_name = row[1] if row[1] is not None else "Без названия"
                p_price = row[3] if row[3] is not None else 0.0
                p_stock = row[4] if row[4] is not None else 0

                self.display_area.insert("end", f"ID: {p_id:<3} | {p_name:<25} | Цена: {p_price:<8.2f} | Остаток: {p_stock}\n")
            
            conn.close()
        except Exception as e:
            messagebox.showerror("Ошибка процедуры", f"Ошибка при вызове SP: {e}")

if __name__ == "__main__":
    app = BestShopApp()
    app.mainloop()