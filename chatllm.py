import json
import random

import ollama
import pyperclip
import flet as ft


class Model:
    def get_models():
        return [m['name'] for m in ollama.list()['models']]

    def __init__(self, name, lang='en'):
        self.name = name
        self.lang = lang

    def prompt(self, prompt, context):
        return ollama.generate(model=self.name, prompt=prompt, context=context)['response']

    def prompt_stream(self, prompt, context):
        return ollama.generate(model=self.name, prompt=prompt, context=context, stream=True)


def main(page: ft.Page):
    # settings
    settings = json.load(open('settings.json', 'r'))
    topics = json.load(open('topics.json', 'r'))

    page.title = 'ChatLLM'
    page.theme_mode = settings['theme']
    page.theme = ft.Theme(color_scheme_seed=settings['color'])

    model = None

    chat = []
    answering = False

    prompt_suggestions = random.sample(topics[settings['lang']], 4)

    # handlers
    def model_selected(_):
        model_load.disabled = False
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

        page.controls[2].content = prompt_suggestions_grid
        page.update()


    def theme_switched(_):
        settings['theme'] = 'dark' if theme_switch.value == 0 else 'light'
        page.theme_mode = settings['theme']
        page.update()


    def prompt_suggestion_click(i):
        prompt_entry.value = prompt_suggestions[i]['prompt']
        page.controls[2].content = chat_entries
        page.update()


    def chat_entry_copy_click(i):
        pyperclip.copy(chat[i]['msg'])


    def chat_add_entry(entry):
        chat.append(entry)

        body = ft.Markdown(entry['msg'], selectable=True, extension_set=ft.MarkdownExtensionSet.GITHUB_FLAVORED, code_theme='atom-one-dark', code_style=ft.TextStyle(font_family="monospace"),on_tap_link=lambda e: page.launch_url(e.data))
        panel = ft.Row([
            ft.Icon(ft.icons.ACCOUNT_CIRCLE, ft.alignment.center_right) if entry['who'] == 'user' else ft.Icon(ft.icons.COMPUTER, ft.alignment.center_right),
            ft.IconButton(icon=ft.icons.CONTENT_COPY_ROUNDED, on_click=lambda _, i=len(chat)-1: chat_entry_copy_click(i), alignment=ft.alignment.center_right)
        ])
        column = ft.Column([panel, body])

        container = ft.Container(content=column, bgcolor=ft.colors.SURFACE_VARIANT, border_radius=ft.border_radius.all(10), padding=10)

        chat_entries.controls.append(container)
        page.update()


    def chat_to_str():
        out = ''
        for e in chat:
            out += f"{e['who']}:\n{e['msg']}\n\n"
        return out

    def chat_update_entry(i, entry):
        chat_entries.controls[i].content.controls[1].value = entry['msg']
        page.update()


    def clear_chat_clicked(_):
        chat.clear()
        chat_entries.controls.clear()
        page.controls[1].controls.clear()
        page.controls[2].content = prompt_suggestions_grid
        page.update()


    def clear_context_clicked(_):
        chat[-1]['ctx'] = None
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

        with open(e.path, 'w') as f:
            f.write(chat_to_str())


    def prompt_go_clicked(_):
        nonlocal answering

        def stop():
            nonlocal answering

            answering = False
            prompt_go.color = ft.colors.PRIMARY
            prompt_go.bgcolor = ft.colors.ON_INVERSE_SURFACE
            prompt_go.text = 'Go'
            page.controls[1].disabled = False
            page.update()

        if answering or not model:
            stop()
            return

        prompt = prompt_entry.value
        prompt_entry.value = None

        if not prompt:
            return

        answering = True
        page.controls[2].content = chat_entries
        page.controls[1].controls = [save_chat, copy_chat, clear_chat, clear_context]
        page.controls[1].disabled = True

        prompt_go.color = ft.colors.WHITE
        prompt_go.bgcolor = ft.colors.ERROR_CONTAINER
        prompt_go.text = 'Stop'

        context = chat[-1]['ctx'] if chat else None

        chat_add_entry({'who': 'user', 'msg': prompt, 'ctx': context})
        chat_add_entry({'who': 'assistant', 'msg': '', 'ctx': context})

        stream = model.prompt_stream(prompt, context)
        for t in stream:
            if not answering:
                stream.close()
                break
            chat[-1]['msg'] += t['response']
            chat[-1]['ctx'] = t['context'] if t['done'] else chat[-1]['ctx']
            chat_update_entry(len(chat) - 1, chat[-1])

        stop()


    # app
    model_box = ft.Dropdown(label='model', options=[ft.dropdown.Option(m) for m in Model.get_models()], on_change=model_selected)
    model_load = ft.ElevatedButton(text='Load', on_click=model_load_clicked, disabled=True)
    theme_switch = ft.Switch(label='light', on_change=theme_switched)

    prompt_entry = ft.TextField(value='', label='prompt', hint_text=random.choice(topics[settings['lang']])['prompt'], multiline=True, shift_enter=True, expand=True, border_radius=10, on_submit=prompt_go_clicked)
    prompt_go = ft.ElevatedButton(text='Go', on_click=prompt_go_clicked, disabled=True, bgcolor=ft.colors.ON_INVERSE_SURFACE, color=ft.colors.PRIMARY)

    save_chat_dialog = ft.FilePicker(on_result=save_chat_click)
    save_chat = ft.ElevatedButton(text='Save', on_click=lambda _: save_chat_dialog.save_file())
    copy_chat = ft.ElevatedButton(text='Copy', on_click=copy_chat_click)

    clear_chat = ft.ElevatedButton(text='Clear', on_click=clear_chat_clicked)
    clear_context = ft.ElevatedButton(text='Clear context', on_click=clear_context_clicked)

    chat_entries = ft.ListView(expand=True, auto_scroll=True, spacing=15, padding=20)

    prompt_suggestions_containers = [
        ft.Container(
            content=ft.Text(prompt_suggestions[i]['prompt']),
            bgcolor=ft.colors.SURFACE_VARIANT,
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

    page.overlay.append(save_chat_dialog)

    page.add(
        ft.Row([
            model_box,
            model_load,
            theme_switch
        ]),
        ft.Row([]),
        ft.Container(content=chat_entries, border_radius=ft.border_radius.all(10), bgcolor=ft.colors.ON_INVERSE_SURFACE, expand=True),
        ft.Row([prompt_entry, prompt_go])
    )


app = ft.app(target=main)
