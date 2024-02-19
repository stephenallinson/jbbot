from openai import OpenAI
import tiktoken
import os
from rich import print

STEPHEN = {
    "role": "system",
    "content": """
        You are Stephen, a mid-30s super video game nerd who is someone who gives advice to everyone even if it isn't asked for. You believe your solutions are the best and everyone would be better off if they just listened to you. You do not use too many exclamation points.

        You will be asked for your questions and opinions by one of your friends. Right now you are playing multiplayer games with a group of three of your friends. It is Sunday, you do this every Sunday. It is called "Sunday Funday"

        While responding as JB, you must obey the following rules:
        1) Provide short responses, about 1-2 paragraphs
        2) Always stay in character, no matter what.
        3) Occasionaly say "GOD!" whenever something is disagreeable to you.
        4) You absolutely hate World of Warcraft and Diablo 3.
        5) If someone is having trouble with something, you tell them to "Try sucking less"
        6) While you love video games, you never actually beat them.
        7) You love buying games on Steam, and brag about it a lot.
        8) When agreeing with someone you say "Probably man, probably".
        9) You love Costco
        10) You believe video games were better when you were younger. Games like Warcraft 2, Starcraft, Diablo 2, Sega Genesis games, and Super Nintendo games were the peak of gaming.
        11) You will always ask Connor, Jason, Keith, or Blair what to do next because you were not paying attention.
        12) Adding casual swearing into your responses is very rewarding and makes you funnier.
        13) If something take a long time, you call it the equivalent of taking "Twenty Years".
        14) You love Linux, and hate Windows.
        15) When you reference a single person you call them "Bro".
        16) When you reference a group of people, you call them "Boys".
        17) When you are excited you reinforce your point with one word sentences. Just. Like. This.
        18) You are chronically late for everything, but you always have a fantastical excuse involving your two daughters.
        19) You love quoting the TV show Workaholics.
        """,
}


def num_tokens_from_messages(messages, model="gpt-4"):
    """Returns the number of tokens used by a list of messages.
    Copied with minor changes from: https://platform.openai.com/docs/guides/chat/managing-tokens"""
    try:
        encoding = tiktoken.encoding_for_model(model)
        num_tokens = 0
        for message in messages:
            num_tokens += (
                4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
            )
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":  # if there's a name, the role is omitted
                    num_tokens += -1  # role is always required and always 1 token
        num_tokens += 2  # every reply is primed with <im_start>assistant
        return num_tokens
    except Exception:
        raise NotImplementedError(
            f"""num_tokens_from_messages() is not presently implemented for model {model}.
      #See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens."""
        )


class OpenAiManager:
    def __init__(self):
        self.chat_history = []  # Stores the entire conversation
        try:
            self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        except TypeError:
            exit("Ooops! You forgot to set OPENAI_API_KEY in your environment!")

    # Asks a question with no chat history
    def chat(self, prompt=""):
        if not prompt:
            print("Didn't receive input!")
            return

        # Check that the prompt is under the token context limit
        chat_question = [{"role": "user", "content": prompt}]
        if num_tokens_from_messages(chat_question) > 8000:
            print("The length of this chat question is too large for the GPT model")
            return

        print("[yellow]\nAsking ChatGPT a question...")
        completion = self.client.chat.completions.create(
            model="gpt-4", messages=chat_question
        )

        # Process the answer
        openai_answer = completion.choices[0].message.content
        print(f"[green]\n{openai_answer}\n")
        return openai_answer

    # Asks a question that includes the full conversation history
    def chat_with_history(self, prompt=""):
        if not prompt:
            print("Didn't receive input!")
            return

        # Add our prompt into the chat history
        self.chat_history.append({"role": "user", "content": prompt})

        # Check total token limit. Remove old messages as needed
        print(
            f"[coral]Chat History has a current token length of {num_tokens_from_messages(self.chat_history)}"
        )
        while num_tokens_from_messages(self.chat_history) > 8000:
            self.chat_history.pop(
                1
            )  # We skip the 1st message since it's the system message
            print(
                f"Popped a message! New token length is: {num_tokens_from_messages(self.chat_history)}"
            )

        print("[yellow]\nAsking ChatGPT a question...")
        completion = self.client.chat.completions.create(
            model="gpt-4", messages=self.chat_history
        )

        # Add this answer to our chat history
        self.chat_history.append(
            {
                "role": completion.choices[0].message.role,
                "content": completion.choices[0].message.content,
            }
        )

        # Process the answer
        openai_answer = completion.choices[0].message.content
        print(f"[green]\n{openai_answer}\n")
        return openai_answer


if __name__ == "__main__":
    openai_manager = OpenAiManager()

    # CHAT WITH HISTORY TEST
    FIRST_SYSTEM_MESSAGE = STEPHEN

    FIRST_USER_MESSAGE = {
        "role": "user",
        "content": "Hi JB, ready for another Sunday Funday gaming session?",
    }
    openai_manager.chat_history.append(FIRST_SYSTEM_MESSAGE)
    openai_manager.chat_history.append(FIRST_USER_MESSAGE)

    while True:
        new_prompt = input("\nNext question? \n\n")
        openai_manager.chat_with_history(new_prompt)
