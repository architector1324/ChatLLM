import json
import random

import flet as ft
import ollama


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

    model = None

    chat = []
    answering = False

    prompt_suggestions = random.sample(topics[settings['lang']], 4)

    # handlers
    def model_selected(_e):
        model_load.disabled = False
        page.update()


    def model_load_clicked(_e):
        nonlocal model
        nonlocal prompt_suggestions

        model = Model(model_box.value, settings['lang'])

        prompt_go.disabled = False
        page.snack_bar = ft.SnackBar(content=ft.Text(model_box.value), duration=1000)
        page.snack_bar.open = True

        if chat:
            return

        page.controls[1].content = prompt_suggestions_grid
        page.update()


    def theme_switched(_e):
        settings['theme'] = 'dark' if theme_switch.value == 0 else 'light'
        page.theme_mode = settings['theme']
        page.update()


    def prompt_suggestion_click(i):
        prompt_entry.value = prompt_suggestions[i]['prompt']
        page.controls[1].content = chat_entries
        page.update()


    def chat_add_entry(entry):
        chat.append(entry)

        entry_body = ft.Markdown(entry['msg'], selectable=True, extension_set=ft.MarkdownExtensionSet.GITHUB_WEB, on_tap_link=lambda e: page.launch_url(e.data))
        column = ft.Column([ft.Icon(ft.icons.ACCOUNT_CIRCLE) if entry['who'] == 'user' else ft.Icon(ft.icons.COMPUTER), entry_body])
    
        container = ft.Container(content=column, bgcolor=ft.colors.GREY_800, border_radius=ft.border_radius.all(10), padding=10)

        chat_entries.controls.append(container)
        page.update()


    def chat_update_entry(i, entry):
        chat_entries.controls[i].content.controls[1].value = entry['msg']
        page.update()


    def prompt_go_clicked(_e):
        answering = True

        prompt = prompt_entry.value
        prompt_entry.value = None

        context = chat[-1]['ctx'] if chat else None

        chat_add_entry({'who': 'user', 'msg': prompt, 'ctx': context})
        chat_add_entry({'who': 'ai', 'msg': '', 'ctx': context})

        stream = model.prompt_stream(prompt, context)
        for t in stream:
            if not answering:
                stream.close()
                break
            chat[-1]['msg'] += t['response']
            chat[-1]['ctx'] = t['context'] if t['done'] else chat[-1]['ctx']
            chat_update_entry(len(chat) - 1, chat[-1])

        answering = False


    # app
    model_box = ft.Dropdown(label='model', options=[ft.dropdown.Option(m) for m in Model.get_models()], on_change=model_selected)
    model_load = ft.ElevatedButton(text='Load', on_click=model_load_clicked, disabled=True)
    theme_switch = ft.Switch(label='light', on_change=theme_switched)

    prompt_entry = ft.TextField(value='', label='prompt', multiline=True, hint_text=random.choice(topics[settings['lang']])['prompt'], expand=True)
    prompt_go = ft.ElevatedButton(text='Go', on_click=prompt_go_clicked, disabled=True)

    chat_entries = ft.ListView(expand=True, auto_scroll=True, spacing=15, padding=20)

    prompt_suggestions_containers = [
        ft.Container(
            content=ft.Text(prompt_suggestions[i]['prompt']),
            bgcolor=ft.colors.GREY_800,
            border_radius=ft.border_radius.all(10),
            padding=10,
            alignment=ft.alignment.center,
            expand=True,
            on_click=lambda e, i=i: prompt_suggestion_click(i)
        ) for i in range(4)
    ]

    prompt_suggestions_grid = ft.Column([
        ft.Row([prompt_suggestions_containers[0], prompt_suggestions_containers[1]], expand=True),
        ft.Row([prompt_suggestions_containers[2], prompt_suggestions_containers[3]], expand=True)
    ], expand=True)

    page.add(
        ft.Row([
            model_box,
            model_load,
            theme_switch
        ]),
        ft.Container(content=chat_entries, border_radius=ft.border_radius.all(10), bgcolor=ft.colors.GREY_900, expand=True),
        ft.Row([prompt_entry, prompt_go])
    )


app = ft.app(target=main)
