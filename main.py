import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageGrab, ImageOps, ImageFilter, ImageEnhance
from pyzbar.pyzbar import decode
from urllib.parse import urlparse, parse_qs, unquote
import threading
import pytesseract
import re

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class QRCodeReaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("QR Code Reader + Screenshot Parser")
        self.root.geometry("650x500")
        self.root.resizable(False, False)

        # Переменные для хранения результатов
        self.code_result = tk.StringVar()
        self.url_result = tk.StringVar()
        self.digits_result = tk.StringVar()

        self.setup_ui()

    def setup_ui(self):
        # Основной фрейм
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Заголовок
        title_label = ttk.Label(main_frame, text="QR Code Reader + Screenshot Parser",
                                font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # ================ СЕКЦИЯ QR-КОДА ================
        qr_section = ttk.LabelFrame(main_frame, text="QR Code Reader", padding="10")
        qr_section.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        # Кнопка чтения QR-кода
        self.read_btn = ttk.Button(qr_section, text="1. Считать QR из буфера обмена",
                                   command=self.read_qr_from_clipboard,
                                   width=30)
        self.read_btn.grid(row=0, column=0, columnspan=2, pady=5)

        # Область для кода из QR
        qr_code_frame = ttk.LabelFrame(qr_section, text="Код из QR", padding="5")
        qr_code_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5, padx=(0, 5))

        self.code_entry = tk.Text(qr_code_frame, height=2, width=35, wrap=tk.WORD)
        self.code_entry.grid(row=0, column=0, sticky=(tk.W, tk.E))

        copy_code_btn = ttk.Button(qr_code_frame, text="2. Копировать код",
                                   command=self.copy_code)
        copy_code_btn.grid(row=1, column=0, pady=5)

        # Область для URL из QR
        qr_url_frame = ttk.LabelFrame(qr_section, text="Ссылка из QR", padding="5")
        qr_url_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))

        self.url_entry = tk.Text(qr_url_frame, height=2, width=35, wrap=tk.WORD)
        self.url_entry.grid(row=0, column=0, sticky=(tk.W, tk.E))

        copy_url_btn = ttk.Button(qr_url_frame, text="3. Копировать ссылку",
                                  command=self.copy_url)
        copy_url_btn.grid(row=1, column=0, pady=5)

        # ================ СЕКЦИЯ СКРИНШОТА ================
        screenshot_section = ttk.LabelFrame(main_frame, text="Screenshot Parser", padding="10")
        screenshot_section.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 10))

        # Кнопка чтения скриншота
        self.read_screenshot_btn = ttk.Button(screenshot_section, text="4. Считать цифры со скриншота",
                                              command=self.read_screenshot,
                                              width=30)
        self.read_screenshot_btn.grid(row=0, column=0, columnspan=2, pady=5)

        # Область для цифр со скриншота
        digits_frame = ttk.LabelFrame(screenshot_section, text="Цифры со скриншота", padding="5")
        digits_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5, padx=(0, 5))

        self.digits_entry = tk.Text(digits_frame, height=2, width=35, wrap=tk.WORD)
        self.digits_entry.grid(row=0, column=0, sticky=(tk.W, tk.E))

        copy_digits_btn = ttk.Button(digits_frame, text="5. Копировать цифры",
                                     command=self.copy_digits)
        copy_digits_btn.grid(row=1, column=0, pady=5)

        # Область для предпросмотра (необязательно, но полезно)
        preview_frame = ttk.LabelFrame(screenshot_section, text="Информация", padding="5")
        preview_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))

        info_text = "Формат цифр: '00'\nСкопируйте скриншот с цифрами\nв буфер обмена и нажмите кнопку 4"
        preview_label = ttk.Label(preview_frame, text=info_text, justify=tk.LEFT)
        preview_label.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)

        # Статус бар
        self.status_var = tk.StringVar(value="Готов к работе")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var,
                               relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))

        # Настройка весов строк и столбцов
        main_frame.columnconfigure(0, weight=1)
        qr_section.columnconfigure(0, weight=1)
        qr_section.columnconfigure(1, weight=1)
        screenshot_section.columnconfigure(0, weight=1)
        screenshot_section.columnconfigure(1, weight=1)
        qr_code_frame.columnconfigure(0, weight=1)
        qr_url_frame.columnconfigure(0, weight=1)
        digits_frame.columnconfigure(0, weight=1)
        preview_frame.columnconfigure(0, weight=1)

    # ================ МЕТОДЫ ДЛЯ QR-КОДА ================

    def parse_phonefactor_url(self, url_string):
        """Парсит строку и извлекает код и URL"""
        try:
            parsed = urlparse(url_string)
            query_params = parse_qs(parsed.query)

            code = query_params['code'][0]
            url = unquote(query_params['url'][0])

            return code, url
        except Exception as e:
            self.show_error(f"Ошибка при парсинге: {e}")
            return None, None

    def read_qr_from_clipboard(self):
        """Читает QR-код из буфера обмена в отдельном потоке"""
        self.read_btn.config(state='disabled')
        self.status_var.set("Считываю QR-код из буфера обмена...")

        thread = threading.Thread(target=self._read_qr_thread)
        thread.daemon = True
        thread.start()

    def _read_qr_thread(self):
        """Поток для чтения QR-кода"""
        try:
            # Получаем изображение из буфера обмена
            image = ImageGrab.grabclipboard()

            if image is None:
                self.root.after(0, lambda: self.show_error("В буфере обмена нет изображения"))
                return

            # Конвертируем в RGB если нужно
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Декодируем QR-код
            decoded_objects = decode(image)

            if decoded_objects:
                qr_data = decoded_objects[0].data.decode('utf-8')
                self.root.after(0, lambda: self.process_qr_data(qr_data))
            else:
                self.root.after(0, lambda: self.show_error("QR-код не найден в изображении из буфера обмена"))

        except Exception as e:
            self.root.after(0, lambda: self.show_error(f"Ошибка при чтении QR-кода: {e}"))

    def process_qr_data(self, qr_data):
        """Обрабатывает данные QR-кода и обновляет GUI"""
        try:
            # Парсим данные
            code, url = self.parse_phonefactor_url(qr_data)

            if code and url:
                # Очищаем поля
                self.code_entry.delete(1.0, tk.END)
                self.url_entry.delete(1.0, tk.END)

                # Вставляем новые данные
                self.code_entry.insert(1.0, code)
                self.url_entry.insert(1.0, url)

                self.status_var.set("QR-код успешно обработан!")
                #messagebox.showinfo("Успех", "QR-код успешно считан и обработан!")
            else:
                self.show_error("Не удалось распарсить данные из QR-кода")

        except Exception as e:
            self.show_error(f"Ошибка при обработке данных: {e}")
        finally:
            self.read_btn.config(state='normal')

    def copy_code(self):
        """Копирует код из QR в буфер обмена"""
        code = self.code_entry.get(1.0, tk.END).strip()
        if code:
            self.root.clipboard_clear()
            self.root.clipboard_append(code)
            self.status_var.set("Код скопирован в буфер обмена!")
            #messagebox.showinfo("Успех", "Код скопирован в буфер обмена!")
        else:
            self.show_error("Нет данных для копирования")

    def copy_url(self):
        """Копирует URL из QR в буфер обмена"""
        url = self.url_entry.get(1.0, tk.END).strip()
        if url:
            self.root.clipboard_clear()
            self.root.clipboard_append(url)
            self.status_var.set("Ссылка скопирована в буфер обмена!")
            #messagebox.showinfo("Успех", "Ссылка скопирована в буфер обмена!")
        else:
            self.show_error("Нет данных для копирования")

    # ================ МЕТОДЫ ДЛЯ СКРИНШОТА ================

    def read_screenshot(self):
        """Читает цифры со скриншота из буфера обмена"""
        self.read_screenshot_btn.config(state='disabled')
        self.status_var.set("Обрабатываю скриншот из буфера обмена...")

        thread = threading.Thread(target=self._read_screenshot_thread)
        thread.daemon = True
        thread.start()

    def _read_screenshot_thread(self):
        """Поток для обработки скриншота и извлечения цифр"""
        try:
            # Получаем изображение из буфера обмена
            image = ImageGrab.grabclipboard()

            if image is None:
                self.root.after(0, lambda: self.show_error("В буфере обмена нет изображения"))
                return

            # Преобразуем изображение для лучшего распознавания
            processed_image = self.preprocess_image_for_ocr(image)

            # Используем OCR для извлечения текста
            text = pytesseract.image_to_string(processed_image, config='--psm 8 --oem 3')

            # Ищем две цифры в формате "00"
            digits = self.extract_two_digits(text)

            if digits:
                self.root.after(0, lambda: self.process_screenshot_digits(digits))
            else:
                self.root.after(0, lambda: self.show_error(
                    f"Не найдены две цифры в формате '00'. Распознанный текст: '{text.strip()}'"))

        except Exception as e:
            self.root.after(0, lambda: self.show_error(f"Ошибка при обработке скриншота: {e}"))

    def preprocess_image_for_ocr(self, image):
        """Подготавливает изображение для OCR"""
        # Конвертируем в grayscale
        if image.mode != 'L':
            image = image.convert('L')

        # Увеличиваем контраст
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)

        # Увеличиваем резкость
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(2.0)

        # Применяем бинаризацию
        image = image.point(lambda x: 0 if x < 128 else 255, '1')

        # Увеличиваем размер для лучшего распознавания
        width, height = image.size
        image = image.resize((width * 2, height * 2), Image.Resampling.LANCZOS)

        return image

    def extract_two_digits(self, text):
        """Извлекает две цифры из текста"""
        # Ищем последовательность из двух цифр
        matches = re.findall(r'\b\d{2}\b', text)

        if matches:
            return matches[0]  # Возвращаем первое совпадение

        # Если не нашли, попробуем найти любые две цифры подряд
        matches = re.findall(r'\d{2}', text)

        if matches:
            return matches[0]

        return None

    def process_screenshot_digits(self, digits):
        """Обрабатывает найденные цифры и обновляет GUI"""
        try:
            # Очищаем поле
            self.digits_entry.delete(1.0, tk.END)

            # Вставляем найденные цифры
            self.digits_entry.insert(1.0, digits)

            self.status_var.set(f"Найдены цифры: {digits}")
            ##messagebox.showinfo("Успех", f"Цифры успешно извлечены: {digits}")

        except Exception as e:
            pass#self.show_error(f"Ошибка при обработке цифр: {e}")
        finally:
            self.read_screenshot_btn.config(state='normal')

    def copy_digits(self):
        """Копирует цифры со скриншота в буфер обмена"""
        digits = self.digits_entry.get(1.0, tk.END).strip()
        if digits:
            self.root.clipboard_clear()
            self.root.clipboard_append(digits)
            self.status_var.set("Цифры скопированы в буфер обмена!")
            ##messagebox.showinfo("Успех", "Цифры скопированы в буфер обмена!")
        else:
            self.show_error("Нет данных для копирования")

    # ================ ОБЩИЕ МЕТОДЫ ================

    def show_error(self, message):
        """Показывает сообщение об ошибке"""
        self.status_var.set("Ошибка!")
        self.read_btn.config(state='normal')
        self.read_screenshot_btn.config(state='normal')
        #messagebox.showerror("Ошибка", message)


def main():
    root = tk.Tk()

    # Проверяем наличие Tesseract OCR
    try:
        pytesseract.get_tesseract_version()
    except Exception:
        messagebox.showwarning("Внимание",
                               "Tesseract OCR не установлен или не найден в PATH.\n"
                               "Функция распознавания цифр со скриншотов может не работать.\n\n"
                               "Для установки Tesseract:\n"
                               "1. Скачайте с https://github.com/UB-Mannheim/tesseract/wiki\n"
                               "2. Установите и добавьте в PATH\n"
                               "3. Или укажите путь в коде: pytesseract.pytesseract.tesseract_cmd = r'C:\\...\\tesseract.exe'")

    app = QRCodeReaderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()