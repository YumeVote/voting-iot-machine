import io
from PIL import Image, ImageTk
from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes

import tkinter as tk
import requests
import os
import urllib.request
import base64
import serial
import threading

load_dotenv()

if not os.path.exists('tempimg'):
    os.makedirs('tempimg')

VOTING_SYSTEM_API_BASE = os.getenv("VOTING_SYSTEM_API_BASE")
VOTING_SYSTEM_CANDIDATE_API = VOTING_SYSTEM_API_BASE + "/candidates"
VOTING_SYSTEM_CANDIDATE_PROFILE_IMAGE_API = VOTING_SYSTEM_API_BASE + "/candidate-image/{}"

candidates = requests.get(VOTING_SYSTEM_CANDIDATE_API).json()
candidate_images = []
for i, candidate in enumerate(candidates):
    with urllib.request.urlopen(VOTING_SYSTEM_CANDIDATE_PROFILE_IMAGE_API.format(candidate[0])) as u:
      raw_data = u.read()
    with open(f"tempimg/{candidate[0]}.jpg", "wb") as f:
        f.write(raw_data)

gif_animation_started = False

current_citizen_hash = None
current_citizen_private_key = None
arduino_serial_input_thread = None

def reset_citizen_data():
    global current_citizen_hash
    global current_citizen_private_key
    current_citizen_hash = None
    current_citizen_private_key = None

def sign_message(message):
    global current_citizen_private_key
    private_key = serialization.load_pem_private_key(
        current_citizen_private_key.encode(),
        password=None,
        backend=default_backend()
    )
    return base64.b64encode(private_key.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )).decode()

def arduino_serial_input(comport, baudrate, votingScreen, invalidCitizenCardScreen, loadingScreen):
    global arduino_serial_input_thread
    def read_serial():
        ser = serial.Serial(comport, baudrate, timeout=0.1)
        while True:
            data = ser.readline().decode().strip()
            if data:
                if data.startswith("ACCESS_DENIED"):
                    print("Access denied")
                    reset_citizen_data()
                    invalidCitizenCardScreen.display()
                elif data.startswith("ACCESS_GRANTED"):
                    print("Access granted")
                    votingScreen.display()
                elif data.startswith("CARD_READING"):
                    loadingScreen.display("Please wait...Your card is being read")

    arduino_serial_input_thread = threading.Thread(target=read_serial)
    arduino_serial_input_thread.start()

class App(tk.Tk):
    screens = []

    def __init__(self):
        tk.Tk.__init__(self)
        self._frame = None
        self.attributes('-fullscreen', True)
    
    def add_to_list(self, new_screen):
        self.screens.append(new_screen)
    
    def close_all_screens(self):
        for screen in self.screens:
            screen.pack_forget()

class Screen(tk.Canvas):
    def __init__(self, master):
        tk.Canvas.__init__(self, master)
        self.master = master
        self.master.add_to_list(self)
    
    def display(self):
        pass

class WelcomeScreen(Screen):
    def __init__(self, master):
        Screen.__init__(self, master)
    
    def display(self):
        self.master.close_all_screens()
        self.pack(fill=tk.BOTH, expand=True)

        # Get the width and height of the screen
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()

        # Load the GIF animation
        gif_image = Image.open("assets/insert_card.gif")
        gif_photo = ImageTk.PhotoImage(gif_image)

        # Create a label to display the GIF animation
        gif_label = self.create_image(screen_width / 2, screen_height / 2 + 100, image=gif_photo)

        # Function to update the GIF animation frames
        def update_gif_frame(frame_index):
            global gif_photo  # Add this line to access the global variable
            # Update the image of the GIF animation
            gif_image.seek(frame_index)
            gif_photo = ImageTk.PhotoImage(gif_image)
            self.itemconfig(gif_label, image=gif_photo)
            
            # Schedule the next frame update
            self.master.after(50, update_gif_frame, (frame_index + 1) % gif_image.n_frames)

        # Start the GIF animation
        global gif_animation_started
        if not gif_animation_started:
            gif_animation_started = True
            update_gif_frame(0)

        self.create_text(screen_width / 2, screen_height / 2 - 50, text="Devmatch Government 2024 Election", font=("Helvetica", 32))
        self.create_text(screen_width / 2, screen_height / 2, text="Please insert your card to vote", font=("Helvetica", 24))
        self.configure(background='#1c2d5c')

class LoadingScreen(Screen):
    def __init__(self, master):
        Screen.__init__(self, master)
    
    def display(self, text):
        self.master.close_all_screens()
        self.pack(fill=tk.BOTH, expand=True)

        # Get the width and height of the screen
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        
        self.create_text(screen_width / 2, screen_height / 2, text=text, font=("Helvetica", 24))
        self.configure(background='#1c2d5c')

class InvalidCitizenCardScreen(Screen):
    def __init__(self, master, onQuitButtonClicked):
        Screen.__init__(self, master)
        self.onQuitButtonClicked = onQuitButtonClicked
    
    def display(self):
        self.master.close_all_screens()
        self.pack(fill=tk.BOTH, expand=True)

        # Get the width and height of the screen
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()

        self.create_text(screen_width / 2, screen_height / 2, text="The IC card that you have inserted is invalid", font=("Helvetica", 32))

        quitButton = tk.Button(self, text="Quit", font=("Helvetica", 32), command=lambda: self.onQuitButtonClicked())
        self.create_window(screen_width / 2, screen_height / 2 + 170, window=quitButton)

        self.configure(background='#1c2d5c')

class VotingScreen(Screen):
    def __init__(self, master):
        Screen.__init__(self, master)
    
    def vote(self, candidate_id):
        # Generate a private key
        voteDigitalSignature = sign_message(candidates[candidate_id - 1][1].encode())
        identitySignature = sign_message(current_citizen_hash.encode())
        storedIdentitySignature = sign_message(b"Devmatch")
        vote_response = requests.post(VOTING_SYSTEM_API_BASE + "/vote", params={
            "candidate_id": candidate_id,
            "vote": candidates[candidate_id - 1][1],
            "voteDigitalSignature": voteDigitalSignature,
            "identitySignature": identitySignature,
            "storedIdentitySignature": storedIdentitySignature
        })

    def display(self):
        self.master.close_all_screens()
        self.pack(fill=tk.BOTH, expand=True)

        # Get the width and height of the screen
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()

        self.create_text(screen_width / 2, 200, text="Please cast your vote to a candidate", font=("Helvetica", 32))
        spacing = 50

        for i, candidate in enumerate(candidates):
            global candidate_images
            candidate_id = candidate[0]

            candidate_profile_image = Image.open("tempimg/" + str(candidate_id) + ".jpg")
            candidate_profile_photo = ImageTk.PhotoImage(candidate_profile_image.resize((300, 300)))
            candidate_images.append(candidate_profile_photo)

        # Calculate the total width of all candidate images
        total_width = len(candidates) * 300 + (len(candidates) - 1) * spacing

        # Calculate the starting x position to center the images
        start_x = (screen_width - total_width) / 2 + 150

        for i, candidate_image in enumerate(candidate_images):
            x = start_x + (i * (300 + spacing))
            y = screen_height / 2

            self.create_image(x, y, image=candidate_image)
            self.create_text(x, y + 200, text=candidates[i][1], font=("Helvetica", 24))
            
            def vote_for_this_candidate(candidate_id=candidates[i][0]):
                self.vote(candidate_id)

            voteButton = tk.Button(self, text="Vote", font=("Helvetica", 18), command=lambda candidate_id=candidates[i][0]: vote_for_this_candidate(candidate_id))
            self.create_window(x, screen_height / 2 + 250, window=voteButton)
        self.configure(background='#1c2d5c')

class ResultsScreen(Screen):
    def __init__(self, master, onQuitButtonClicked):
        Screen.__init__(self, master)
        self.app = master
        self.onQuitButtonClicked = onQuitButtonClicked
    
    def display(self):
        self.app.close_all_screens()
        self.pack(fill=tk.BOTH, expand=True)

        # Get the width and height of the screen
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()

        self.create_text(screen_width / 2, screen_height/2 - 200, text="Thank you for your vote!", font=("Helvetica", 32))
        self.create_text(screen_width / 2, screen_height/2 - 150, text="For future reference, your vote id is displayed below (which can be used on the main website for verification)", font=("Helvetica", 24))
        self.create_text(screen_width / 2, screen_height/2, text="1234567890", font=("Helvetica", 64))
        
        quitButton = tk.Button(self, text="Quit", font=("Helvetica", 32), command=lambda: self.onQuitButtonClicked())
        self.create_window(screen_width / 2, screen_height / 2 + 170, window=quitButton)

        self.configure(background='#1c2d5c')

app = App()
welcomeScreen = WelcomeScreen(app)
invalidCitizenCardScreen = InvalidCitizenCardScreen(app, onQuitButtonClicked=lambda: welcomeScreen.display() and reset_citizen_data())
votingScreen = VotingScreen(app)
resultsScreen = ResultsScreen(app, onQuitButtonClicked=lambda: welcomeScreen.display() and reset_citizen_data())
loadingScreen = LoadingScreen(app)

welcomeScreen.display()
#votingScreen.display()
#resultsScreen.display()

arduino_serial_input('/dev/cu.usbserial-FTB6SPL3', 9600, votingScreen, invalidCitizenCardScreen, loadingScreen)

def onQuit():
    global arduino_serial_input_thread
    arduino_serial_input_thread.join()
    app.quit()

app.protocol("WM_DELETE_WINDOW", onQuit)
app.mainloop()