import random

def main():
    secret = random.randint(1, 100)
    guesses = 0

    print("I'm thinking of a number between 1 and 100.")

    while True:
        try:
            guess = int(input("Your guess: "))
        except ValueError:
            print("Please enter a valid number.")
            continue

        guesses += 1

        if guess < secret:
            print("Too low!")
        elif guess > secret:
            print("Too high!")
        else:
            print(f"Correct! You got it in {guesses} guesses.")
            break

if __name__ == "__main__":
    main()
