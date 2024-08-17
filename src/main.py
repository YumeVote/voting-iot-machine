from PIL import Image, ImageTk

import tkinter as tk

root = tk.Tk()
root.attributes('-fullscreen', True)

canvas = tk.Canvas(root)
canvas.pack(fill=tk.BOTH, expand=True)

# Get the width and height of the screen
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# Load the GIF animation
gif_image = Image.open("assets/insert_card.gif")
gif_photo = ImageTk.PhotoImage(gif_image)

# Create a label to display the GIF animation
gif_label = canvas.create_image(screen_width / 2, screen_height / 2 + 100, image=gif_photo)

# Function to update the GIF animation frames
def update_gif_frame(frame_index):
    global gif_photo  # Add this line to access the global variable
    # Update the image of the GIF animation
    gif_image.seek(frame_index)
    gif_photo = ImageTk.PhotoImage(gif_image)
    canvas.itemconfig(gif_label, image=gif_photo)
    
    # Schedule the next frame update
    root.after(50, update_gif_frame, (frame_index + 1) % gif_image.n_frames)

# Start the GIF animation
update_gif_frame(0)

canvas.create_text(screen_width / 2, screen_height / 2 - 50, text="Devmatch Government 2024 Election", font=("Helvetica", 32))
canvas.create_text(screen_width / 2, screen_height / 2, text="Please insert your card to vote", font=("Helvetica", 24))
canvas.configure(background='#1c2d5c')

root.mainloop()