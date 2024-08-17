import tkinter as tk
root = tk.Tk()
root.attributes('-fullscreen', True)

a = tk.Label(root, text="Hello World")
a.pack(anchor=tk.CENTER)
a.pack()
root.mainloop()