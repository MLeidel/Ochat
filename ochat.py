#
# ochat.py
# wxPython GUI with Ollama API`
#
import os
import sys
import iniproc
import markdown
import webbrowser
import subprocess
from time import localtime, strftime
import wx
import json
import platform
from time import localtime, strftime
from ollama import chat

opts = [] # loading options from the options.ini file into a list
opts = iniproc.read("options.ini", 'model',     # 0
                                   'fontsz1',   # 1
                                   'fontsz2',   # 2
                                   'role',      # 3
                                   'log',       # 4
                                   'editor',    # 5
                                   'font1',     # 6
                                   'font2',     # 7
                                   'height',    # 8
                                   'color')     # 9
intro = f'''
Welcome to OChat
    Ollama 'chat' API for most models

Current Options:

    Model: {opts[0]}
    role: {opts[3]}
    log: {opts[4]}
    font1: {opts[6]}  {opts[1]}
    font2: {opts[7]}  {opts[2]}
    color: {opts[9]}
    editor: {opts[5]}
    prompt height: {opts[8]}
'''

class MyFrame(wx.Frame):
    def __init__(self, parent, title="OChat V1.0 Ollama " + opts[0]):
        super(MyFrame, self).__init__(parent, title=title, size=(600, 550))

        panel = wx.Panel(self)
        sizer = wx.GridBagSizer(5, 5)

        self.cpath = "conversation.json"

        # ----------------------------
        # First Text Widget (text1) the Prompt area
        # ----------------------------
        # This TextCtrl will expand horizontally but not vertically
        self.text1 = wx.TextCtrl(panel, style=wx.TE_MULTILINE)
        sizer.Add(
            self.text1,
            pos=(0, 0),          # Position at row 0, column 0
            span=(1, 5),         # Span of 1 row and 2 columns
            flag=wx.EXPAND       # Allow horizontal expansion
        )
        sizer.SetItemMinSize(self.text1, self.text1.GetSize().GetWidth(), 125)  # Set minimum height
        self.text1.Bind(wx.EVT_KEY_DOWN, self.on_key_down_hotkeys)
        self.text1.SetToolTip("Enter Prompt in this field")
        sizer.SetItemMinSize(self.text1, self.text1.GetSize().GetWidth(), int(opts[8]))  # Height
        self.text1.SetFocus()

        # ----------------------------
        # Second Text Widget (text2) the response area
        # ----------------------------
        # This TextCtrl will expand both horizontally and vertically
        self.text2 = wx.TextCtrl(panel, style=wx.TE_MULTILINE)  # wx.TE_DONTWRAP
        sizer.Add(
            self.text2,
            pos=(1, 0),          # Position at row 1, column 0
            span=(1, 5),         # Span of 1 row and 2 columns
            flag=wx.EXPAND       # Allow both horizontal and vertical expansion
        )
        self.text2.Bind(wx.EVT_KEY_DOWN, self.on_key_down_hotkeys)
        color_attr = wx.TextAttr()
        color_attr.SetTextColour(wx.Colour(opts[9]))  # "color"
        # Set the default style for all text written from now on
        self.text2.SetDefaultStyle(color_attr)
        self.text2.WriteText(intro)
        #self.text2.SetValue(intro)

        # ----------------------------
        # Clear Button
        # ----------------------------
        clear_btn = wx.Button(panel, label="Clear")
        sizer.Add(
            clear_btn,
            pos=(2, 0),          # Position at row 2, column 0
            span=(1, 1),         # Span of 1 row and 1 column
            flag=wx.EXPAND | wx.ALL, # Align to bottom-right
            border=5  # behaves like a "margin"
        )
        # Bind the close button event to the handler
        clear_btn.Bind(wx.EVT_BUTTON, self.on_new)
        clear_btn.SetToolTip("Start new Conversation")

        # ----------------------------
        # Export Button
        # ----------------------------
        export_btn = wx.Button(panel, label="Export")
        sizer.Add(
            export_btn,
            pos=(2, 1),          # Position at row 2, column 1
            span=(1, 1),         # Span of 1 row and 1 column
            flag=wx.EXPAND | wx.ALL, # Align to bottom-right
            border=5  # behaves like a "margin"
        )
        # Bind the close button event to the handler
        export_btn.Bind(wx.EVT_BUTTON, self.on_export)
        export_btn.SetToolTip("Open response in web browser")

        # ----------------------------
        # View Button
        # ----------------------------
        view_btn = wx.Button(panel, label="View Log")
        sizer.Add(
            view_btn,
            pos=(2, 2),          # Position at row 2, column 2
            span=(1, 1),         # Span of 1 row and 1 column
            flag=wx.EXPAND | wx.ALL, # Align to bottom-right
            border=5  # behaves like a "margin"
        )
        # Bind the close button event to the handler
        view_btn.Bind(wx.EVT_BUTTON, self.on_view)

        # ----------------------------
        # Submit Button
        # ----------------------------
        submit_btn = wx.Button(panel, label="Submit")
        sizer.Add(
            submit_btn,
            pos=(2, 3),          # Position at row 2, column 3
            span=(1, 1),         # Span of 1 row and 1 column
            flag=wx.EXPAND | wx.ALL, # Align to bottom-right
            border=5  # behaves like a "margin"
        )
        submit_btn.SetToolTip(f"Submit prompt to {opts[1]} (Ctrl-G)")
        submit_btn.Bind(wx.EVT_BUTTON, self.on_submit)

        # ----------------------------
        # Close Button
        # ----------------------------
        close_btn = wx.Button(panel, label="Close")
        sizer.Add(
            close_btn,
            pos=(2, 4),          # Position at row 2, column 4
            span=(1, 1),         # Span of 1 row and 1 column
            flag=wx.EXPAND | wx.ALL, # Align to bottom-right
            border=5  # behaves like a "margin"
        )
        # Bind the close button event to the handler
        close_btn.Bind(wx.EVT_BUTTON, self.on_close)
        close_btn.SetToolTip("Ctrl-Q")


        # ----------------------------
        # Configure Growable Columns and Rows
        # ----------------------------
        sizer.AddGrowableCol(0, 1)    # Column 0 for Submit button & response area grows horizontally
        sizer.AddGrowableCol(1, 1)    # Clear button grows horizontally
        sizer.AddGrowableCol(2, 1)    # Export button grows horizontally
        sizer.AddGrowableCol(3, 1)    #
        sizer.AddGrowableCol(4, 1)    #
        sizer.AddGrowableRow(1, 1)    #

        panel.SetSizer(sizer)

        #----------------------------
        # set window metrics from winfo file
        # ----------------------------
        if os.path.isfile("winfo"):
            with open("winfo", "r", encoding='utf-8') as fin:
                winfo = fin.read()
            p = winfo.split("|")
            x, y, w, h = int(p[0]), int(p[1]), int(p[2]), int(p[3])
            position = wx.Point(x, y)
            self.SetPosition(position)
            self.SetSize(wx.Size(w, h))

        #----------------------------
        # SET CUSTOM FONTS
        # https://docs.wxpython.org/wx.FontInfo.html#wx-fontinfo
        # https://docs.wxpython.org/wx.FontFamily.enumeration.html#wx-fontfamily
        if platform.system() == "Windows":
            custom_font1 = wx.Font(
                        int(opts[1]),
                        wx.FONTFAMILY_DEFAULT,
                        wx.FONTSTYLE_NORMAL,
                        wx.FONTWEIGHT_NORMAL,
                        False,
                        opts[6]
            )
            self.text1.SetFont(custom_font1)

            custom_font2 = wx.Font(
                        int(opts[2]),           # Font size
                        wx.FONTFAMILY_DEFAULT,  # Font family: MODERN is typically monospaced
                        wx.FONTSTYLE_NORMAL,    # Font style
                        wx.FONTWEIGHT_NORMAL,   # Font weight
                        False,                  # Underlined
                        opts[7]                 # Face name
            )
            self.text2.SetFont(custom_font2)
        else:  # not Windows ...
            custom_font1 = wx.Font(
                        int(opts[1]),
                        wx.FONTFAMILY_DEFAULT,
                        wx.FONTSTYLE_NORMAL,
                        wx.FONTWEIGHT_NORMAL,
                        False,
                        opts[6]
            )
            self.text1.SetFont(custom_font1)

            custom_font2 = wx.Font(
                        int(opts[2]),           # Font size
                        wx.FONTFAMILY_DEFAULT,  # Font family: MODERN is typically monospaced
                        wx.FONTSTYLE_NORMAL,    # Font style
                        wx.FONTWEIGHT_NORMAL,   # Font weight
                        False,                  # Underlined
                        opts[7]                 # Face name
            )
            self.text2.SetFont(custom_font2)


        # DISABLE View Log if not set to 'on'
        if opts[4] == "off":
            view_btn.Enable(False)
            view_btn.SetToolTip("Log is 'off'")
        else:
            view_btn.SetToolTip("View past queries")

        # get conversation status and initialize

        self.conversation = self.load_buffer(self.cpath)

        if self.conversation == []:
            self.conversation = [
                {"role": "system", "content": opts[3]}
            ]
            if os.path.isfile(self.cpath):
                os.remove(self.cpath)
        else:
            self.on_new(None)

        self.Show()


    # ----------------------------
    #   Event handlers follow
    # ----------------------------

    def on_new(self, event):
        ''' Event handler for the Clear button.
        Optionally starts new conversation '''
        dlg = wx.MessageDialog(
            self,
            "Do you want to start a new conversation?",
            "New Confirm",  # title
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION
        )
        result = dlg.ShowModal()
        dlg.Destroy()

        if result == wx.ID_YES:
            # start new conversation
            self.conversation.clear()
            self.conversation = [
                {"role": "system", "content": opts[3]}
            ]
            if os.path.isfile(self.cpath):
                os.remove(self.cpath)
            self.text1.SetValue("")
            self.text2.SetValue(intro)


    def save_buffer(self, buf, path):
        with open(self.cpath, "w", encoding="utf-8") as f:
            json.dump(buf, f, ensure_ascii=False, indent=2)


    def load_buffer(self, path):
        try:
            with open(self.cpath, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return []
        except json.JSONDecodeError:
            # corrupted file -> start clean
            return []
        # corrupted file -> start clean
        return []


    def on_close(self, event):
        ''' Event handler for the Close button.'''
        # save Window metrics
        pos = self.GetPosition()
        x, y = str(pos[0]), str(pos[1])
        size = self.GetSize()
        w, h = str(size[0]), str(size[1])
        with open("winfo", "w") as fout:
            fout.write(x + "|" + y + "|" + w + "|" + h)
        self.Close()


    def on_clear(self, event):
        ''' Event handler for the Clear button.'''
        dlg = wx.MessageDialog(
            self,
            "Do you want to clear PROMPT and RESPONSE areas?",  # content
            "Confirm Clear",  # title
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION
        )
        result = dlg.ShowModal()
        dlg.Destroy()

        if result == wx.ID_YES:
            self.text1.SetValue("")
            self.text2.SetValue(intro)


    def on_export(self, event):
        ''' convert MD file to HTML file and open in default browser '''
        mdtext = self.text2.GetValue()
        htmlText = markdown.markdown(mdtext, extensions=['tables', 'fenced_code'])
        htmlFile = "exported.html"
        # open in default browser
        with open(htmlFile, 'w', encoding='utf-8') as file:
            file.write(htmlText)
        webbrowser.open(htmlFile)


    def on_view(self, event):
        ''' view the current log
            if set to "on" in options '''
        if not os.path.isfile("log.md"):
            wx.MessageBox("Log File Not Found", "Oops!")
            return
        with open("log.md", "r", encoding='utf-8') as fin:
            self.text2.SetValue(fin.read())
        self.text2.SetFocus()
        self.text2.SetInsertionPointEnd()


    def delete_log(self):
        ''' User presses Ctrl-D for option to delete log file '''
        dlg = wx.MessageDialog(
            self,
            "Do you want to clear the current log file?",
            "Clear Log Confirm",
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION
        )
        result = dlg.ShowModal()
        dlg.Destroy()

        if result == wx.ID_YES:
            if os.path.isfile("log.md"):
                os.remove("log.md")


    def on_submit(self, event):
        ''' Event handler for Submit button (Ctrl-G). '''
        self.text2.SetValue("Thinking . .  .   .    .")
        wx.Yield()
        query = self.text1.GetValue()

        # 1) add the user message
        self.conversation.append(
            {"role": "user", "content": query}
        )
        # 2) call the chat completion
        ai_text = self.gptCode(opts[0], self.conversation)

        if ai_text == "":
            self.text2.SetValue("")
            self.text1.SetValue("")
            return

        # 3) add the assistant reply to history
        self.conversation.append(
            {"role": "assistant", "content": ai_text}
        )

        # 4) show it
        self.text2.SetValue(ai_text)

        # SAVE conversation to disk
        self.save_buffer(self.conversation, self.cpath)
        if ai_text == "":
            self.text2.SetValue("")
            self.text1.SetValue("")
            return
        self.text2.SetValue(ai_text)
        if opts[4].lower() == "on":
            today = strftime("%a %d %b %Y", localtime())
            tm    = strftime("%H:%M", localtime())
            with open("log.md", "a", encoding="utf-8") as fout:
                fout.write("\n\n=== Chat on %s %s ===\n\n" % (today, tm))
                #fout.write(f"{prompt}, {completion}, {total} \n\n")
                for msg in self.conversation:
                    role = msg["role"]
                    fout.write(f"{role.upper()}:\n{msg['content']}\n\n")
                fout.write("="*40 + "\n\n")

        # clear the input query box
        self.text1.SetValue("")
        # Speak response, if speach is on ...
        # if self.playback is True:
        #     self.speak_text(ai_text)

        # # put these token values into the status bar
        # self.info_label.SetLabel(f"Tokens: Prompt {prompt}  Completion {completion}  Total: {total}")


    def gptCode(self, model: str, query: str) -> str:
        ''' method to access Gemini API '''
        try:

            response = chat(model=model, messages=query)

            return response.message.content

        except Exception as e:
            wx.MessageBox(str(e), 'Info', wx.OK | wx.ICON_ERROR)
            return ""


    def on_key_down_hotkeys(self, event):
        ''' Set up HotKeys for the App '''
        keycode = event.GetKeyCode()
        modifiers = event.GetModifiers()

        if modifiers == (wx.MOD_CONTROL | wx.MOD_ALT) and keycode == ord('C'):  # Ctrl-Alt C on copy code
            self.on_copy_code()
        elif modifiers == wx.MOD_CONTROL and keycode == ord('F'):  # Ctrl+F: open search dialog.
            self.doSearchDialog()
        elif modifiers == wx.MOD_CONTROL and keycode == ord('N'):  # Ctrl+N: find next occurrence.
            self.findNext()
        elif modifiers == wx.MOD_CONTROL and keycode == ord('G'):
            self.on_submit(event)
        elif modifiers == wx.MOD_CONTROL and keycode == ord('Q'):
            self.on_close(event)
        elif modifiers == wx.MOD_CONTROL and keycode == ord('O'):  # Ctrl+O: open editor with options
            self.openEditor()
        elif modifiers == wx.MOD_CONTROL and keycode == ord('H'):  # Ctrl+F: open search dialog.
            self.on_help_dialog()
        elif modifiers == wx.MOD_CONTROL and keycode == ord('D'):  # Ctrl+D: delete log
            self.delete_log()
        else:
            event.Skip()  # Ensure other key events are processed


    def doSearchDialog(self):
        # Open a dialog to accept search text.
        dlg = wx.TextEntryDialog(self, "Enter text to search:", "Find")
        if dlg.ShowModal() == wx.ID_OK:
            self.search_text = dlg.GetValue()
            # Start search from current insertion point.
            self.search_pos = self.text2.GetInsertionPoint()
            self.findNext()
        dlg.Destroy()

    def findNext(self):
        if not self.search_text:
            return  # Nothing to search.

        # Get the full text from the TextCtrl.
        full_text = self.text2.GetValue()
        # For a case–insensitive search, convert both full text and search string to lower case.
        lower_text = full_text.lower()
        lower_search = self.search_text.lower()

        # Search from the current position.
        idx = lower_text.find(lower_search, self.search_pos)
        if idx == -1:
            # Optionally, notify the user if the search text is not found:
            wx.MessageBox(f'"{self.search_text}" was not found.', "Find", wx.OK | wx.ICON_INFORMATION)
            # Reset search position for a new search.
            self.search_pos = 0
        else:
            # Set focus to the TextCtrl and highlight the found text.
            self.text2.SetFocus()
            self.text2.ShowPosition(idx)
            self.text2.SetSelection(idx, idx + len(self.search_text))
            # Update the search position for next search.
            self.search_pos = idx + len(self.search_text)

    def on_copy_code(self):
        text = self.text2.GetValue()
        lines = text.splitlines()
        result = []
        in_backticks = False

        for line in lines:
            if line.startswith('```'):
                if in_backticks:
                    break
                else:
                    in_backticks = True
                    continue
            else:
                if in_backticks:
                    result.append(line)  # Collect lines within the back-ticked region

        # Join selected text and put it to the clipboard
        if result:
            clipboard_text = '\n'.join(result)
            self.set_clipboard(clipboard_text)
            wx.MessageBox('Copied to clipboard', "Code")
        else:
            wx.MessageBox('No text found between triple back-ticks.')

    def set_clipboard(self, text):
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(text))
            wx.TheClipboard.Close()

    def reLaunch(self):
        ''' close and re-open this instance '''
        wx.MessageBox('App will now close and re-open...')
        python = sys.executable
        #self.Destroy()
        self.on_close(None)
        os.execl(python, python, *sys.argv)

    def openEditor(self):
        ''' Open text editor to alter options.ini '''
        global opts
        p = subprocess.Popen([opts[5], 'options.ini'])
        p.wait()  # wait until editor closes
        opts = []
        opts = iniproc.read("options.ini", 'model',     # 0
                                           'fontsz1',   # 1
                                           'fontsz2',   # 2
                                           'role',      # 3
                                           'log',       # 4
                                           'editor',    # 5
                                           'font1',     # 6
                                           'font2',     # 7
                                           'height',    # 8
                                           'color')     # 9
        self.reLaunch()


    def on_help_dialog(self):
        msg = '''
        Ctrl-H     This help message\n
        Ctrl-F     Find text\n
        Ctrl-N     Find next\n
        Ctrl-Q     Quit App\n
        Ctrl-G     Execute AI request\n
        Ctrl-O     Open Options\n
        Ctrl-D     Delete Log\n
        Alt-Ctrl-C
                   Copy Code in Markup\n
        '''
        #wx.MessageBox(msg)
        wx.MessageBox(msg, 'Hot Keys' , wx.OK)


class MyApp(wx.App):
    def OnInit(self):
        frame = MyFrame(None)
        self.SetTopWindow(frame)
        return True

if __name__ == '__main__':
    app = MyApp(False)
    app.MainLoop()
