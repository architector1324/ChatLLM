import json
import ollama
import customtkinter as gui


class Model:
    PROMPTS_SUGGESTION = {
        'en': 'generate 2 simple and 2 interesting prompts (about 12 words) to ChatGPT. Use json schema: [{"prompt":"string", "topic":"string"}]',
        'ru': 'придумай 2 простых и 2 интересных промпта (не больше 12 слов) для ChatGPT на русском языке. Используй json схему: [{"prompt":"string", "topic":"string"}]'
    }

    def get_models():
        return [m['name'] for m in ollama.list()['models']]

    def __init__(self, name, lang='en'):
        self.name = name
        self.lang = lang

    def generate_suggestions(self):
        res = ollama.generate(model=self.name, prompt=Model.PROMPTS_SUGGESTION[self.lang])['response']
        return json.loads(res)
    
    def answer(self, prompt):
        return ollama.generate(model=self.name, prompt=prompt)['response']

    def answer_stream(self, prompt):
        return ollama.generate(model=self.name, prompt=prompt, stream=True)


class ChatLLM(gui.CTk):
    def __init__(self, settings):
        super().__init__()

        self.settings = settings
        self.chat = []
        self.model = None

        self.select_model_cb(Model.get_models()[0])

        self.title('ChatLLM')
        self.geometry('800x600')
        self.resizable(True, True)

        self._init_side_panel()
        self._init_chat()

    def _init_side_panel(self):
        self.side_panel_frame = gui.CTkFrame(self)
        self.side_panel_frame.grid(row=0, column=0, padx=20, pady=20, sticky='ns', rowspan=2)

        self.model_box = gui.CTkComboBox(self.side_panel_frame, values=Model.get_models(), command=self.select_model_cb)
        self.model_box.grid(row=0, column=0, padx=20, pady=20)

    def _init_chat(self):
        self.chat_frame = gui.CTkFrame(self)
        self.chat_frame.grid(row=0, column=1, padx=20, pady=20, stick='we')

        self.answer_entry = gui.CTkEntry(self.chat_frame)
        self.answer_entry.grid(row=1, column=0, padx=(20, 0), pady=20)

        self.answer_go = gui.CTkButton(self.chat_frame, text='>', width=28, command=self.answer_cb)
        self.answer_go.grid(row=1, column=1, padx=(0, 20), pady=20, stick='we')

        self.chat_textbox = gui.CTkTextbox(self.chat_frame)
        self.chat_textbox.configure(state='disabled')
        self.chat_textbox.grid(row=0, column=0, padx=20, pady=20, columnspan=2, stick='we')

    def select_model_cb(self, name):
        print(name)
        self.model = Model(name, settings['lang'])
        # suggestions = self.model.generate_suggestions()
        # print(suggestions)

    def update_chat(self):
        self.chat_textbox.configure(state='normal')
        self.chat_textbox.delete('0.0', 'end')
        self.chat_textbox.insert('0.0', '\n'.join(self.chat))
        self.chat_textbox.configure(state='disabled')
        self.update()

    def answer_cb(self):
        prompt = self.answer_entry.get()
        self.answer_entry.delete(0, 'end')

        self.chat.append(prompt)
        self.update_chat()

        self.chat.append('')
        for t in self.model.answer_stream(prompt):
            self.chat[-1] += t['response']
            self.update_chat()


# settings
settings = {
    'theme': 'dark',
    'color': 'blue',
    'lang': 'en'
}

# app
gui.set_appearance_mode(settings['theme'])
gui.set_default_color_theme(settings['color'])

app = ChatLLM(settings)
app.mainloop()
