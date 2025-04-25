# Example Inputs for the Credit Card Recommendation Chatbot

This document provides examples of what you can say to the credit card recommendation chatbot at different stages of the conversation.

## 1. Starting the Conversation & Requesting Recommendation

You can start by greeting the bot and asking for a recommendation:

* `Hi`
* `Hello`
* `Can you recommend me a credit card?`
* `I need help finding a credit card.`
* `Suggest some cards for me.`
* `Which cards can I qualify for?`

## 2. Providing Information (During the Form)

The bot will ask you for specific details. Respond with:

* **(Income):**
    * `$90000`
    * `I make $65k a year`
    * `My annual income is 120000`
* **(Credit Score):**
    * `780`
    * `My score is 690`
    * `around 715`
* **(Debt-to-Income Ratio):**
    * `15%`
    * `0.25`
    * `My DTI is 10 percent`
    * `about 30`
* **(Employment Length):**
    * `8 years`
    * `employed for 3`
    * `15 years`
    * `just 1 year`

## 3. Asking Follow-up Questions (After Recommendations)

Once the bot recommends cards (e.g., Card A, Card B, Card C), you can ask follow-up questions.

**Important:** Replace `[Recommended Card Name]` in the examples below with one of the actual card names the bot recommended to you in your session.

### Asking for General Card Details

* `Tell me more about the first one.`
* `What are the details for the second card?`
* `More info on the last recommendation.`
* `Tell me about [Recommended Card Name].` (e.g., `Tell me about the Chase Sapphire Preferred®`)
* `Details on the third option?`
* `What can you tell me about the first?`

### Asking About Specific Card Features

**Using Ordinals (first, second, third, last):**

* `What is the signup bonus for the first one?`
* `Does the second card have foreign transaction fees?`
* `Tell me about the travel insurance on the third recommendation.`
* `What are the rewards details for the first card?`
* `Is there an intro APR for balance transfers on the second one?`
* `What's the annual fee for the last card?`
* `What score do I need for the first card?`
* `Any introductory APR on the second recommendation?`
* `Who issues the third card?`

**Using Card Names:**

* `What is the welcome offer for the [Recommended Card Name]?`
* `Tell me the minimum credit score for the [Recommended Card Name].`
* `Does the [Recommended Card Name] have an intro purchase APR?`
* `Are there any FTFs on the [Recommended Card Name]?`
* `What kind of points system does the [Recommended Card Name] use?`
* `How do I apply for the [Recommended Card Name]?`
* `What about cell phone protection on the [Recommended Card Name]?`
* `What are the rewards for the [Recommended Card Name]?`
* `Interest rate on [Recommended Card Name]?`

### Testing Variations, Typos, and Edge Cases

* `Any bonus on the first card?` (Variation)
* `Interest rate for the second option?` (Variation)
* `Does the last one cost anything per year?` (Variation + Ordinal)
* `Are there international fees on the [Recommended Card Name]?` (Variation)
* `Does it have forigen transaciton fees?` (Typo - tests fuzzy matching/robustness)
* `Tell me the reward details` (Singular - tests fuzzy matching/robustness)
* `What FICO do I need for the first one?` (Variation)
* `What lounge access does the [Recommended Card Name] have?` (Feature likely not present)
* `What's the signup bonus for the Amex Platinum?` (Asking about a potentially unrecommended card)
* `Tell me about the issuer for the second card`

## 4. Ending the Conversation

* `Thanks!`
* `Okay, thank you.`
* `That's all I need.`
* `goodbye`
* `bye`
* `talk soon`