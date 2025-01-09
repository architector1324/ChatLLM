#!/bin/python

import json
import random

import ollama
import datetime
import pyperclip

import flet as ft


class Model:
    def get_models():
        try:
            return [m.model for m in ollama.list()['models']]
        except ollama.ResponseError:
            return ['none']

    def __init__(self, name, lang='en'):
        self.name = name
        self.lang = lang

    def prompt(self, prompt, context):
        return ollama.generate(model=self.name, prompt=prompt, context=context)['response']

    def prompt_stream(self, prompt, context):
        return ollama.generate(model=self.name, prompt=prompt, context=context, stream=True)


def main(page: ft.Page):
    # settings
    settings = json.load(open('settings.json', 'r', encoding='utf-8'))
    topics = json.load(open('topics.json', 'r', encoding='utf-8'))

    page.title = 'ChatLLM'
    page.theme_mode = settings['theme']
    page.theme = ft.Theme(color_scheme_seed=settings['color'])

    model = None

    chat = []
    answering = False

    prompt_suggestions = random.sample(topics[settings['lang']], 4)

    # handlers
    def models_update(_):
        model_box.options = [ft.dropdown.Option(m) for m in Model.get_models()]
        page.update()


    def model_load_clicked(_):
        nonlocal model
        nonlocal prompt_suggestions

        model = Model(model_box.value, settings['lang'])

        prompt_go.disabled = False
        page.snack_bar = ft.SnackBar(content=ft.Text(model_box.value), duration=1000)
        page.snack_bar.open = True
        page.update()

        if chat:
            return

        if prompt_suggestions_grid not in chat_stack.controls:
            chat_stack.controls.append(prompt_suggestions_grid)
            page.update()


    def theme_switched(_):
        settings['theme'] = 'dark' if theme_switch.value == 0 else 'light'
        page.theme_mode = settings['theme']
        page.update()


    def prompt_suggestion_click(i):
        prompt_entry.value = prompt_suggestions[i]['prompt']

        if prompt_suggestions_grid in chat_stack.controls:
            chat_stack.controls.remove(prompt_suggestions_grid)
        page.update()


    def chat_entry_reply_click(i):
        prompt_entry.value = '\n'.join([f'> {m}' for m in chat[i]['content'].split('\n')])
        page.update()


    def chat_add_entry(entry):
        chat.append(entry)

        body = ft.Markdown(entry['content'], selectable=True, extension_set=ft.MarkdownExtensionSet.GITHUB_FLAVORED, code_theme='atom-one-dark', code_style=ft.TextStyle(font_family="monospace"),on_tap_link=lambda e: page.launch_url(e.data))
        icon = ft.Icon(ft.Icons.ACCOUNT_CIRCLE) if entry['role'] == 'user' else ft.Icon(ft.Icons.COMPUTER)
        panel = ft.Row([
            ft.IconButton(icon=ft.Icons.REPLY_ROUNDED, on_click=lambda _, i=len(chat)-1: chat_entry_reply_click(i)),
            ft.IconButton(icon=ft.Icons.CONTENT_COPY_ROUNDED, on_click=lambda _, i=len(chat)-1: pyperclip.copy(chat[i]['content']))
        ])
        column = ft.Column([icon, body, panel])

        container = ft.Container(content=column, bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST, border_radius=ft.border_radius.all(10), padding=10)

        chat_entries.controls.append(container)
        page.update()


    def chat_to_str(in_json=False):
        if not in_json:
            return '\n'.join([f"{e['role']}:\n{e['content']}\n" for e in chat])

        return json.dumps(chat, ensure_ascii=False)


    def chat_update_entry(i, entry):
        chat_entries.controls[i].content.controls[1].value = entry['content']
        page.update()


    def clear_chat_clicked(_):
        chat.clear()
        chat_entries.controls.clear()

        if prompt_suggestions_grid not in chat_stack.controls:
            chat_stack.controls.append(prompt_suggestions_grid)
        page.update()


    def clear_context_clicked(_):
        if not chat:
            return

        chat[-1]['context'] = None
        page.snack_bar = ft.SnackBar(content=ft.Text('Context cleared'), duration=1000)
        page.snack_bar.open = True
        page.update()


    def copy_chat_click(_):
        pyperclip.copy(chat_to_str())

        page.snack_bar = ft.SnackBar(content=ft.Text('Chat copied'), duration=1000)
        page.snack_bar.open = True
        page.update()


    def save_chat_click(e: ft.FilePickerResultEvent):
        if not e.path:
            return

        with open(e.path, 'w', encoding='utf-8') as f:
            page.snack_bar = ft.SnackBar(content=ft.Text(f'Chat saved: {e.path}'), duration=1000)
            page.snack_bar.open = True
            page.update()
            f.write(chat_to_str())


    def prompt_focus(_):
        prompt_entry.hint_text = random.choice(topics[settings['lang']])['prompt']
        page.update()


    def prompt_go_clicked(_):
        nonlocal answering

        def stop():
            nonlocal answering

            answering = False
            prompt_go.color = ft.Colors.PRIMARY
            prompt_go.bgcolor = ft.Colors.ON_INVERSE_SURFACE
            prompt_go.text = 'Go'
            chat_control.disabled = False
            page.update()

        if answering or not model:
            stop()
            return

        prompt = prompt_entry.value
        prompt_entry.value = None

        if not prompt:
            return

        answering = True
        if prompt_suggestions_grid in chat_stack.controls:
            chat_stack.controls.remove(prompt_suggestions_grid)
        chat_control.disabled = True

        prompt_go.color = ft.Colors.WHITE
        prompt_go.bgcolor = ft.Colors.ERROR_CONTAINER
        prompt_go.text = 'Stop'

        context = chat[-1]['context'] if chat else None

        chat_add_entry({'role': 'user', 'content': prompt, 'context': context, 'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
        chat_add_entry({'role': 'assistant', 'content': '', 'context': context, 'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})

        stream = model.prompt_stream(prompt, context)
        for t in stream:
            if not answering:
                stream.close()
                break
            chat[-1]['content'] += t['response']
            chat[-1]['context'] = t['context'] if t['done'] else chat[-1]['context']
            chat_update_entry(len(chat) - 1, chat[-1])

        stop()


    # app
    model_box = ft.Dropdown(label='model', options=[ft.dropdown.Option(m) for m in Model.get_models()], on_change=model_load_clicked, on_click=models_update)
    theme_switch = ft.Switch(thumb_icon=ft.Icons.LIGHT_MODE_ROUNDED, on_change=theme_switched)

    prompt_entry = ft.TextField(value='', label='prompt', multiline=True, shift_enter=True, expand=True, border_radius=10, on_submit=prompt_go_clicked, on_focus=prompt_focus)
    prompt_go = ft.ElevatedButton(text='Go', on_click=prompt_go_clicked, disabled=True, bgcolor=ft.Colors.ON_INVERSE_SURFACE, color=ft.Colors.PRIMARY)

    save_chat_dialog = ft.FilePicker(on_result=save_chat_click)

    save_chat = ft.IconButton(icon=ft.Icons.SAVE_ALT_ROUNDED, tooltip='Save chat', on_click=lambda _: save_chat_dialog.save_file())
    copy_chat = ft.IconButton(icon=ft.Icons.CONTENT_COPY_ROUNDED, tooltip='Copy chat', on_click=copy_chat_click)
    clear_chat = ft.IconButton(icon=ft.Icons.DELETE_ROUNDED, tooltip='Clear chat', on_click=clear_chat_clicked)
    clear_context = ft.IconButton(icon=ft.Icons.INSERT_DRIVE_FILE_ROUNDED, tooltip='Clear context', on_click=clear_context_clicked)

    # chat_control = ft.Container(
    #     content=ft.Row([
    #         save_chat,
    #         copy_chat,
    #         clear_chat,
    #         clear_context,
    #     ], alignment=ft.MainAxisAlignment.CENTER), alignment=ft.alignment.bottom_center, disabled=True)
    
    chat_control = ft.Row([
            save_chat,
            copy_chat,
            clear_chat,
            clear_context,
        ], alignment=ft.MainAxisAlignment.CENTER, disabled=True)

    chat_entries = ft.ListView(expand=True, auto_scroll=True, spacing=15, padding=20)
    chat_container = ft.Container(content=chat_entries, border_radius=ft.border_radius.all(10), bgcolor=ft.Colors.ON_INVERSE_SURFACE, expand=True)

    prompt_suggestions_containers = [
        ft.Container(
            content=ft.Text(prompt_suggestions[i]['prompt']),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            border_radius=ft.border_radius.all(10),
            padding=10,
            alignment=ft.alignment.center,
            expand=True,
            on_click=lambda _, i=i: prompt_suggestion_click(i)
        ) for i in range(4)
    ]

    prompt_suggestions_grid = ft.Column([
        ft.Row([prompt_suggestions_containers[0], prompt_suggestions_containers[1]], expand=True),
        ft.Row([prompt_suggestions_containers[2], prompt_suggestions_containers[3]], expand=True)
    ], expand=True)

    chat_stack = ft.Stack([chat_container, chat_control], expand=True)

    page.overlay.append(save_chat_dialog)

    page.add(
        ft.Row([
            model_box,
            ft.Container(content=ft.Column([theme_switch], expand=True), alignment=ft.alignment.center_right, expand=True)
        ]),
        chat_stack,
        ft.Row([prompt_entry, prompt_go])
    )


ft.app(target=main)
