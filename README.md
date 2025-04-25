# Credit-Recommendation Chatbot

A conversational assistant that recommends the best U.S. credit card for a user based on credit score, income bracket, and a few preference questions. Built with Rasa 3, Python, and a lightweight eligibility classifier.

## To use the chatbot for yourself, follow these instructions:
### Rasa Chatbot
#### How to Use

### With Docker

```
docker build -t credit-bot .
docker run -p 5005:5005 credit-bot
```
### Local (virutalenv)
1) Make sure Docker Desktop is running and Duckling is up (see command above).
```
docker run -it --rm -p 8000:8000 rasa/duckling
```
3) Launch two shells at project root(can be windows CMD, Ubuntu, etc.)
   

4) Create a new virtual environment using Python 3.9 venv

```
python3 -m venv venv
```

3) Ensure that the virtual environment is activated

```
source venv/bin/activate
```

4) In the terminal run the following command to install the required packages:

```
pip install -r requirements.txt
```

5) Navigate to ./code and run the following command to train the rasa chatbot

```
rasa train
```

6) In the same terminal navigate to ./code/actions and run the following command to start the actions server

```
rasa run actions
```

7) In the other terminal, start the chatbot

```
rasa shell
```

## What to ask? 
Ask things like “Which card fits a 720 score, mid income?”

“I earn $45 k and my credit is 640, what do you recommend?”.

Variations work too; the NLU model handles paraphrases.
