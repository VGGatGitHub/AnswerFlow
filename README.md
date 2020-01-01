## Overview

AnswerFlow is a deep learning chatbot that learns from question-answer pairs.
We used data from Google's Natural Questions posted on the web.  
https://ai.google.com/research/NaturalQuestions/download

From the data we only use questions and short answers such as these for training the chatbot.

question: what is the orange stuff on my sushi  
answer: tobiko

question: who spread the theory that one is a product of the mind and body  
answer: rene descartes

question: when did star trek the next generation first air  
answer: september 28 , 1987

The training data is in English but the chatbot can work with other languages by feeding it question-answer pairs in another language. The model does not need to know word meanings or use linguistic features like word stems, parts-of-speech, or stop words.