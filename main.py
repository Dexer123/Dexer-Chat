from datetime import datetime, timezone
from pathlib import Path
import os, sqlite3, base64
import flet as ft



settings_path = rf"{os.getenv('APPDATA')}\Dexer\Dexer's Chat\settings\settings.dx"
db_path = rf"{os.getenv('APPDATA')}\Dexer\Dexer's Chat"

Path(rf"{os.getenv('APPDATA')}\Dexer\Dexer's Chat\settings").mkdir(parents=True, exist_ok=True)

def b64e(s):
    return base64.b64encode(s.encode()).decode()


def b64d(s):
    return base64.b64decode(s).decode()


class Message():
    def __init__(self, user_name: str, text: str = '', message_type: str = 'chat_message', old_nickname: str = ''):
        self.user_name = user_name
        self.text = text
        self.message_type = message_type
        self.old_nickname = old_nickname


class ChatMessage(ft.Row):
    def __init__(self, message: Message):
        super().__init__()
        self.vertical_alignment = ft.CrossAxisAlignment.START
        self.controls = [
            ft.CircleAvatar(
                content=ft.Text(self.get_initials(message.user_name)),
                color=ft.colors.WHITE,
                bgcolor=self.get_avatar_color(message.user_name),
            ),
            ft.Column(
                [
                    ft.Text(message.user_name, weight="bold"),
                    ft.Text(message.text, selectable=True),
                ],
                tight=True,
                spacing=5,
            ),
        ]
        self.height=55
        

    def get_initials(self, user_name: str):
        if user_name:
            return user_name[:1].capitalize()
        else:
            return "Unknown"

    def get_avatar_color(self, user_name: str):
        colors_lookup = [
            ft.colors.AMBER,
            ft.colors.BLUE,
            ft.colors.BROWN,
            ft.colors.CYAN,
            ft.colors.GREEN,
            ft.colors.INDIGO,
            ft.colors.LIME,
            ft.colors.ORANGE,
            ft.colors.PINK,
            ft.colors.PURPLE,
            ft.colors.RED,
            ft.colors.TEAL,
            ft.colors.YELLOW,
        ]
        return colors_lookup[hash(user_name) % len(colors_lookup)]


def main(page: ft.Page):
    page.clean()
    page.title = "Dexer's Chat"
    page.theme_mode = 'system'
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.MainAxisAlignment.CENTER
    page.window.width = 360
    page.window.height = 450
    page.window.resizable = False
    page.window.maximizable = False
    page.padding = 10
    
    def auto_login():
        try:
            with open(settings_path, 'r') as settings:
                login = b64d(settings.readline())
                password = b64d(settings.readline())
            if login and password:
                db = sqlite3.connect(rf'{db_path}\DexerChat.db')
                cur = db.cursor()
                cur.execute(f"SELECT * FROM users WHERE login = ? AND password = ?", (login, password))
                user = cur.fetchone()
                if user != None:
                    snack('Вы успешно зашли!')
                    cur.execute("UPDATE users SET last_auth = ? WHERE id = ?", (datetime.now(timezone.utc).isoformat(), user[0]))
                    user_name = user[3]
                    page.pubsub.send_all(Message(user_name, message_type="login_message"))
                    page.session.set('user_name', user_name)
                    page.title = f"Dexer's Chat ({user_name})"
                    log_in(user_name)
        except:
            pass
    
    
    def change_theme(event):
        page.theme_mode = 'dark' if dd_check_theme.value == 'Темная' else 'light' if dd_check_theme.value == 'Светлая' else 'system'
        page.update()
        
    def save_settings(event):
        save_nickname()
        
    def save_nickname():
        if user_nickname.value.strip() != '':
            old_nickname = page.session.get('user_name')
            new_nickname = user_nickname.value
            page.session.set('user_name', new_nickname)
            db = sqlite3.connect(rf'{db_path}\DexerChat.db')
        
            cur = db.cursor()
            cur.execute('UPDATE users SET username = ? WHERE login = ?', (new_nickname, user[1]))
            db.commit()
            db.close
            page.pubsub.send_all(Message(new_nickname, message_type="nickname_change_message", old_nickname=old_nickname))
        log_in(page.session.get('user_name'))
    
    def snack(text):
        snack_bar = ft.SnackBar(ft.Text(text))
        page.overlay.append(snack_bar)
        snack_bar.open = True
    
    def focus_password(event):
        user_password.focus()
    
    def register(event):
        db = sqlite3.connect(rf'{db_path}\DexerChat.db')
        
        cur = db.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            login TEXT NOT NULL,
            password TEXT NOT NULL,
            username TEXT NOT NULL,
            reg_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            last_auth DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )""")

        login = user_login.value
        password = user_password.value
        cur.execute('INSERT INTO users (login, password, username) VALUES (?, ?, ?)', (login, password, login))
        
        db.commit()
        db.close()
        
        snack('Вы успешно зарегистрировались!')
        
        user_login.value = ''
        user_password.value = ''
        page.update()
        
    def auth(event):
        db = sqlite3.connect(rf'{db_path}\DexerChat.db')
        
        cur = db.cursor()
        cur.execute(f"SELECT * FROM users WHERE login = ? AND password = ?", (user_login.value, user_password.value))
        global user
        user = cur.fetchone()
        if user != None:
            snack('Вы успешно зашли!')
            cur.execute("UPDATE users SET last_auth = ? WHERE id = ?", (datetime.now(timezone.utc).isoformat(), user[0]))
            user_name = user[3]
            page.pubsub.send_all(Message(user_name, message_type="login_message"))
            page.session.set('user_name', user_name)
            user_login.value, user_password.value = '', ''
            page.title = f"Dexer's Chat ({user_name})"
            log_in(user_name)
            with open(settings_path, 'w') as settings:
                if check_remember.value:
                    settings.write(f"{b64e(user[1])}\n{b64e(user[2])}")
                else:
                    settings.write('')
                    
        else:
            snack('Неверно введены данные!')
            page.update()
        
        db.commit()
        db.close()

    def log_in(user_name):
        page.clean()
        user_nickname.value = page.session.get('user_name')
        page.horizontal_alignment = ft.MainAxisAlignment.START
        page.window.width = 450
        page.window.height = 550
        page.navigation_bar = None
        page.add(panel_chat, ft.Container(
                        content=chat,
                        border=ft.border.all(1, ft.colors.OUTLINE),
                        border_radius=5,
                        padding=10,
                        expand=True,
                    ), panel_message)
        page.update()

    def validate(event): # Проверка на пустые поля
        if all([user_login.value, user_password.value]):
            btn_reg.disabled = False
            btn_auth.disabled = False
        else:
            btn_reg.disabled = True
            btn_auth.disabled = True
        page.update()
    
    def settings(event): # Настройки
        page.clean()
        page.add(btn_back, user_nickname, check_theme, settings_btns)
        page.update()
    
    def exit(event):
        with open(settings_path, 'w') as settings:
            settings.write('')
        main(page)
    
    def on_message(msg: Message):
        if msg.message_type == "chat_message":
            m = ChatMessage(msg)
        elif msg.message_type == "login_message":
            m = ft.Text(f"{msg.user_name} присоединился к чату", italic=True, color='gray', size=12, height=25) # ft.colors.BLACK45
        elif msg.message_type == 'nickname_change_message':
            m = ft.Text(f"{msg.old_nickname} изменил имя на {msg.user_name}", italic=True, color='gray', size=12, height=25)
        chat.controls.append(m)
        page.update()

    def send_click(e):
        if new_message.value.strip() != '':
            page.pubsub.send_all(Message(user_name=page.session.get('user_name'), text=new_message.value))
            new_message.value = ''
            new_message.focus()
            page.update()
    
    # Авторизация/Регистрация
    user_login = ft.TextField(label='Логин', hint_text='Введите логин', max_length=20, max_lines=1, autofocus=True, on_change=validate)
    user_password = ft.TextField(label='Пароль', hint_text='Введите пароль', max_length=30, max_lines=1, password=True, can_reveal_password=True, on_change=validate)
    btn_reg = ft.ElevatedButton(text='Зарегистрироваться', on_click=register, disabled=True)
    btn_auth = ft.ElevatedButton(text='Авторизоваться', on_click=auth, disabled=True)
    check_remember = ft.Checkbox(label='Запомнить', scale=0.9)
    
    # Настройки
    btn_back = ft.Row([
            ft.IconButton(icon=ft.icons.ARROW_BACK, tooltip='Вернуться назад', on_click=log_in, alignment=ft.alignment.top_left),
            ft.Text('Версия: 1.0 beta', size=12, italic=True, color='gray') ])
    user_nickname = ft.TextField(label='Изменить имя', width=300, value=page.session.get('user_name'), max_length=20, max_lines=1, autofocus=True)
    dd_check_theme = ft.Dropdown(label='Тема', width=150, options=[ft.dropdown.Option('Системная'), ft.dropdown.Option('Темная'), ft.dropdown.Option('Светлая')], on_change=change_theme)
    check_theme = ft.Row([
            ft.Icon(ft.icons.LIGHT_MODE),
            dd_check_theme])
    btn_save = ft.ElevatedButton(text='Сохранить', icon=ft.icons.SAVE, on_click=save_settings)
    btn_exit = ft.ElevatedButton(text='Выйти из аккаунта', icon=ft.icons.EXIT_TO_APP, on_click=exit)
    btn_dev = ft.IconButton(icon=ft.icons.DEVELOPER_MODE, tooltip='Связаться с разработчиком', url='https://t.me/dexering')
    settings_btns = ft.Row([
            btn_save,
            btn_exit,
            btn_dev ])
    
    # Чат
    page.pubsub.subscribe(on_message)
    btn_send = ft.IconButton(icon=ft.icons.SEND_ROUNDED, tooltip='Отправить сообщение', on_click=send_click)
    btn_settings = ft.IconButton(icon=ft.icons.SETTINGS, tooltip='Открыть настройки', on_click=settings)
    new_message = ft.TextField(hint_text='Введите сообщение', max_length=150, autofocus=True, shift_enter=True, min_lines=1, max_lines=5, filled=True, expand=True, on_submit=send_click)
    chat = ft.ListView()
    
    panel_register = ft.Row(
        [
            ft.Column(
                [
                    ft.Text('Регистрация'),
                    user_login,
                    user_password,
                    check_remember,
                    btn_reg
                ]
            )
        ],
        alignment=ft.MainAxisAlignment.CENTER
    )
    
    panel_auth = ft.Row(
        [
            ft.Column(
                [
                    ft.Text('Авторизация'),
                    user_login,
                    user_password,
                    check_remember,
                    btn_auth
                ]
            )
        ],
        alignment=ft.MainAxisAlignment.CENTER
    )
    
    panel_chat = ft.Row(
        [
            ft.Text('Чат', size=25),
            btn_settings
        ],
        alignment=ft.MainAxisAlignment.END,
        spacing=page.window.width/2
    )
    
    panel_message = ft.Row(
        [
            new_message,
            btn_send
        ]
    )
                     
    def navigate(event):
        index = page.navigation_bar.selected_index
        page.clean()
        
        if index == 0: page.add(panel_auth);user_password.on_submit=auth
        elif index == 1: page.add(panel_register);user_password.on_submit=register
        page.update()
        
        
    page.navigation_bar = ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(icon=ft.icons.VERIFIED_USER, label='Авторизация'),
            ft.NavigationBarDestination(icon=ft.icons.APP_REGISTRATION, label='Регистрация')
        ],
        selected_index=0,
        on_change=navigate
    )
        
    user_login.on_submit=focus_password
    user_password.on_submit=auth
    page.add(panel_auth)
    auto_login()
    
    
ft.app(target=main)
