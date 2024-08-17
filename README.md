# Voting IOT Machine UI

## Target Requirements

1. A voting DRE IoT machine made with Arduino that reads the private key and the hash from a RFID National Card (emulated), and interacts with the voting service api. The DRE Machine should be able to read the RFID Card, show a list of candidates they can vote, sign the digital signature, and send the data to the voting service api. If the api mentioned the vote is invalid because the identity and digital signature can be verified, then this citizen is using a fake id. If the vote is valid, a Vote ID will be returned by the Voting Service API.

## Solutions

1. An emulated User Interface that acts as the GUI of the POS machine which displays:
    - A Welcome Screen
      <img width="1440" alt="image" src="https://github.com/user-attachments/assets/7c35a203-137b-4f88-9b1d-5bcb2dfd1686">

    - Loading Screen
    - Error Screen
    - Candidate Choosing Screen
      <img width="1440" alt="image" src="https://github.com/user-attachments/assets/88365672-d15a-40c9-8f55-e4c903ceb015">

    - Receipt Screen

## How To Run

```
make
```

By running the command above, the required python libraries will be installed and the application will launch by itself

## Limitation

1. Right now, due to poor thread management, the application does not close when the close button is clicked
2. No sophiscated system is implemented here, and the security could be flawed
