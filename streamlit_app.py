import streamlit as st
import streamlit.components.v1 as components
import random
import json
import io
import re
import html
import textwrap
import requests
import plotly.graph_objects as go
from PIL import Image, ImageDraw, ImageFont

st.set_page_config(page_title="Fantasy Quiz", page_icon="🔮", layout="centered")

# ============================================================
# DATA — HOGWARTS HOUSES
# (fondatore, animale, elemento, colori, fantasma, sala comune,
#  values, notable alumni: factual details of the Harry
#  Potter universe, not text protected by the books)
# ============================================================
HOUSES = {
    "Gryffindor": {
        "gradiente": "linear-gradient(135deg, #740001 0%, #ae0001 45%, #d3a625 100%)",
        "rgb_top": (116, 0, 1),
        "rgb_bottom": (211, 166, 37),
        "emoji": "🦁",
        "descrizione": "Courage runs through your veins. You're not fearless — no true Gryffindor is — but you act even when you're afraid, and that's exactly what defines you.",
        "dettagli": [
            ("Founder", "Godric Gryffindor"),
            ("Animal", "Lion"),
            ("Element", "Fire"),
            ("Colors", "Scarlet and gold"),
            ("Ghost", "Nearly Headless Nick"),
            ("Common room", "Seventh floor, behind the Fat Lady"),
            ("Values", "Courage, boldness, determination"),
            ("Notable alumni", "Harry Potter, Hermione Granger, Albus Dumbledore"),
        ],
    },
    "Slytherin": {
        "gradiente": "linear-gradient(135deg, #0d1f13 0%, #1a472a 50%, #3c6e47 100%)",
        "rgb_top": (13, 31, 19),
        "rgb_bottom": (60, 110, 71),
        "emoji": "🐍",
        "descrizione": "You know exactly what you want and how to get it. Your strategic mind and ambition always push you one step further than everyone else.",
        "dettagli": [
            ("Founder", "Salazar Slytherin"),
            ("Animal", "Snake"),
            ("Element", "Water"),
            ("Colors", "Emerald green and silver"),
            ("Ghost", "The Bloody Baron"),
            ("Common room", "Dungeons, overlooking the lake"),
            ("Values", "Ambition, cunning, leadership"),
            ("Notable alumni", "Severus Snape, Tom Riddle, Horace Slughorn"),
        ],
    },
    "Ravenclaw": {
        "gradiente": "linear-gradient(135deg, #060d24 0%, #0e1a40 50%, #2b4a8c 100%)",
        "rgb_top": (6, 13, 36),
        "rgb_bottom": (43, 74, 140),
        "emoji": "🦅",
        "descrizione": "Your mind never stops. Curiosity and wit guide you, and for you, knowledge isn't a duty but one of life's greatest joys.",
        "dettagli": [
            ("Founder", "Rowena Ravenclaw"),
            ("Animal", "Eagle"),
            ("Element", "Air"),
            ("Colors", "Midnight blue and bronze"),
            ("Ghost", "The Grey Lady"),
            ("Common room", "A tower, entered by solving a riddle"),
            ("Values", "Intelligence, creativity, curiosity"),
            ("Notable alumni", "Luna Lovegood, Gilderoy Lockhart, Filius Flitwick"),
        ],
    },
    "Hufflepuff": {
        "gradiente": "linear-gradient(135deg, #4a3b00 0%, #b89b1a 50%, #ffdb00 100%)",
        "rgb_top": (74, 59, 0),
        "rgb_bottom": (255, 219, 0),
        "emoji": "🦡",
        "descrizione": "You don't seek the spotlight, but no group would hold together without you. Loyal to the core, you work hard and treat everyone with the same honest kindness.",
        "dettagli": [
            ("Founder", "Helga Hufflepuff"),
            ("Animal", "Badger"),
            ("Element", "Earth"),
            ("Colors", "Canary yellow and black"),
            ("Ghost", "The Fat Friar"),
            ("Common room", "Basement near the kitchens"),
            ("Values", "Loyalty, hard work, patience"),
            ("Notable alumni", "Cedric Diggory, Newt Scamander, Pomona Sprout"),
        ],
    },
}

QUESTIONS_HP = [
    {
        "domanda": "You're in the Forbidden Forest at night and hear a branch snap behind you. What do you really do, on instinct?",
        "opzioni": [
            ("I spin around at once, wand ready: if there's danger, better to face it head-on", {"Gryffindor": 1}),
            ("I freeze and silently work out what creature it might be, based on the sounds", {"Ravenclaw": 1}),
            ("I weigh whether it's better to flee or whether I can turn the situation to my advantage", {"Slytherin": 1}),
            ("I look for my companions to make sure everyone's okay before moving", {"Hufflepuff": 1}),
        ],
    },
    {
        "domanda": "The Sorting Hat points out you could thrive in more than one house. How do you respond?",
        "opzioni": [
            ("I ask to be placed where I can show the most courage", {"Gryffindor": 1}),
            ("I ask where I'll be able to learn the most and develop my ideas", {"Ravenclaw": 1}),
            ("I ask where I can build the most solid path for my future", {"Slytherin": 1}),
            ("I ask where I'll find the most sincere, lasting friendships", {"Hufflepuff": 1}),
        ],
    },
    {
        "domanda": "You have to choose an elective for your third year. Which do you pick?",
        "opzioni": [
            ("Care of Magical Creatures: I like the risk and the hands-on contact", {"Gryffindor": 1, "Hufflepuff": 0.5}),
            ("Arithmancy: I love complex systems and logic", {"Ravenclaw": 1}),
            ("Divination: it might give me an edge others don't have", {"Slytherin": 0.5, "Ravenclaw": 0.5}),
            ("Care of Magical Creatures, but simply for the joy of looking after them", {"Hufflepuff": 1}),
        ],
    },
    {
        "domanda": "A classmate is being mocked in front of everyone. What do you do?",
        "opzioni": [
            ("I step in right away, openly, whatever it costs", {"Gryffindor": 1}),
            ("I wait for the right moment to point out, with solid arguments, how unfair it was", {"Ravenclaw": 1}),
            ("I weigh the situation: does stepping in now help me, or just expose me needlessly?", {"Slytherin": 1}),
            ("I go straight to them afterward, privately, so they know they're not alone", {"Hufflepuff": 1}),
        ],
    },
    {
        "domanda": "Honestly, what's your deepest fear?",
        "opzioni": [
            ("Being remembered as a coward", {"Gryffindor": 1}),
            ("Being trapped in mediocrity, never realizing my potential", {"Slytherin": 1}),
            ("Discovering I got something wrong out of ignorance, not bad luck", {"Ravenclaw": 1}),
            ("Disappointing or losing the people I trust most", {"Hufflepuff": 1}),
        ],
    },
    {
        "domanda": "You've stumbled on a very powerful magical object of dubious origin. What do you do?",
        "opzioni": [
            ("I use it right away if it helps protect someone, without thinking twice", {"Gryffindor": 1}),
            ("I study it thoroughly before deciding anything: understanding comes before acting", {"Ravenclaw": 1}),
            ("I consider how it could be useful to me, with due caution", {"Slytherin": 1}),
            ("I hand it over to a teacher I trust: it's not right to keep it for myself", {"Hufflepuff": 1}),
        ],
    },
    {
        "domanda": "How do you prefer to work on a group project for a difficult subject?",
        "opzioni": [
            ("I volunteer for the riskiest or most demanding part", {"Gryffindor": 1}),
            ("I put together a detailed plan and make sure everything goes as intended", {"Slytherin": 1}),
            ("I bring the most original ideas and the least obvious solutions", {"Ravenclaw": 1}),
            ("I make sure the work is shared fairly and no one gets left behind", {"Hufflepuff": 1}),
        ],
    },
    {
        "domanda": "You're standing before a mirror that shows your deepest desire. What do you most likely see?",
        "opzioni": [
            ("A moment where I save someone I care about", {"Gryffindor": 1}),
            ("A future where I'm respected and have achieved everything I wanted", {"Slytherin": 1}),
            ("The answer to a question that's always haunted me", {"Ravenclaw": 1}),
            ("My family and friends, all together and happy", {"Hufflepuff": 1}),
        ],
    },
    {
        "domanda": "A teacher offers you two paths for an exam: a safe but ordinary one, or a risky but memorable one. Which do you choose?",
        "opzioni": [
            ("The risky one: if it goes wrong, at least I'll have given it everything", {"Gryffindor": 1}),
            ("The risky one, but only after precisely calculating my odds of success", {"Ravenclaw": 0.5, "Slytherin": 0.5}),
            ("Whichever one gets me the best result in the long run", {"Slytherin": 1}),
            ("The safe one: I'd rather have a solid guaranteed result than a pointless gamble", {"Hufflepuff": 1}),
        ],
    },
    {
        "domanda": "What bothers you most in someone you work with?",
        "opzioni": [
            ("Indecision: people afraid to act drive me crazy", {"Gryffindor": 1}),
            ("Dishonesty or disloyalty to the group", {"Hufflepuff": 1}),
            ("Superficiality: people who never dig deeper into anything", {"Ravenclaw": 1}),
            ("Incompetence: people who aren't up to their own goals", {"Slytherin": 1}),
        ],
    },
    {
        "domanda": "If you could receive just one gift from a Hogwarts professor, which would you choose?",
        "opzioni": [
            ("The courage to never waver in the face of danger", {"Gryffindor": 1}),
            ("An endless library holding all the knowledge of the magical world", {"Ravenclaw": 1}),
            ("The power to achieve any goal I set for myself", {"Slytherin": 1}),
            ("Loyal friends for life", {"Hufflepuff": 1}),
        ],
    },
    {
        "domanda": "It's the last night before a big, risky event (a tournament, a mission, a decisive exam). How do you spend it?",
        "opzioni": [
            ("I can't sit still: I just want the moment to act to arrive", {"Gryffindor": 1}),
            ("I go over every single detail, again and again, until I'm sure I'm ready", {"Ravenclaw": 1}),
            ("I polish my strategy, thinking through every possible twist and how to use it to my advantage", {"Slytherin": 1}),
            ("I stay with the people I love: they give me the strength for the day ahead", {"Hufflepuff": 1}),
        ],
    },
]


# ============================================================
# DATA — GODLY PARENTS (Percy Jackson / Camp Half-Blood)
# (domain, symbol animal, colors, cabin, notable children, values:
#  factual details of the universe/mythology, not protected text)
# ============================================================
GODS = {
    "Zeus": {
        "gradiente": "linear-gradient(135deg, #1b2f4d 0%, #3a5f8a 50%, #a9c9e8 100%)",
        "rgb_top": (27, 47, 77),
        "rgb_bottom": (169, 201, 232),
        "emoji": "⚡",
        "descrizione": "Born to lead. You have an innate sense of authority and justice, even if your pride sometimes plays tricks on you.",
        "dettagli": [
            ("Domain", "Sky and lightning"),
            ("Symbol animal", "Eagle"),
            ("Colors", "Electric blue and silver"),
            ("Cabin", "Cabin 1"),
            ("Notable children", "Jason Grace, Thalia Grace"),
            ("Values", "Leadership, authority, pride"),
        ],
    },
    "Poseidon": {
        "gradiente": "linear-gradient(135deg, #04303a 0%, #0f6e7d 50%, #2ea3b8 100%)",
        "rgb_top": (4, 48, 58),
        "rgb_bottom": (46, 163, 184),
        "emoji": "🌊",
        "descrizione": "Your heart is as unpredictable as the sea: calm on the surface, capable of furious storms when someone you love is threatened.",
        "dettagli": [
            ("Domain", "Sea and earthquakes"),
            ("Symbol animal", "Horse"),
            ("Colors", "Aqua green and ocean blue"),
            ("Cabin", "Cabin 3"),
            ("Notable children", "Percy Jackson, Tyson"),
            ("Values", "Loyalty, instinct, protection"),
        ],
    },
    "Hades": {
        "gradiente": "linear-gradient(135deg, #0a0a0a 0%, #3b2f10 55%, #5a4a14 100%)",
        "rgb_top": (10, 10, 10),
        "rgb_bottom": (90, 74, 20),
        "emoji": "💀",
        "descrizione": "You prefer the shadows to the spotlight. Beneath your apparent coldness hides a very strong sense of duty.",
        "dettagli": [
            ("Domain", "Realm of the dead and underground riches"),
            ("Symbol animal", "Hellhound"),
            ("Colors", "Black and deep gold"),
            ("Cabin", "No official cabin, due to an ancient pact"),
            ("Notable children", "Nico di Angelo, Hazel Levesque"),
            ("Values", "Sense of duty, solitude, rigor"),
        ],
    },
    "Athena": {
        "gradiente": "linear-gradient(135deg, #23232b 0%, #55555f 50%, #8c7850 100%)",
        "rgb_top": (35, 35, 43),
        "rgb_bottom": (140, 120, 80),
        "emoji": "🦉",
        "descrizione": "Your mind is your most powerful weapon. You plan, you observe, and rarely does anyone manage to surprise you.",
        "dettagli": [
            ("Domain", "Wisdom and battle strategy"),
            ("Symbol animal", "Owl"),
            ("Colors", "Grey and bronze"),
            ("Cabin", "Cabin 6"),
            ("Notable children", "Annabeth Chase, Malcolm Pace"),
            ("Values", "Intelligence, planning, pride"),
        ],
    },
    "Ares": {
        "gradiente": "linear-gradient(135deg, #280404 0%, #6e0f0f 50%, #961414 100%)",
        "rgb_top": (40, 4, 4),
        "rgb_bottom": (150, 20, 20),
        "emoji": "🗡️",
        "descrizione": "You live for action and challenge. Your courage in battle is undeniable, even if you sometimes act before thinking.",
        "dettagli": [
            ("Domain", "War and violence"),
            ("Symbol animal", "Boar"),
            ("Colors", "Blood red and black"),
            ("Cabin", "Cabin 5"),
            ("Notable children", "Clarisse La Rue"),
            ("Values", "Strength, courage, group loyalty"),
        ],
    },
    "Apollo": {
        "gradiente": "linear-gradient(135deg, #785a0a 0%, #c99b1f 50%, #ffddaa 100%)",
        "rgb_top": (120, 90, 10),
        "rgb_bottom": (255, 221, 170),
        "emoji": "🎵",
        "descrizione": "You bring light wherever you go, with creativity, optimism, and a strong urge to take care of others.",
        "dettagli": [
            ("Domain", "Sun, music, prophecy, and healing"),
            ("Symbol animal", "Swan"),
            ("Colors", "Gold and white"),
            ("Cabin", "Cabin 7"),
            ("Notable children", "Will Solace, Austin Lake"),
            ("Values", "Creativity, optimism, empathy"),
        ],
    },
    "Aphrodite": {
        "gradiente": "linear-gradient(135deg, #5a1e32 0%, #a8496b 50%, #e696b4 100%)",
        "rgb_top": (90, 30, 50),
        "rgb_bottom": (230, 150, 180),
        "emoji": "💗",
        "descrizione": "Your power is your heart. You feel everything intensely, and that makes you braver than you think.",
        "dettagli": [
            ("Domain", "Love and beauty"),
            ("Symbol animal", "Dove"),
            ("Colors", "Powder pink and rose gold"),
            ("Cabin", "Cabin 10"),
            ("Notable children", "Piper McLean, Silena Beauregard"),
            ("Values", "Empathy, charm, authenticity"),
        ],
    },
    "Hermes": {
        "gradiente": "linear-gradient(135deg, #3c2d0a 0%, #7a5c1a 50%, #c89a3c 100%)",
        "rgb_top": (60, 45, 10),
        "rgb_bottom": (200, 154, 60),
        "emoji": "🪽",
        "descrizione": "You're built for movement and the unexpected. Wit, humor, and a touch of healthy rebellion define you.",
        "dettagli": [
            ("Domain", "Travel, trade, and messengers"),
            ("Symbol animal", "Hawk"),
            ("Colors", "Mustard yellow and leather brown"),
            ("Cabin", "Cabin 11"),
            ("Notable children", "Luke Castellan, Travis and Connor Stoll"),
            ("Values", "Wit, adaptability, freedom"),
        ],
    },
    "Hephaestus": {
        "gradiente": "linear-gradient(135deg, #281406 0%, #6e3a12 50%, #c8782e 100%)",
        "rgb_top": (40, 20, 6),
        "rgb_bottom": (200, 120, 46),
        "emoji": "🔨",
        "descrizione": "Your hands speak louder than your voice. You build, repair, invent: your practical genius is your most authentic form of expression, even if few notice it right away.",
        "dettagli": [
            ("Domain", "Blacksmiths, fire, and mechanical creations"),
            ("Symbol animal", "Donkey"),
            ("Colors", "Bronze and fire red"),
            ("Cabin", "Cabin 9"),
            ("Notable children", "Leo Valdez, Charles Beckendorf"),
            ("Values", "Practical ingenuity, patience, perseverance"),
        ],
    },
}

QUESTIONS_PJ = [
    {
        "domanda": "You're leading an important mission and the group is waiting for your order. What do you do?",
        "opzioni": [
            ("I give the order firmly: the team needs clear guidance", {"Zeus": 1}),
            ("I listen to everyone, but once I decide, nothing changes my mind", {"Poseidon": 1}),
            ("I prefer to hang back and act only when it's truly necessary", {"Hades": 1}),
            ("I weigh every possible scenario before giving any instruction", {"Athena": 1}),
        ],
    },
    {
        "domanda": "How do you prefer to spend a free afternoon at camp?",
        "opzioni": [
            ("In the arena, training with a sword until I'm exhausted", {"Ares": 1}),
            ("Writing music or singing with friends", {"Apollo": 1}),
            ("Spending quality time with people I care about", {"Aphrodite": 1}),
            ("Exploring around, maybe cooking up some harmless prank", {"Hermes": 1}),
            ("In the workshop, building or fixing something with my hands", {"Hephaestus": 1}),
        ],
    },
    {
        "domanda": "The group is split on how to face an imminent danger. What do you do?",
        "opzioni": [
            ("I make the final call myself: someone has to", {"Zeus": 1}),
            ("I follow my gut, even if it goes against the majority", {"Poseidon": 1}),
            ("I propose facing it head-on, with force", {"Ares": 1}),
            ("I try to calm everyone down and find a middle ground", {"Apollo": 1}),
        ],
    },
    {
        "domanda": "What makes you feel truly yourself?",
        "opzioni": [
            ("A moment of silence and solitude, far from the noise", {"Hades": 1}),
            ("Solving a complex problem better than anyone else", {"Athena": 1}),
            ("A genuine, deep connection with someone", {"Aphrodite": 1}),
            ("The freedom to go wherever I want, with no strings attached", {"Hermes": 1}),
            ("Building something with my own hands, from start to finish", {"Hephaestus": 1}),
        ],
    },
    {
        "domanda": "Honestly, what's your weak point?",
        "opzioni": [
            ("Pride: I struggle to admit when I'm wrong", {"Zeus": 1}),
            ("The tendency to isolate myself when things get complicated", {"Hades": 1}),
            ("My temper: I act before thinking about the consequences", {"Ares": 1}),
            ("I let my emotions guide me too much, sometimes", {"Aphrodite": 1}),
        ],
    },
    {
        "domanda": "A friend asks you for important advice. How do you respond?",
        "opzioni": [
            ("I tell them what I feel, sincerely and on instinct", {"Poseidon": 1}),
            ("I break down the situation with them, point by point", {"Athena": 1}),
            ("I try to be supportive and reassuring", {"Apollo": 1}),
            ("I suggest a creative alternative they might not have thought of", {"Hermes": 1}),
            ("I build or fix something concrete for them that could really help", {"Hephaestus": 1}),
        ],
    },
    {
        "domanda": "For you, what's the true definition of strength?",
        "opzioni": [
            ("The power to enforce rules and order", {"Zeus": 1}),
            ("The ability to out-plan your opponent", {"Athena": 1}),
            ("Physical courage and determination in battle", {"Ares": 1}),
            ("The wit that gets you out of any situation", {"Hermes": 1}),
        ],
    },
    {
        "domanda": "How do you react when someone you love is in danger?",
        "opzioni": [
            ("I unleash everything I have to protect them, without a second thought", {"Poseidon": 1}),
            ("I turn cold and calculating: no panic, just action", {"Hades": 1}),
            ("My first instinct is to heal or ease their suffering", {"Apollo": 1}),
            ("My heart shatters, but I find the strength for them", {"Aphrodite": 1}),
            ("I quietly build something that could really protect them", {"Hephaestus": 1}),
        ],
    },
    {
        "domanda": "If you could have just one divine power, which would you choose?",
        "opzioni": [
            ("Commanding lightning and the sky", {"Zeus": 1}),
            ("Controlling the waters and storm-tossed seas", {"Poseidon": 1}),
            ("Knowing every strategy and secret in the world", {"Athena": 1}),
            ("The charm to win over anyone's heart", {"Aphrodite": 1}),
        ],
    },
    {
        "domanda": "What's your favorite place to think?",
        "opzioni": [
            ("A quiet, secluded place, far from everyone", {"Hades": 1}),
            ("In the gym, working it out through training", {"Ares": 1}),
            ("Outdoors, under the sun", {"Apollo": 1}),
            ("On the road, wherever my feet take me", {"Hermes": 1}),
            ("In a workshop, working with my hands while I think", {"Hephaestus": 1}),
        ],
    },
    {
        "domanda": "What bothers you most in other people?",
        "opzioni": [
            ("A lack of respect for authority or rules", {"Zeus": 1}),
            ("Superficiality and mental laziness", {"Athena": 1}),
            ("Coldness and a lack of empathy", {"Apollo": 1}),
            ("Dishonesty about one's feelings", {"Aphrodite": 1}),
        ],
    },
    {
        "domanda": "It's the last night before a dangerous mission. How do you spend it?",
        "opzioni": [
            ("Near the water, to calm down and think", {"Poseidon": 1}),
            ("In silence, going over every possible scenario alone", {"Hades": 1}),
            ("Still training right up to the last minute", {"Ares": 1}),
            ("Joking around with friends to ease the tension", {"Hermes": 1}),
            ("Checking and fixing every piece of my gear", {"Hephaestus": 1}),
        ],
    },
]


# ============================================================
# DATA — DIVERGENT FACTIONS
# (headquarters, symbol, colors, values, notable characters: factual
#  factual details of the novel's universe, not protected text)
# ============================================================
DIVERGENT = {
    "Abnegation": {
        "gradiente": "linear-gradient(135deg, #3c3c40 0%, #6b6b70 50%, #aaaaad 100%)",
        "rgb_top": (60, 60, 64),
        "rgb_bottom": (170, 170, 173),
        "emoji": "🤲",
        "descrizione": "You easily forget yourself to put others first. Quiet service, to you, is worth more than any recognition.",
        "dettagli": [
            ("Headquarters", "Neighborhood near the Fence"),
            ("Symbol", "Cupped hands"),
            ("Colors", "Grey"),
            ("Values", "Selflessness, humility, service"),
            ("Notable characters", "Tris Prior (by birth), Andrew and Natalie Prior"),
        ],
    },
    "Erudite": {
        "gradiente": "linear-gradient(135deg, #0a1e3c 0%, #1d3f6b 50%, #5b8fd6 100%)",
        "rgb_top": (10, 30, 60),
        "rgb_bottom": (91, 143, 214),
        "emoji": "👁️",
        "descrizione": "Knowledge is your beacon. You never stop asking questions, and truth matters more to you than comfort.",
        "dettagli": [
            ("Headquarters", "The great central library"),
            ("Symbol", "Eye"),
            ("Colors", "Blue"),
            ("Values", "Intelligence, curiosity, logic"),
            ("Notable characters", "Caleb Prior, Jeanine Matthews"),
        ],
    },
    "Dauntless": {
        "gradiente": "linear-gradient(135deg, #100a08 0%, #4a1a0a 50%, #c8641e 100%)",
        "rgb_top": (16, 10, 8),
        "rgb_bottom": (200, 100, 30),
        "emoji": "🔥",
        "descrizione": "You live for the moment fear turns into action. The leap into the void doesn't scare you — that's when you feel most alive.",
        "dettagli": [
            ("Headquarters", "Former amusement park, near the train tracks"),
            ("Symbol", "Flames"),
            ("Colors", "Black"),
            ("Values", "Courage, boldness, adrenaline"),
            ("Notable characters", "Tris Prior (by choice), Tobias 'Four' Eaton"),
        ],
    },
    "Amity": {
        "gradiente": "linear-gradient(135deg, #4a1608 0%, #8a4a12 50%, #e0c04a 100%)",
        "rgb_top": (74, 22, 8),
        "rgb_bottom": (224, 192, 74),
        "emoji": "🌳",
        "descrizione": "You seek harmony wherever you go. You'd rather build bridges than win a fight.",
        "dettagli": [
            ("Headquarters", "Orchards and farms outside the city"),
            ("Symbol", "Tree"),
            ("Colors", "Red and yellow"),
            ("Values", "Peace, kindness, harmony"),
            ("Notable characters", "Robert Black"),
        ],
    },
    "Candor": {
        "gradiente": "linear-gradient(135deg, #141414 0%, #6a6a6a 50%, #e6e6e6 100%)",
        "rgb_top": (20, 20, 20),
        "rgb_bottom": (230, 230, 230),
        "emoji": "⚖️",
        "descrizione": "You can't stand lies, not even kind ones. You say what you think, always, even when it hurts.",
        "dettagli": [
            ("Headquarters", "The courthouse, a black-and-white building"),
            ("Symbol", "Scale"),
            ("Colors", "Black and white"),
            ("Values", "Honesty, frankness, truth"),
            ("Notable characters", "Christina"),
        ],
    },
}

QUESTIONS_DIV = [
    {
        "domanda": "Choosing Day has arrived and the knife trembles in your hand. What do you think in that instant?",
        "opzioni": [
            ("I think about who'd be left without my help if I left", {"Abnegation": 1}),
            ("I think about which choice is objectively the most rational for my future", {"Erudite": 1}),
            ("I only think about the leap I'm about to take, without looking back", {"Dauntless": 1}),
            ("I think about staying at peace with everyone, whatever I choose", {"Amity": 1}),
            ("I think I should just say out loud what I really feel", {"Candor": 1}),
        ],
    },
    {
        "domanda": "During training, a fellow initiate openly challenges you in front of the group. How do you react?",
        "opzioni": [
            ("I try to calm the situation, setting my pride aside", {"Abnegation": 1}),
            ("I respond with a logical argument that dismantles their provocation", {"Erudite": 1}),
            ("I accept the challenge right away, whatever it is", {"Dauntless": 1}),
            ("I try to understand what's really bothering them, beyond the challenge", {"Amity": 1}),
            ("I tell them clearly what I think of them, no beating around the bush", {"Candor": 1}),
        ],
    },
    {
        "domanda": "You discover an uncomfortable secret about someone you respect. What do you do?",
        "opzioni": [
            ("I keep it to myself, if revealing it would do more harm than good", {"Abnegation": 1}),
            ("I carefully verify the facts before drawing conclusions", {"Erudite": 1}),
            ("I confront them directly, right away, without beating around the bush", {"Dauntless": 1}),
            ("I wait for the right moment to bring it up gently", {"Amity": 1}),
            ("I can't keep it in: the truth has to be told", {"Candor": 1}),
        ],
    },
    {
        "domanda": "Deep down, what do you fear most?",
        "opzioni": [
            ("Becoming selfish and forgetting about others", {"Abnegation": 1}),
            ("Staying ignorant or making a mistake out of carelessness", {"Erudite": 1}),
            ("Being paralyzed by fear in the decisive moment", {"Dauntless": 1}),
            ("Constant conflict and the loss of harmony", {"Amity": 1}),
            ("Being forced to lie or hide who I really am", {"Candor": 1}),
        ],
    },
    {
        "domanda": "Your ideal place in society would be...",
        "opzioni": [
            ("A role of quiet service, with no need for recognition", {"Abnegation": 1}),
            ("A lab or library where I could study without limits", {"Erudite": 1}),
            ("On the front line, protecting others through concrete action", {"Dauntless": 1}),
            ("A place that fosters peace and cooperation among everyone", {"Amity": 1}),
            ("A place where the truth always comes out, no exceptions", {"Candor": 1}),
        ],
    },
    {
        "domanda": "A friend asks for your honest opinion on an important choice. How do you respond?",
        "opzioni": [
            ("I think mainly about how my answer will affect them", {"Abnegation": 1}),
            ("I offer them an objective analysis of the pros and cons", {"Erudite": 1}),
            ("I encourage them to go for it, whatever the risk", {"Dauntless": 1}),
            ("I look for the gentlest answer, one that hurts no one", {"Amity": 1}),
            ("I tell them exactly what I think, even if it's uncomfortable", {"Candor": 1}),
        ],
    },
    {
        "domanda": "What makes you feel strongest?",
        "opzioni": [
            ("Knowing I helped someone without asking for anything in return", {"Abnegation": 1}),
            ("Having understood something no one else had grasped", {"Erudite": 1}),
            ("Having overcome a fear that had held me back for a long time", {"Dauntless": 1}),
            ("Having brought calm to a tense situation", {"Amity": 1}),
            ("Having told the truth even when it was hard to do", {"Candor": 1}),
        ],
    },
    {
        "domanda": "How do you react in the face of an injustice?",
        "opzioni": [
            ("I try to fix it by concretely helping whoever's suffering from it", {"Abnegation": 1}),
            ("I gather solid evidence and arguments to prove it", {"Erudite": 1}),
            ("I react on instinct, right away, without much calculation", {"Dauntless": 1}),
            ("I try to mediate, looking for an agreement that works for everyone", {"Amity": 1}),
            ("I call it out openly, unafraid of the consequences", {"Candor": 1}),
        ],
    },
    {
        "domanda": "If you had to pick just one value to uphold forever, which would it be?",
        "opzioni": [
            ("Selflessness", {"Abnegation": 1}),
            ("Knowledge", {"Erudite": 1}),
            ("Courage", {"Dauntless": 1}),
            ("Peace", {"Amity": 1}),
            ("Honesty", {"Candor": 1}),
        ],
    },
    {
        "domanda": "It's the last night before a decisive trial. How do you spend it?",
        "opzioni": [
            ("I think about how I can be useful to others the next day", {"Abnegation": 1}),
            ("I go over every single detail that might come in handy", {"Erudite": 1}),
            ("I can't sit still, I just want the moment to arrive", {"Dauntless": 1}),
            ("I stay with people I love, so I can face it all calmly", {"Amity": 1}),
            ("I openly confront myself about what I really feel", {"Candor": 1}),
        ],
    },
]


# ============================================================
# DATA — HUNGER GAMES DISTRICTS
# (industry, symbol, colors, notable tributes, values: factual
#  factual details of the novel's universe, not protected text)
# ============================================================
DISTRICTS = {
    "District 1": {
        "gradiente": "linear-gradient(135deg, #6b5108 0%, #b8952e 50%, #f0dfa0 100%)",
        "rgb_top": (107, 81, 8),
        "rgb_bottom": (240, 223, 160),
        "emoji": "💎",
        "descrizione": "You were raised to win. Competition motivates you more than anything else, and you rarely doubt your abilities.",
        "dettagli": [
            ("Industry", "Luxury goods and jewelry"),
            ("Symbol", "Diamond"),
            ("Colors", "Gold and ivory"),
            ("Notable tributes", "Glimmer, Marvel"),
            ("Values", "Ambition, competitiveness, self-confidence"),
        ],
    },
    "District 2": {
        "gradiente": "linear-gradient(135deg, #2b2b2b 0%, #5a1414 50%, #8a2020 100%)",
        "rgb_top": (43, 43, 43),
        "rgb_bottom": (138, 32, 32),
        "emoji": "⛏️",
        "descrizione": "You've trained your whole life to be ready for any challenge. Discipline is your armor.",
        "dettagli": [
            ("Industry", "Stone quarries and training"),
            ("Symbol", "Crossed hammer and pickaxe"),
            ("Colors", "Stone grey and red"),
            ("Notable tributes", "Cato, Clove"),
            ("Values", "Strength, discipline, rigorous training"),
        ],
    },
    "District 3": {
        "gradiente": "linear-gradient(135deg, #1c2128 0%, #384a5c 50%, #6fa3c9 100%)",
        "rgb_top": (28, 33, 40),
        "rgb_bottom": (111, 163, 201),
        "emoji": "⚙️",
        "descrizione": "Your mind works like a perfect mechanism: precise, methodical, always one step ahead in finding solutions no one else sees.",
        "dettagli": [
            ("Industry", "Electronics and technology"),
            ("Symbol", "Gear and circuit"),
            ("Colors", "Metallic grey and electric blue"),
            ("Notable tributes", "Beetee, Wiress"),
            ("Values", "Ingenuity, precision, lateral thinking"),
        ],
    },
    "District 4": {
        "gradiente": "linear-gradient(135deg, #063a42 0%, #157a8a 50%, #6ec6d4 100%)",
        "rgb_top": (6, 58, 66),
        "rgb_bottom": (110, 198, 212),
        "emoji": "🎣",
        "descrizione": "You move with the same ease as someone raised among the waves: able to adapt to any current, yet deeply rooted.",
        "dettagli": [
            ("Industry", "Fishing and seafood"),
            ("Symbol", "Net and trident"),
            ("Colors", "Turquoise and silver"),
            ("Notable tributes", "Finnick Odair, Annie Cresta"),
            ("Values", "Adaptability, charm, quiet resilience"),
        ],
    },
    "District 5": {
        "gradiente": "linear-gradient(135deg, #3a3418 0%, #7a6d1e 50%, #c9b93c 100%)",
        "rgb_top": (58, 52, 24),
        "rgb_bottom": (201, 185, 60),
        "emoji": "🔌",
        "descrizione": "You move quietly, watching everything before acting. Your practical intelligence lets you survive without ever exposing yourself too much.",
        "dettagli": [
            ("Industry", "Electric power production"),
            ("Symbol", "Stylized lightning bolt"),
            ("Colors", "Yellow and industrial grey"),
            ("Notable tributes", "Foxface (the girl with the fox face)"),
            ("Values", "Intuition, caution, self-sufficiency"),
        ],
    },
    "District 7": {
        "gradiente": "linear-gradient(135deg, #14200e 0%, #355c26 50%, #6e9b4f 100%)",
        "rgb_top": (20, 32, 14),
        "rgb_bottom": (110, 155, 79),
        "emoji": "🪓",
        "descrizione": "Behind a rough exterior, you hide a sharp mind. Never underestimate whoever seems the weakest in the room: it might be you.",
        "dettagli": [
            ("Industry", "Timber cutting"),
            ("Symbol", "Axe"),
            ("Colors", "Forest green and brown"),
            ("Notable tributes", "Johanna Mason"),
            ("Values", "Endurance, hidden cunning, independence"),
        ],
    },
    "District 8": {
        "gradiente": "linear-gradient(135deg, #2e1a38 0%, #5e3970 50%, #a97fc0 100%)",
        "rgb_top": (46, 26, 56),
        "rgb_bottom": (169, 127, 192),
        "emoji": "🧵",
        "descrizione": "You turn hard work into something beautiful. Behind labor that's often invisible to others, you hide a creativity capable of leaving its mark.",
        "dettagli": [
            ("Industry", "Textile production"),
            ("Symbol", "Loom and shuttle"),
            ("Colors", "Purple and pearl grey"),
            ("Notable tributes", "Cinna (stylist originally from District 8)"),
            ("Values", "Creativity, quiet resilience, aesthetic sense"),
        ],
    },
    "District 11": {
        "gradiente": "linear-gradient(135deg, #2e2a0a 0%, #6b5f1a 50%, #a8973c 100%)",
        "rgb_top": (46, 42, 10),
        "rgb_bottom": (168, 151, 60),
        "emoji": "🌾",
        "descrizione": "A sense of community is your compass. You protect others with a quiet but unshakeable loyalty.",
        "dettagli": [
            ("Industry", "Large-scale agriculture"),
            ("Symbol", "Wheat sheaf"),
            ("Colors", "Olive green and ochre"),
            ("Notable tributes", "Rue, Thresh"),
            ("Values", "Community, kindness, quiet strength"),
        ],
    },
    "District 12": {
        "gradiente": "linear-gradient(135deg, #0a0a0a 0%, #2e2e30 50%, #5a5a5e 100%)",
        "rgb_top": (10, 10, 10),
        "rgb_bottom": (90, 90, 94),
        "emoji": "🔥",
        "descrizione": "You've learned to survive on little, and that's made you stronger than you realize. For the people you love, you'd be ready for anything.",
        "dettagli": [
            ("Industry", "Coal mining"),
            ("Symbol", "Flame"),
            ("Colors", "Anthracite black and grey"),
            ("Notable tributes", "Katniss Everdeen, Peeta Mellark"),
            ("Values", "Survival, sacrifice, resilience"),
        ],
    },
}

QUESTIONS_HG = [
    {
        "domanda": "On Reaping Day, your name is called out loud. What's your first thought?",
        "opzioni": [
            ("This is my chance to shine in front of everyone", {"District 1": 1}),
            ("I'm ready: I've trained my whole life for this moment", {"District 2": 1}),
            ("I immediately start weighing every possible scenario, with a clear head", {"District 3": 1}),
            ("I think about how fast I'll need to adapt to an environment I don't know", {"District 4": 1}),
        ],
    },
    {
        "domanda": "You're in the arena and find the Cornucopia full of supplies. What do you do?",
        "opzioni": [
            ("I watch everything from a distance before approaching, unhurried", {"District 5": 1}),
            ("I wait off to the side, watching who trusts the others least", {"District 7": 1}),
            ("I grab something useful but not essential, without risking too much", {"District 8": 1}),
            ("I think first about who might need an item more than me", {"District 11": 1}),
        ],
    },
    {
        "domanda": "An ally betrays you at your moment of need. How do you react?",
        "opzioni": [
            ("I still find the strength to carry on alone", {"District 12": 1}),
            ("I'm annoyed, but I expected it: an alliance only lasts as long as it's useful", {"District 1": 1}),
            ("I don't let it throw me off: I stick to my training", {"District 2": 1}),
            ("I coolly analyze what this changes for the rest of my plan", {"District 3": 1}),
        ],
    },
    {
        "domanda": "What's your favorite survival strategy?",
        "opzioni": [
            ("Adapting quickly to whatever environment I end up in", {"District 4": 1}),
            ("Staying low, watching everything, moving only when needed", {"District 5": 1}),
            ("Staying in the shadows until it's time to strike", {"District 7": 1}),
            ("Patiently building something useful with my hands", {"District 8": 1}),
        ],
    },
    {
        "domanda": "Deep down, what do you fear most?",
        "opzioni": [
            ("Failing to protect those who need me", {"District 11": 1}),
            ("Failing to protect the people I love", {"District 12": 1}),
            ("Being remembered as too weak to matter", {"District 1": 1}),
            ("Failing after training my whole life for this", {"District 2": 1}),
        ],
    },
    {
        "domanda": "How do you behave in front of the cameras, during interviews?",
        "opzioni": [
            ("I answer in a calculated way, without revealing too much", {"District 3": 1}),
            ("I try to be charismatic, without giving too much of myself away", {"District 4": 1}),
            ("I say as little as possible, staying elusive", {"District 5": 1}),
            ("I let others underestimate me: it works in my favor", {"District 7": 1}),
        ],
    },
    {
        "domanda": "Your greatest strength is...",
        "opzioni": [
            ("Patience and attention to detail", {"District 8": 1}),
            ("The ability to inspire trust in others", {"District 11": 1}),
            ("Resilience: I hold on even when all seems lost", {"District 12": 1}),
            ("The charm and confidence I project to others", {"District 1": 1}),
        ],
    },
    {
        "domanda": "Food is scarce in the arena. What do you do?",
        "opzioni": [
            ("I actively go hunting, without waiting", {"District 2": 1}),
            ("I build a calculated trap with what I have on hand", {"District 3": 1}),
            ("I trust my instinct to find a nearby water or food source", {"District 4": 1}),
            ("I carefully ration what I have, with no waste", {"District 5": 1}),
        ],
    },
    {
        "domanda": "What truly motivates you to fight to the end?",
        "opzioni": [
            ("Proving that whoever seems weak can surprise everyone", {"District 7": 1}),
            ("The desire to go back to creating something of my own", {"District 8": 1}),
            ("The people in my community counting on me", {"District 11": 1}),
            ("The people I love, back home", {"District 12": 1}),
        ],
    },
    {
        "domanda": "How do you choose your allies?",
        "opzioni": [
            ("I look for someone who gives me a concrete advantage", {"District 1": 1}),
            ("I carefully consider who has skills that complement mine", {"District 3": 1}),
            ("I rarely trust anyone: I mostly prefer to rely on myself", {"District 5": 1}),
            ("I look for someone who shares my same patience and loyalty", {"District 8": 1}),
        ],
    },
    {
        "domanda": "What's your relationship with rules imposed from above?",
        "opzioni": [
            ("I follow them with discipline: I've trained for this", {"District 2": 1}),
            ("I respect them, but I know how to adapt if things change", {"District 4": 1}),
            ("I quietly work around them, without drawing attention", {"District 7": 1}),
            ("I respect them if they protect my community, otherwise not", {"District 11": 1}),
        ],
    },
    {
        "domanda": "If you survived the Games, what would you do first?",
        "opzioni": [
            ("I'd protect the people I love, more fiercely than before", {"District 12": 1}),
            ("I'd enjoy the recognition I earned", {"District 1": 1}),
            ("I'd look for somewhere quiet, far from the spotlight", {"District 5": 1}),
            ("I'd go back to creating something beautiful with my hands", {"District 8": 1}),
        ],
    },
]


# ============================================================
# DATA — CHARACTER CREATOR (original elements for each
# world: traits, items, allies; the final affiliation is chosen
# from the entities already defined above for each world)
# ============================================================
CREATOR_DATA = {
    "hogwarts": {
        "titolo": "Create Your Wizard",
        "eyebrow": "THE MINISTRY OF MAGIC REGISTERS A NEW WITCH OR WIZARD",
        "tratti": ["Brave", "Cunning", "Loyal", "Curious", "Ambitious", "Kind", "Rebellious", "Studious"],
        "oggetti": ["A rowan wood wand", "A family invisibility cloak",
                    "A time-turner forgotten in the attic", "A mirror that reveals emotions",
                    "A rusty but fast racing broom", "A cauldron that bubbles on its own"],
        "alleati": ["A loyal messenger owl", "A cat with golden eyes", "A small tamed dragon",
                    "A devoted house-elf", "A companion phoenix", "A loyal hippogriff"],
        "entita": HOUSES,
        "gradiente_default": "linear-gradient(135deg, #1c140b 0%, #4a2f0e 50%, #8a6a12 100%)",
        "rgb_top": (28, 20, 11),
        "rgb_bottom": (138, 106, 18),
        "font_titolo": "titolo_hp",
    },
    "percy": {
        "titolo": "Create Your Demigod",
        "eyebrow": "CAMP HALF-BLOOD WELCOMES A NEW CAMPER",
        "tratti": ["Brave", "Loyal", "Cunning", "Impulsive", "Protective", "Curious", "Witty", "Determined"],
        "oggetti": ["A celestial bronze sword", "A shield engraved with ancient symbols",
                    "A bow that never misses its target", "A dagger forged in shadow",
                    "A protective amulet", "A pair of winged sandals"],
        "alleati": ["A satyr scout", "A wood nymph", "A tamed hellhound",
                    "A loyal pegasus", "A silent guiding spirit", "An inseparable demigod companion"],
        "entita": GODS,
        "gradiente_default": "linear-gradient(135deg, #060d24 0%, #0e1a40 50%, #2b4a8c 100%)",
        "rgb_top": (6, 13, 36),
        "rgb_bottom": (43, 74, 140),
        "font_titolo": "titolo_pj",
    },
    "divergent": {
        "titolo": "Create Your Initiate",
        "eyebrow": "THE CHOOSING CEREMONY WELCOMES A NEW INITIATE",
        "tratti": ["Selfless", "Brave", "Intelligent", "Honest", "Peaceful", "Ambitious", "Loyal", "Independent"],
        "oggetti": ["A perfectly balanced throwing knife", "An armored jacket",
                    "A simulation manual", "A faction walkie-talkie",
                    "A secret journal", "A pair of jumping boots"],
        "alleati": ["A trusted training partner", "A strict but fair mentor",
                    "A loyal childhood friend", "A mysterious informant",
                    "A Dauntless instructor", "An Erudite ally"],
        "entita": DIVERGENT,
        "gradiente_default": "linear-gradient(135deg, #0d1114 0%, #2b3238 50%, #4a555e 100%)",
        "rgb_top": (13, 17, 20),
        "rgb_bottom": (74, 85, 94),
        "font_titolo": "titolo_div",
    },
    "hunger": {
        "titolo": "Create Your Tribute",
        "eyebrow": "THE CAPITOL PRESENTS A NEW TRIBUTE",
        "tratti": ["Resilient", "Cunning", "Loyal", "Quiet", "Charismatic", "Protective", "Calculating", "Brave"],
        "oggetti": ["A bow with a quiver", "A throwing knife", "A fishing net",
                    "A medicinal herb kit", "A slingshot", "A camouflage cloak"],
        "alleati": ["A trusted allied tribute", "An experienced mentor", "A mysterious sponsor",
                    "A district companion", "A silent guide", "A tamed forest animal"],
        "entita": DISTRICTS,
        "gradiente_default": "linear-gradient(135deg, #0c0f08 0%, #2c3322 50%, #6b7a4a 100%)",
        "rgb_top": (12, 15, 8),
        "rgb_bottom": (107, 122, 74),
        "font_titolo": "titolo_hg",
    },
}


# ============================================================
# DATA — SURVIVAL IN THE ARENA (Hunger Games)
# Original branching narrative simulator, not protected text.
# Each choice affects health and supplies; if health drops
# to zero, the tribute is eliminated before the days end.
# ============================================================
GIORNI_ARENA = [
    {
        "situazione": "The gong sounds and the Cornucopia is just steps away, surrounded by supplies and other tributes ready to spring into action. What do you do?",
        "scelte": [
            ("I rush to the center to grab as much as I can, risking a confrontation", {"salute": -15, "provviste": 25}),
            ("I run straight for the forest, risking nothing", {"salute": 0, "provviste": 0}),
            ("I grab only what's within reach at the edge, without getting too close", {"salute": -3, "provviste": 10}),
        ],
    },
    {
        "situazione": "You find a water source, but another tribute seems to be lying in wait among the bushes, guarding it. What do you do?",
        "scelte": [
            ("I confront them openly to get a clear path", {"salute": -15, "provviste": 15}),
            ("I hide and wait for them to leave", {"salute": 0, "provviste": 5}),
            ("I look for another, safer water source further away", {"salute": -5, "provviste": -5}),
        ],
    },
    {
        "situazione": "You come across another tribute, wounded and unarmed, who doesn't seem like a threat. What do you do?",
        "scelte": [
            ("I help them, sharing some of my supplies", {"salute": 0, "provviste": -15}),
            ("I ignore them and go on my way", {"salute": 0, "provviste": 0}),
            ("I take the opportunity to grab their equipment", {"salute": 0, "provviste": 12}),
        ],
    },
    {
        "situazione": "At night, a violent storm unleashed by the Gamemakers breaks out. How do you react?",
        "scelte": [
            ("I immediately look for safe shelter, even if it costs me time and supplies", {"salute": 8, "provviste": -10}),
            ("I keep moving so I don't lose precious ground", {"salute": -12, "provviste": -5}),
            ("I hunker down where I am, saving my strength", {"salute": -5, "provviste": 0}),
        ],
    },
    {
        "situazione": "Supplies are starting to run low and hunger sets in. What do you do?",
        "scelte": [
            ("I go hunting, risking being spotted by other tributes", {"salute": -10, "provviste": 20}),
            ("I ration what I have and wait for a safer moment", {"salute": -5, "provviste": -8}),
            ("I send a signal, hoping a sponsor will help", {"salute": 0, "provviste": 12}),
        ],
    },
    {
        "situazione": "Only a handful of tributes remain. The final gong is about to sound. How do you face the last confrontation?",
        "scelte": [
            ("I face the last opponent head-on", {"salute": -20, "provviste": 0}),
            ("I set a strategic ambush, using the terrain to my advantage", {"salute": -10, "provviste": 0}),
            ("I hold back and wait for the others to eliminate each other", {"salute": -5, "provviste": 0}),
        ],
    },
]


# ============================================================
# DATA — INTERACTIVE MAPS (points of interest for each world:
# factual details of the narrative universe, not protected text)
# ============================================================
MAP_POIS = {
    "hogwarts": {
        "titolo": "Map of Hogwarts",
        "eyebrow": "\"Not every hidden passage is found on the first attempt...\"",
        "stile_card": "parchment",
        "font_titolo_css": "hat-title",
        "luoghi": [
            {"slug": "salone", "nome": "The Great Hall", "x": 130, "y": 120,
             "desc": "The beating heart of the castle: meals are eaten here beneath an enchanted ceiling that mirrors the real sky, and major ceremonies like the Sorting take place here."},
            {"slug": "biblioteca", "nome": "The Library", "x": 400, "y": 90,
             "desc": "A vast collection of magical books and scrolls, strictly guarded. Some sections, the most dangerous ones, are accessible only with special permission."},
            {"slug": "foresta", "nome": "The Forbidden Forest", "x": 620, "y": 220,
             "desc": "A dense, dark forest at the edge of the school, home to powerful and unpredictable magical creatures. Students may not enter without authorization."},
            {"slug": "quidditch", "nome": "The Quidditch Pitch", "x": 250, "y": 300,
             "desc": "A wide oval field where matches between the four houses are played, watched by the whole school from the stands."},
            {"slug": "torre", "nome": "The Astronomy Tower", "x": 520, "y": 60,
             "desc": "The highest point of the castle, used for night-sky observation lessons and reached by a long spiral staircase."},
        ],
    },
    "percy": {
        "titolo": "Map of Camp Half-Blood",
        "eyebrow": "\"It's never safe for a demigod to stay still for too long.\"",
        "stile_card": "marble",
        "font_titolo_css": "camp-title",
        "luoghi": [
            {"slug": "casa_grande", "nome": "The Big House", "x": 400, "y": 100,
             "desc": "The camp's administrative headquarters, where instructors reside and the most important meetings among camp leaders take place."},
            {"slug": "arena", "nome": "The Combat Arena", "x": 160, "y": 200,
             "desc": "An open-air space dedicated to sword and weapons training, overseen by the most experienced instructors."},
            {"slug": "bosco", "nome": "The Woods", "x": 620, "y": 160,
             "desc": "A wide wild area where campers face practical trials and, at times, genuine mythological creatures."},
            {"slug": "spiaggia", "nome": "The Beach", "x": 300, "y": 320,
             "desc": "The stretch of coastline where the camp meets the sea, a territory where Poseidon's influence is felt most strongly."},
            {"slug": "cabine", "nome": "The Cabins", "x": 500, "y": 280,
             "desc": "The camp's residential area, with a building dedicated to each Olympian god who has children among the campers."},
        ],
    },
    "divergent": {
        "titolo": "Map of the Faction City",
        "eyebrow": "\"Faction before blood.\"",
        "stile_card": "steel",
        "font_titolo_css": "steel-title",
        "luoghi": [
            {"slug": "erudito", "nome": "The Erudite Quarter", "x": 150, "y": 100,
             "desc": "A complex of libraries and laboratories where Erudite conduct research and preserve the city's knowledge."},
            {"slug": "pozzo", "nome": "The Pit", "x": 420, "y": 90,
             "desc": "The underground entrance to the Dauntless compound, reachable only by a leap into the void for new initiates."},
            {"slug": "recinto", "nome": "The Fence", "x": 620, "y": 240,
             "desc": "The city's outer boundary, patrolled and maintained by Abnegation to protect those living within."},
            {"slug": "tribunale", "nome": "The Courthouse", "x": 300, "y": 300,
             "desc": "The black-and-white building where Candor administers justice, based on the collective pursuit of truth."},
            {"slug": "frutteti", "nome": "The Orchards", "x": 500, "y": 340,
             "desc": "The farmland cultivated by Amity, outside the city center, a source of much of the community's food."},
        ],
    },
    "hunger": {
        "titolo": "Map of Panem",
        "eyebrow": "\"May fortune find you when it matters most.\"",
        "stile_card": "canvas",
        "font_titolo_css": "arena-title",
        "luoghi": [
            {"slug": "capitol", "nome": "The Capitol", "x": 400, "y": 80,
             "desc": "The political and administrative heart of Panem, home to the central government and the spectacle shown during the Games."},
            {"slug": "arena", "nome": "The Arena", "x": 180, "y": 180,
             "desc": "The artificial theater built each year to host the Games, with a different environment and rules every time."},
            {"slug": "villaggio", "nome": "The Victors' Village", "x": 620, "y": 200,
             "desc": "A neighborhood of houses reserved for past winners of the Games, located on the edge of their home district."},
            {"slug": "miniera", "nome": "The Coal Mine", "x": 280, "y": 320,
             "desc": "The industrial heart of District 12, where most of the population works under brutal conditions."},
            {"slug": "giustizia", "nome": "The Justice Building", "x": 500, "y": 300,
             "desc": "The main building of each district, where the Reaping ceremony takes place every year."},
        ],
    },
}



# ============================================================
# GLOBAL CSS — shared background + two typographic identities
# (parchment/Hogwarts and marble/Olympus)
# ============================================================
st.markdown(
    textwrap.dedent("""\
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700&family=Cinzel+Decorative:wght@700;900&family=EB+Garamond:ital,wght@0,400;0,600;1,400&family=IM+Fell+English:ital@0;1&family=Lora:ital,wght@0,500;1,500&family=IBM+Plex+Mono:wght@500&family=Barlow+Condensed:wght@600;700&family=Barlow:ital,wght@0,400;1,400&family=Philosopher:wght@700&family=Bebas+Neue&family=Crimson+Text:ital@0;1&display=swap');

    html, body, [class*="css"] { font-family: 'EB Garamond', serif; }

    .stApp {
        background:
            radial-gradient(ellipse at top left, rgba(120,90,30,0.25), transparent 55%),
            radial-gradient(ellipse at bottom right, rgba(40,20,60,0.35), transparent 55%),
            linear-gradient(180deg, #120d08 0%, #1c140b 40%, #120d08 100%);
        background-attachment: fixed;
    }

    #MainMenu, footer, header {visibility: hidden;}

    .hat-title {
        font-family: 'Cinzel Decorative', serif;
        font-size: 2.6rem;
        text-align: center;
        background: linear-gradient(180deg, #f3d98b 0%, #c9a227 55%, #8a6a12 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 25px rgba(201,162,39,0.25);
        margin-bottom: 0;
        animation: flicker 4s infinite ease-in-out;
    }
    @keyframes flicker { 0%, 100% { opacity: 1; } 50% { opacity: 0.88; } }

    .subtitle {
        font-family: 'IM Fell English', serif;
        font-style: italic;
        text-align: center;
        color: #cbb989;
        font-size: 1.05rem;
        margin-top: -8px;
        margin-bottom: 1.6rem;
        letter-spacing: 0.5px;
    }

    .parchment {
        background:
            radial-gradient(circle at 15% 20%, rgba(139,110,60,0.18), transparent 40%),
            radial-gradient(circle at 85% 80%, rgba(90,60,20,0.22), transparent 45%),
            linear-gradient(135deg, #ecdcb2 0%, #e2cd9a 50%, #dcc389 100%);
        border: 1px solid #8a6a12;
        outline: 6px solid #120d08;
        outline-offset: -12px;
        border-radius: 4px;
        padding: 2rem 2.2rem;
        box-shadow: 0 15px 45px rgba(0,0,0,0.55), inset 0 0 60px rgba(120,90,40,0.25);
        color: #2b1d0e;
        margin-bottom: 1.4rem;
    }
    .parchment h3 {
        font-family: 'Cinzel Decorative', serif;
        font-size: 1.25rem;
        color: #4a2f0e;
        border-bottom: 1px solid #8a6a12;
        padding-bottom: 8px;
        margin-top: 0;
    }

    .marble {
        background:
            radial-gradient(circle at 20% 25%, rgba(150,160,170,0.35), transparent 45%),
            radial-gradient(circle at 80% 75%, rgba(120,130,145,0.3), transparent 45%),
            linear-gradient(135deg, #eef0ee 0%, #e3e6e6 50%, #d9dcdb 100%);
        border: 1px solid #a68a3c;
        outline: 6px solid #120d08;
        outline-offset: -12px;
        border-radius: 2px;
        padding: 2rem 2.2rem;
        box-shadow: 0 15px 45px rgba(0,0,0,0.55), inset 0 0 50px rgba(120,130,140,0.25);
        color: #1c2430;
        margin-bottom: 1.4rem;
    }
    .marble h3 {
        font-family: 'Cinzel', serif;
        font-size: 1.2rem;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        color: #1c2430;
        border-bottom: 1px solid #a68a3c;
        padding-bottom: 8px;
        margin-top: 0;
    }

    .qcounter {
        font-family: 'IM Fell English', serif;
        font-style: italic;
        color: #cbb989;
        text-align: center;
        font-size: 1rem;
        margin-bottom: 6px;
    }
    .qcounter.oly {
        font-family: 'IBM Plex Mono', monospace;
        font-style: normal;
        letter-spacing: 2px;
        text-transform: uppercase;
        font-size: 0.8rem;
        color: #2b3b4a;
    }

    .camp-title {
        font-family: 'Cinzel', serif;
        font-size: 2.6rem;
        text-align: center;
        letter-spacing: 3px;
        background: linear-gradient(180deg, #0b3d59 0%, #145c86 55%, #b8860b 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .camp-subtitle {
        font-family: 'Lora', serif;
        font-style: italic;
        text-align: center;
        color: #3a4a3a;
        font-size: 1.05rem;
        margin-top: -8px;
        margin-bottom: 1.2rem;
        letter-spacing: 0.3px;
    }

    .steel-title {
        font-family: 'Barlow Condensed', sans-serif;
        font-weight: 700;
        font-size: 2.8rem;
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 4px;
        color: #d8dde2;
        text-shadow: 0 0 20px rgba(120,140,160,0.35);
        margin-bottom: 0;
    }
    .steel-subtitle {
        font-family: 'Barlow', sans-serif;
        font-style: italic;
        text-align: center;
        color: #8a95a0;
        font-size: 1rem;
        margin-top: -6px;
        margin-bottom: 1.4rem;
        letter-spacing: 0.5px;
    }
    .steel {
        background:
            repeating-linear-gradient(135deg, rgba(255,255,255,0.02) 0px, rgba(255,255,255,0.02) 2px, transparent 2px, transparent 14px),
            linear-gradient(135deg, #2b3238 0%, #3a434b 50%, #4a555e 100%);
        border: 1px solid #6b7680;
        outline: 6px solid #0d1114;
        outline-offset: -12px;
        border-radius: 2px;
        padding: 2rem 2.2rem;
        box-shadow: 0 15px 45px rgba(0,0,0,0.6), inset 0 0 40px rgba(0,0,0,0.35);
        color: #e4e8eb;
        margin-bottom: 1.4rem;
    }
    .steel h3 {
        font-family: 'Barlow Condensed', sans-serif;
        font-weight: 700;
        font-size: 1.3rem;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: #e4e8eb;
        border-bottom: 1px solid #6b7680;
        padding-bottom: 8px;
        margin-top: 0;
    }
    .qcounter.steel {
        font-family: 'IBM Plex Mono', monospace;
        font-style: normal;
        letter-spacing: 2px;
        text-transform: uppercase;
        font-size: 0.8rem;
        color: #8a95a0;
    }
    .result-house.steel {
        font-family: 'Barlow Condensed', sans-serif;
        font-weight: 700;
        letter-spacing: 3px;
        text-transform: uppercase;
        font-size: 2.2rem;
    }
    .result-desc.steel {
        font-family: 'Barlow', sans-serif;
        font-style: italic;
    }
    .fact-label.steel {
        font-family: 'IBM Plex Mono', monospace;
        font-style: normal;
        letter-spacing: 1px;
        text-transform: uppercase;
        font-size: 0.7rem;
    }

    .nexus-title {
        font-family: 'Philosopher', sans-serif;
        font-weight: 700;
        font-size: 2.7rem;
        text-align: center;
        letter-spacing: 2px;
        background: linear-gradient(90deg, #f3d98b 0%, #7fc7d9 50%, #e08a3c 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 30px rgba(255,255,255,0.15);
        margin-bottom: 0;
    }
    .nexus-subtitle {
        font-family: 'IBM Plex Mono', monospace;
        text-align: center;
        color: #b8b6c9;
        font-size: 0.85rem;
        letter-spacing: 2.5px;
        text-transform: uppercase;
        margin-top: -4px;
        margin-bottom: 0.6rem;
    }

    .arena-title {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 3.2rem;
        text-align: center;
        letter-spacing: 3px;
        color: #e0995c;
        text-shadow: 0 0 22px rgba(224,153,92,0.4), 0 2px 4px rgba(0,0,0,0.6);
        margin-bottom: 0;
    }
    .arena-subtitle {
        font-family: 'Crimson Text', serif;
        font-style: italic;
        text-align: center;
        color: #9fae95;
        font-size: 1.05rem;
        margin-top: -6px;
        margin-bottom: 1.4rem;
        letter-spacing: 0.3px;
    }
    .canvas {
        background:
            radial-gradient(circle at 20% 20%, rgba(90,110,70,0.35), transparent 45%),
            radial-gradient(circle at 80% 70%, rgba(60,50,30,0.4), transparent 50%),
            linear-gradient(135deg, #3a4230 0%, #2c3322 50%, #241f16 100%);
        border: 1px solid #6b7a4a;
        outline: 6px solid #120d08;
        outline-offset: -12px;
        border-radius: 2px;
        padding: 2rem 2.2rem;
        box-shadow: 0 15px 45px rgba(0,0,0,0.6), inset 0 0 45px rgba(0,0,0,0.4);
        color: #e6e4d4;
        margin-bottom: 1.4rem;
    }
    .canvas h3 {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.5rem;
        letter-spacing: 2px;
        color: #e0995c;
        border-bottom: 1px solid #6b7a4a;
        padding-bottom: 8px;
        margin-top: 0;
    }
    .qcounter.arena {
        font-family: 'IBM Plex Mono', monospace;
        font-style: normal;
        letter-spacing: 2px;
        text-transform: uppercase;
        font-size: 0.8rem;
        color: #9fae95;
    }
    .result-house.arena {
        font-family: 'Bebas Neue', sans-serif;
        letter-spacing: 3px;
        font-size: 2.6rem;
    }
    .result-desc.arena {
        font-family: 'Crimson Text', serif;
        font-style: italic;
    }
    .fact-label.arena {
        font-family: 'IBM Plex Mono', monospace;
        font-style: normal;
        letter-spacing: 1px;
        text-transform: uppercase;
        font-size: 0.7rem;
    }
    .menu-card-title.arena {
        font-family: 'Bebas Neue', sans-serif;
        letter-spacing: 2px;
        font-size: 1.5rem;
    }

    div.stButton > button {
        width: 100%;
        background: linear-gradient(180deg, #2a1e10 0%, #1a1108 100%);
        color: #e9d9ad;
        border: 1px solid #8a6a12;
        border-radius: 3px;
        padding: 0.8rem 1rem;
        font-family: 'EB Garamond', serif;
        font-size: 1.02rem;
        text-align: left;
        transition: all 0.25s ease;
        box-shadow: inset 0 0 12px rgba(0,0,0,0.4);
    }
    div.stButton > button:hover {
        border-color: #f3d98b;
        color: #f3d98b;
        box-shadow: 0 0 18px rgba(243,217,139,0.35), inset 0 0 12px rgba(0,0,0,0.4);
        transform: translateX(3px);
    }
    div.stButton > button:focus-visible {
        outline: 2px solid #f3d98b;
        outline-offset: 2px;
    }

    .result-card {
        border-radius: 6px;
        padding: 2.2rem 1.8rem;
        text-align: center;
        box-shadow: 0 20px 60px rgba(0,0,0,0.6);
        border: 2px solid rgba(255,255,255,0.25);
        animation: reveal 0.9s ease-out;
    }
    @keyframes reveal {
        0% { opacity: 0; transform: scale(0.85) translateY(20px); }
        100% { opacity: 1; transform: scale(1) translateY(0); }
    }
    .result-house {
        font-family: 'Cinzel Decorative', serif;
        font-size: 2.4rem;
        color: white;
        text-shadow: 0 3px 10px rgba(0,0,0,0.5);
        margin: 0.3rem 0;
    }
    .result-house.oly {
        font-family: 'Cinzel', serif;
        letter-spacing: 3px;
        text-transform: uppercase;
        font-size: 2.1rem;
    }
    .result-desc {
        font-family: 'IM Fell English', serif;
        font-style: italic;
        color: rgba(255,255,255,0.92);
        font-size: 1.15rem;
        max-width: 520px;
        margin: 0.6rem auto 0;
    }
    .result-desc.oly {
        font-family: 'Lora', serif;
        font-style: italic;
        letter-spacing: 0.2px;
    }

    .fact-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
        margin-top: 1.4rem;
        font-family: 'EB Garamond', serif;
    }
    .fact-item {
        background: rgba(0,0,0,0.25);
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 4px;
        padding: 10px 12px;
        color: white;
    }
    .fact-item.span2 { grid-column: span 2; }
    .fact-label {
        font-family: 'IM Fell English', serif;
        font-style: italic;
        font-size: 0.85rem;
        opacity: 0.75;
        display: block;
    }
    .fact-label.oly {
        font-family: 'IBM Plex Mono', monospace;
        font-style: normal;
        letter-spacing: 1px;
        text-transform: uppercase;
        font-size: 0.7rem;
    }
    .fact-value { font-size: 1rem; font-weight: 600; }

    .menu-card {
        border-radius: 6px;
        padding: 1.8rem 1.5rem;
        text-align: center;
        margin-bottom: 0.8rem;
        border: 2px solid rgba(255,255,255,0.18);
        box-shadow: 0 15px 40px rgba(0,0,0,0.5);
        transition: transform 0.25s ease;
    }
    .menu-card:hover { transform: translateY(-4px); }
    .menu-card-icon { font-size: 2.6rem; margin-bottom: 0.4rem; }
    .menu-card-title {
        font-family: 'Cinzel Decorative', serif;
        font-size: 1.4rem;
        color: #f3e9c9;
        margin-bottom: 0.5rem;
    }
    .menu-card-title.oly {
        font-family: 'Cinzel', serif;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        font-size: 1.25rem;
    }
    .menu-card-desc {
        font-family: 'EB Garamond', serif;
        font-style: italic;
        color: rgba(255,255,255,0.85);
        font-size: 0.95rem;
    }
    </style>
    """),
    unsafe_allow_html=True,
)


# ============================================================
# HOGWARTS CREST (original SVG) and OLYMPUS EMBLEM (original SVG)
# ============================================================
def render_crest():
    svg_code = textwrap.dedent("""\
    <div style="display:flex; justify-content:center; margin: 0.4rem 0 1.6rem;">
    <svg width="190" height="220" viewBox="0 0 200 240" xmlns="http://www.w3.org/2000/svg">
    <defs>
    <clipPath id="shieldClip">
    <path d="M12,12 H188 V145 C188,192 100,228 100,228 C100,228 12,192 12,145 Z" />
    </clipPath>
    <radialGradient id="glow" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="#f3d98b" stop-opacity="0.9"/>
    <stop offset="100%" stop-color="#f3d98b" stop-opacity="0"/>
    </radialGradient>
    </defs>
    <g style="animation: crest-rotate 30s linear infinite; transform-origin: 100px 120px;" opacity="0.55">
    <circle cx="100" cy="10" r="2.4" fill="#f3d98b"/>
    <circle cx="190" cy="120" r="2.4" fill="#f3d98b"/>
    <circle cx="100" cy="230" r="2.4" fill="#f3d98b"/>
    <circle cx="10" cy="120" r="2.4" fill="#f3d98b"/>
    </g>
    <g clip-path="url(#shieldClip)">
    <rect x="12" y="12" width="88" height="108" fill="#740001"/>
    <rect x="100" y="12" width="88" height="108" fill="#1a472a"/>
    <rect x="12" y="120" width="88" height="108" fill="#0e1a40"/>
    <rect x="100" y="120" width="88" height="108" fill="#4a3b00"/>
    <path d="M45,55 q10,-18 20,0 q-10,8 0,20 q-15,4 -20,-20 Z" fill="#d3a625" opacity="0.85"/>
    <path d="M150,70 q-18,-4 -14,-22 q16,2 14,22 Z M136,48 q6,-10 12,0 q-6,6 -12,0 Z" fill="#c0c0c0" opacity="0.85"/>
    <path d="M40,170 q4,-14 18,-14 q-2,14 -18,14 Z M45,168 q10,4 18,-2" fill="none" stroke="#946B2D" stroke-width="3" opacity="0.85"/>
    <path d="M145,165 q-16,6 -16,-8 q10,-6 16,8 Z" fill="#2b2b2b" opacity="0.85"/>
    </g>
    <path d="M12,12 H188 V145 C188,192 100,228 100,228 C100,228 12,192 12,145 Z" fill="none" stroke="#f3d98b" stroke-width="3" opacity="0.9"/>
    <circle cx="100" cy="120" r="34" fill="url(#glow)">
    <animate attributeName="r" values="30;36;30" dur="3.5s" repeatCount="indefinite"/>
    </circle>
    <circle cx="100" cy="120" r="26" fill="#120d08" stroke="#f3d98b" stroke-width="2"/>
    <text x="100" y="130" font-family="Cinzel Decorative, serif" font-size="24" font-weight="700" fill="#f3d98b" text-anchor="middle">H</text>
    </svg>
    </div>
    <style>
    @keyframes crest-rotate { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
    </style>
    """)
    st.markdown(svg_code, unsafe_allow_html=True)


def render_olympus_emblem():
    svg_code = textwrap.dedent("""\
    <div style="display:flex; justify-content:center; margin: 0.4rem 0 1.6rem;">
    <svg width="190" height="200" viewBox="0 0 200 210" xmlns="http://www.w3.org/2000/svg">
    <defs>
    <radialGradient id="glow2" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="#f3d98b" stop-opacity="0.9"/>
    <stop offset="100%" stop-color="#f3d98b" stop-opacity="0"/>
    </radialGradient>
    </defs>
    <g style="animation: oly-rotate 26s linear infinite; transform-origin: 100px 105px;" opacity="0.5">
    <path d="M100,8 l4,8 l-8,0 Z" fill="#f3d98b"/>
    <path d="M192,105 l-8,4 l0,-8 Z" fill="#f3d98b"/>
    <path d="M100,202 l4,-8 l-8,0 Z" fill="#f3d98b"/>
    <path d="M8,105 l8,4 l0,-8 Z" fill="#f3d98b"/>
    </g>
    <path d="M100,20 L172,58 V132 L100,190 L28,132 V58 Z" fill="none" stroke="#a68a3c" stroke-width="2" opacity="0.6"/>
    <path d="M30,64 L100,26 L170,64 L158,70 L100,38 L42,70 Z" fill="#d9dcdb" stroke="#a68a3c" stroke-width="1.5"/>
    <path d="M55,120 q-10,20 0,40 q6,-4 4,-20 q8,10 10,-4 q-8,-2 -14,-16 Z" fill="#8fa6ad" opacity="0.85"/>
    <path d="M145,120 q10,20 0,40 q-6,-4 -4,-20 q-8,10 -10,-4 q8,-2 14,-16 Z" fill="#8fa6ad" opacity="0.85"/>
    <path d="M100,55 L106,95 L96,95 Z M92,90 L108,90 L112,100 L88,100 Z" fill="#c9a227"/>
    <circle cx="100" cy="105" r="30" fill="url(#glow2)">
    <animate attributeName="r" values="26;32;26" dur="3.5s" repeatCount="indefinite"/>
    </circle>
    <circle cx="100" cy="105" r="22" fill="#120d08" stroke="#f3d98b" stroke-width="2"/>
    <text x="100" y="113" font-family="Cinzel, serif" font-size="20" font-weight="700" fill="#f3d98b" text-anchor="middle">Ω</text>
    </svg>
    </div>
    <style>
    @keyframes oly-rotate { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
    </style>
    """)
    st.markdown(svg_code, unsafe_allow_html=True)


def render_light_background():
    st.markdown(
        textwrap.dedent("""\
        <style>
        .stApp {
            background:
                radial-gradient(ellipse at top right, rgba(255, 221, 138, 0.35), transparent 55%),
                radial-gradient(ellipse at bottom left, rgba(63, 151, 173, 0.25), transparent 60%),
                linear-gradient(180deg, #cfe8f3 0%, #eaf4e0 45%, #f6e4b8 100%) !important;
            background-attachment: fixed !important;
        }
        </style>
        """),
        unsafe_allow_html=True,
    )


def render_camp_banner():
    svg_code = textwrap.dedent("""\
    <div style="margin: 0 0 1.4rem; border-radius:6px; overflow:hidden; border:1px solid #a68a3c; box-shadow:0 15px 40px rgba(0,0,0,0.25);">
    <svg viewBox="0 0 800 220" xmlns="http://www.w3.org/2000/svg" style="display:block; width:100%; height:auto;">
    <defs>
    <linearGradient id="camp-sky" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="#bfe3f5"/>
    <stop offset="55%" stop-color="#eaf4e0"/>
    <stop offset="100%" stop-color="#f6e4b8"/>
    </linearGradient>
    <linearGradient id="camp-sea" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="#3f97ad"/>
    <stop offset="100%" stop-color="#1f6b80"/>
    </linearGradient>
    </defs>
    <rect x="0" y="0" width="800" height="220" fill="url(#camp-sky)"/>
    <circle cx="680" cy="55" r="30" fill="#ffdf8a" opacity="0.9"/>
    <path d="M0,150 Q200,110 400,140 T800,120 V220 H0 Z" fill="#7fae6b" opacity="0.9"/>
    <path d="M0,175 Q220,150 430,168 T800,155 V220 H0 Z" fill="#5f8f52"/>
    <g fill="#3d3226" opacity="0.9">
    <path d="M110,150 l24,-22 l24,22 Z"/>
    <path d="M170,158 l22,-20 l22,20 Z"/>
    <path d="M300,148 l24,-22 l24,22 Z"/>
    <path d="M540,152 l22,-20 l22,20 Z"/>
    </g>
    <g opacity="0.85">
    <rect x="600" y="120" width="10" height="45" fill="#e6e2d6"/>
    <rect x="622" y="120" width="10" height="45" fill="#e6e2d6"/>
    <rect x="644" y="120" width="10" height="45" fill="#e6e2d6"/>
    <rect x="592" y="112" width="70" height="10" fill="#d8d2bd"/>
    <path d="M592,112 L627,90 L662,112 Z" fill="#cfc7a8"/>
    </g>
    <rect x="0" y="196" width="800" height="24" fill="url(#camp-sea)"/>
    <path d="M0,200 q20,-6 40,0 t40,0 t40,0 t40,0 t40,0 t40,0 t40,0 t40,0 t40,0 t40,0 t40,0 t40,0 t40,0 t40,0 t40,0 t40,0 t40,0 t40,0 t40,0" fill="none" stroke="#eaf4e8" stroke-width="2" opacity="0.5"/>
    </svg>
    </div>
    """)
    st.markdown(svg_code, unsafe_allow_html=True)


def render_steel_background():
    st.markdown(
        textwrap.dedent("""\
        <style>
        .stApp {
            background:
                repeating-linear-gradient(0deg, rgba(255,255,255,0.015) 0px, rgba(255,255,255,0.015) 1px, transparent 1px, transparent 3px),
                radial-gradient(ellipse at top left, rgba(90,110,130,0.25), transparent 55%),
                radial-gradient(ellipse at bottom right, rgba(40,50,60,0.4), transparent 60%),
                linear-gradient(180deg, #0d1114 0%, #171c20 45%, #0d1114 100%) !important;
            background-attachment: fixed !important;
        }
        </style>
        """),
        unsafe_allow_html=True,
    )


def render_nexus_background():
    st.markdown(
        textwrap.dedent("""\
        <style>
        .stApp {
            background:
                radial-gradient(circle at 18% 22%, rgba(243,217,139,0.14), transparent 38%),
                radial-gradient(circle at 82% 28%, rgba(63,151,173,0.18), transparent 38%),
                radial-gradient(circle at 50% 85%, rgba(224,138,60,0.14), transparent 42%),
                radial-gradient(circle, rgba(255,255,255,0.9) 1px, transparent 1.5px) 0 0/160px 160px,
                radial-gradient(circle, rgba(255,255,255,0.55) 1px, transparent 1.5px) 55px 70px/190px 190px,
                radial-gradient(circle, rgba(255,255,255,0.4) 1px, transparent 1.5px) 100px 30px/220px 220px,
                linear-gradient(180deg, #05060f 0%, #0b0a1a 50%, #05060f 100%) !important;
            background-attachment: fixed !important;
        }
        </style>
        """),
        unsafe_allow_html=True,
    )


def render_nexus_emblem():
    svg_code = textwrap.dedent("""\
    <div style="display:flex; justify-content:center; margin: 0.2rem 0 1.6rem;">
    <svg width="210" height="170" viewBox="0 0 210 170" xmlns="http://www.w3.org/2000/svg">
    <g style="animation: nexus-rotate 34s linear infinite; transform-origin: 105px 92px;" opacity="0.5">
    <circle cx="105" cy="14" r="2" fill="#ffffff"/>
    <circle cx="197" cy="92" r="2" fill="#ffffff"/>
    <circle cx="105" cy="170" r="2" fill="#ffffff"/>
    <circle cx="13" cy="92" r="2" fill="#ffffff"/>
    </g>
    <g style="mix-blend-mode: screen;">
    <circle cx="72" cy="100" r="52" fill="#f3d98b" opacity="0.45"/>
    <circle cx="138" cy="100" r="52" fill="#3f97ad" opacity="0.45"/>
    <circle cx="105" cy="55" r="52" fill="#e08a3c" opacity="0.45"/>
    </g>
    <circle cx="72" cy="100" r="52" fill="none" stroke="#f3d98b" stroke-width="1.2" opacity="0.7"/>
    <circle cx="138" cy="100" r="52" fill="none" stroke="#7fc7d9" stroke-width="1.2" opacity="0.7"/>
    <circle cx="105" cy="55" r="52" fill="none" stroke="#e08a3c" stroke-width="1.2" opacity="0.7"/>
    <circle cx="105" cy="88" r="9" fill="#ffffff" opacity="0.9">
    <animate attributeName="opacity" values="0.6;1;0.6" dur="3s" repeatCount="indefinite"/>
    </circle>
    </svg>
    </div>
    <style>
    @keyframes nexus-rotate { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
    </style>
    """)
    st.markdown(svg_code, unsafe_allow_html=True)


def render_faction_wheel():
    svg_code = textwrap.dedent("""\
    <div style="display:flex; justify-content:center; margin: 0.4rem 0 1.6rem;">
    <svg width="190" height="190" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
    <defs>
    <radialGradient id="glow3" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="#d8dde2" stop-opacity="0.85"/>
    <stop offset="100%" stop-color="#d8dde2" stop-opacity="0"/>
    </radialGradient>
    </defs>
    <g stroke="#0d1114" stroke-width="2">
    <path d="M100,100 L100,10 L185.6,72.2 Z" fill="#6b6b70"/>
    <path d="M100,100 L185.6,72.2 L152.9,172.8 Z" fill="#1d3f6b"/>
    <path d="M100,100 L152.9,172.8 L47.1,172.8 Z" fill="#201010"/>
    <path d="M100,100 L47.1,172.8 L14.4,72.2 Z" fill="#8a4a12"/>
    <path d="M100,100 L14.4,72.2 L100,10 Z" fill="#3a3a3a"/>
    </g>
    <circle cx="65" cy="55" r="6" fill="none" stroke="#d8dde2" stroke-width="2" opacity="0.8"/>
    <ellipse cx="150" cy="105" rx="9" ry="5" fill="none" stroke="#9fc2ea" stroke-width="2" opacity="0.85"/>
    <circle cx="150" cy="105" r="2" fill="#9fc2ea"/>
    <path d="M92,155 q8,-16 0,-28 q10,4 8,18 q6,-6 4,4 q-6,4 -12,6 Z" fill="#e0995c" opacity="0.85"/>
    <path d="M35,140 q0,-16 12,-20 q4,10 -4,18 q8,-2 2,8 q-6,2 -10,-6 Z" fill="#e0c04a" opacity="0.85"/>
    <line x1="45" y1="60" x2="65" y2="60" stroke="#d8dde2" stroke-width="2" opacity="0.85"/>
    <line x1="55" y1="60" x2="55" y2="45" stroke="#d8dde2" stroke-width="2" opacity="0.85"/>
    <circle cx="100" cy="100" r="32" fill="url(#glow3)">
    <animate attributeName="r" values="28;34;28" dur="3.5s" repeatCount="indefinite"/>
    </circle>
    <circle cx="100" cy="100" r="24" fill="#0d1114" stroke="#d8dde2" stroke-width="2"/>
    <path d="M100,86 L110,100 L100,114 L90,100 Z" fill="none" stroke="#d8dde2" stroke-width="2"/>
    </svg>
    </div>
    """)
    st.markdown(svg_code, unsafe_allow_html=True)


def render_arena_background():
    st.markdown(
        textwrap.dedent("""\
        <style>
        .stApp {
            background:
                radial-gradient(ellipse at top, rgba(224,153,92,0.14), transparent 50%),
                radial-gradient(ellipse at bottom left, rgba(60,80,45,0.35), transparent 55%),
                linear-gradient(180deg, #0c0f08 0%, #161d10 45%, #0c0f08 100%) !important;
            background-attachment: fixed !important;
        }
        </style>
        """),
        unsafe_allow_html=True,
    )


def render_arena_compass():
    svg_code = textwrap.dedent("""\
    <div style="display:flex; justify-content:center; margin: 0.4rem 0 1.6rem;">
    <svg width="190" height="190" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
    <defs>
    <radialGradient id="glow4" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="#e0995c" stop-opacity="0.9"/>
    <stop offset="100%" stop-color="#e0995c" stop-opacity="0"/>
    </radialGradient>
    </defs>
    <g style="animation: arena-rotate 40s linear infinite; transform-origin: 100px 100px;">
    <circle cx="100" cy="100" r="88" fill="none" stroke="#6b7a4a" stroke-width="1.5" opacity="0.6"/>
    <g stroke="#6b7a4a" stroke-width="1.5" opacity="0.7">
    <line x1="100" y1="12" x2="100" y2="26"/>
    <line x1="100" y1="174" x2="100" y2="188"/>
    <line x1="12" y1="100" x2="26" y2="100"/>
    <line x1="174" y1="100" x2="188" y2="100"/>
    <line x1="37.6" y1="37.6" x2="47.5" y2="47.5"/>
    <line x1="152.5" y1="152.5" x2="162.4" y2="162.4"/>
    <line x1="37.6" y1="162.4" x2="47.5" y2="152.5"/>
    <line x1="152.5" y1="47.5" x2="162.4" y2="37.6"/>
    </g>
    </g>
    <circle cx="100" cy="100" r="34" fill="url(#glow4)">
    <animate attributeName="r" values="30;36;30" dur="3.5s" repeatCount="indefinite"/>
    </circle>
    <circle cx="100" cy="100" r="24" fill="#0c0f08" stroke="#e0995c" stroke-width="2"/>
    <path d="M100,84 L104,98 L118,100 L104,102 L100,116 L96,102 L82,100 L96,98 Z" fill="#e0995c"/>
    </svg>
    </div>
    <style>
    @keyframes arena-rotate { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
    </style>
    """)
    st.markdown(svg_code, unsafe_allow_html=True)


# ============================================================
# TYPEWRITER EFFECT for the question text
# (due varianti estetiche: pergamena e marmo)
# ============================================================
def render_typewriter_question(testo, stile="pergamena"):
    righe = max(2, -(-len(testo) // 50))
    altezza = 70 + righe * 30
    testo_js = json.dumps(testo)

    if stile == "pergamena":
        box_bg = """
            radial-gradient(circle at 15% 20%, rgba(139,110,60,0.18), transparent 40%),
            radial-gradient(circle at 85% 80%, rgba(90,60,20,0.22), transparent 45%),
            linear-gradient(135deg, #ecdcb2 0%, #e2cd9a 50%, #dcc389 100%)"""
        border_color = "#8a6a12"
        text_color = "#4a2f0e"
        font_import = "Cinzel+Decorative:wght@700"
        font_family = "'Cinzel Decorative', serif"
        text_transform = "none"
        letter_spacing = "normal"
    elif stile == "marmo":
        box_bg = """
            radial-gradient(circle at 20% 25%, rgba(150,160,170,0.35), transparent 45%),
            radial-gradient(circle at 80% 75%, rgba(120,130,145,0.3), transparent 45%),
            linear-gradient(135deg, #eef0ee 0%, #e3e6e6 50%, #d9dcdb 100%)"""
        border_color = "#a68a3c"
        text_color = "#1c2430"
        font_import = "Cinzel:wght@700"
        font_family = "'Cinzel', serif"
        text_transform = "uppercase"
        letter_spacing = "0.5px"
    elif stile == "acciaio":
        box_bg = """
            repeating-linear-gradient(135deg, rgba(255,255,255,0.02) 0px, rgba(255,255,255,0.02) 2px, transparent 2px, transparent 14px),
            linear-gradient(135deg, #2b3238 0%, #3a434b 50%, #4a555e 100%)"""
        border_color = "#6b7680"
        text_color = "#e4e8eb"
        font_import = "Barlow+Condensed:wght@700"
        font_family = "'Barlow Condensed', sans-serif"
        text_transform = "uppercase"
        letter_spacing = "1px"
    else:
        box_bg = """
            radial-gradient(circle at 20% 20%, rgba(90,110,70,0.35), transparent 45%),
            radial-gradient(circle at 80% 70%, rgba(60,50,30,0.4), transparent 50%),
            linear-gradient(135deg, #3a4230 0%, #2c3322 50%, #241f16 100%)"""
        border_color = "#6b7a4a"
        text_color = "#e6e4d4"
        font_import = "Bebas+Neue"
        font_family = "'Bebas Neue', sans-serif"
        text_transform = "none"
        letter_spacing = "0.5px"

    html_code = f"""
    <html>
    <head>
    <style>
        @import url('https://fonts.googleapis.com/css2?family={font_import}&display=swap');
        body {{ margin:0; background:transparent; }}
        .box {{
            background: {box_bg};
            border: 1px solid {border_color};
            outline: 6px solid #120d08;
            outline-offset: -12px;
            border-radius: 4px;
            padding: 1.4rem 1.6rem;
            box-shadow: inset 0 0 60px rgba(120,90,40,0.2);
            box-sizing: border-box;
        }}
        h3 {{
            font-family: {font_family};
            font-size: 1.1rem;
            color: {text_color};
            font-weight: 700;
            margin: 0;
            border-bottom: 1px solid {border_color};
            padding-bottom: 8px;
            line-height: 1.5;
            text-transform: {text_transform};
            letter-spacing: {letter_spacing};
        }}
        .cursor {{
            display: inline-block;
            animation: blink 0.8s step-end infinite;
            color: {text_color};
        }}
        @keyframes blink {{ 50% {{ opacity: 0; }} }}
    </style>
    </head>
    <body>
        <div class="box"><h3 id="q"></h3></div>
        <script>
            const testo = {testo_js};
            const el = document.getElementById('q');
            let i = 0;
            function scrivi() {{
                if (i <= testo.length) {{
                    el.innerHTML = testo.slice(0, i) + '<span class="cursor">|</span>';
                    i++;
                    setTimeout(scrivi, 16);
                }} else {{
                    el.innerHTML = testo;
                }}
            }}
            scrivi();
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=altezza)


# ============================================================
# SHAREABLE IMAGE GENERATION (generic for all quizzes)
# ============================================================
@st.cache_resource(show_spinner=False)
def carica_font():
    fonts = {}
    sorgenti = {
        "titolo_hp": "https://github.com/google/fonts/raw/main/ofl/cinzeldecorative/CinzelDecorative-Bold.ttf",
        "titolo_pj": "https://github.com/google/fonts/raw/main/ofl/cinzel/Cinzel[wght].ttf",
        "titolo_div": "https://github.com/google/fonts/raw/main/ofl/barlowcondensed/BarlowCondensed-Bold.ttf",
        "titolo_hg": "https://github.com/google/fonts/raw/main/ofl/bebasneue/BebasNeue-Regular.ttf",
        "corpo": "https://github.com/google/fonts/raw/main/ofl/ebgaramond/EBGaramond[wght].ttf",
        "corsivo": "https://github.com/google/fonts/raw/main/ofl/ebgaramond/EBGaramond-Italic[wght].ttf",
    }
    for nome, url in sorgenti.items():
        try:
            r = requests.get(url, timeout=6)
            r.raise_for_status()
            fonts[nome] = r.content
        except Exception:
            fonts[nome] = None
    return fonts


def _font(fonts_bytes, chiave, size):
    if fonts_bytes.get(chiave):
        try:
            return ImageFont.truetype(io.BytesIO(fonts_bytes[chiave]), size)
        except Exception:
            pass
    return ImageFont.load_default()


def genera_immagine_condivisione(nome_entita, info, eyebrow_text, footer_text, titolo_font_key="titolo_hp"):
    W, H = 1080, 1080
    top = info["rgb_top"]
    bottom = info["rgb_bottom"]
    img = Image.new("RGB", (W, H), top)
    draw = ImageDraw.Draw(img)

    for y in range(H):
        t = y / H
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    margine = 46
    draw.rectangle([margine, margine, W - margine, H - margine], outline=(243, 217, 139), width=6)
    draw.rectangle(
        [margine + 14, margine + 14, W - margine - 14, H - margine - 14],
        outline=(243, 217, 139, 120), width=1,
    )

    fonts_bytes = carica_font()
    f_eyebrow = _font(fonts_bytes, "corsivo", 32)
    f_titolo = _font(fonts_bytes, titolo_font_key, 88)
    f_desc = _font(fonts_bytes, "corpo", 34)
    f_footer = _font(fonts_bytes, "corsivo", 26)

    def testo_centrato(testo, y, font, fill=(255, 255, 255)):
        bbox = draw.textbbox((0, 0), testo, font=font)
        larghezza = bbox[2] - bbox[0]
        draw.text(((W - larghezza) / 2, y), testo, font=font, fill=fill)

    testo_centrato(eyebrow_text, 165, f_eyebrow, (255, 255, 255))
    testo_centrato(nome_entita.upper(), 225, f_titolo, (255, 255, 255))

    testo_avvolto = textwrap.fill(info["descrizione"], width=46)
    y_desc = 410
    for riga in testo_avvolto.split("\n"):
        testo_centrato(riga, y_desc, f_desc, (255, 255, 255))
        y_desc += 46

    dettagli = info["dettagli"][:4]
    padding_box = 22
    gap_label_valore = 6
    gap_tra_righe = 16

    def altezza_testo(testo, font):
        bbox = draw.textbbox((0, 0), testo, font=font)
        return bbox[3] - bbox[1]

    altezze_righe = []
    for label, valore in dettagli:
        h = altezza_testo(label.upper(), f_footer) + gap_label_valore + altezza_testo(valore, f_desc)
        altezze_righe.append(h)

    box_h = padding_box * 2 + sum(altezze_righe) + gap_tra_righe * (len(dettagli) - 1)
    y_box = y_desc + 60
    draw.rectangle([120, y_box, W - 120, y_box + box_h], outline=(255, 255, 255, 150), width=2)

    y_cursor = y_box + padding_box
    for i, (label, valore) in enumerate(dettagli):
        draw.text((150, y_cursor), label.upper(), font=f_footer, fill=(255, 255, 255, 200))
        y_valore = y_cursor + altezza_testo(label.upper(), f_footer) + gap_label_valore
        draw.text((150, y_valore), valore, font=f_desc, fill=(255, 255, 255))
        y_fine_riga = y_valore + altezza_testo(valore, f_desc)
        if i < len(dettagli) - 1:
            y_line = y_fine_riga + gap_tra_righe / 2
            draw.line(
                [(150, y_line), (W - 150, y_line)],
                fill=(255, 255, 255, 60), width=1,
            )
        y_cursor = y_fine_riga + gap_tra_righe

    testo_centrato(footer_text, H - 110, f_footer, (255, 255, 255))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


# ============================================================
# GENERIC QUIZ ENGINE (used by all quizzes)
# ============================================================
def init_state(prefix, entities):
    if f"{prefix}_iniziato" not in st.session_state:
        st.session_state[f"{prefix}_iniziato"] = False
    if f"{prefix}_domanda" not in st.session_state:
        st.session_state[f"{prefix}_domanda"] = 0
    if f"{prefix}_punteggi" not in st.session_state:
        st.session_state[f"{prefix}_punteggi"] = {nome: 0.0 for nome in entities}
    if f"{prefix}_finito" not in st.session_state:
        st.session_state[f"{prefix}_finito"] = False


def reset_quiz(prefix, entities, questions):
    st.session_state[f"{prefix}_iniziato"] = False
    st.session_state[f"{prefix}_domanda"] = 0
    st.session_state[f"{prefix}_punteggi"] = {nome: 0.0 for nome in entities}
    st.session_state[f"{prefix}_ordine"] = list(range(len(questions)))
    random.shuffle(st.session_state[f"{prefix}_ordine"])
    st.session_state[f"{prefix}_finito"] = False


def rispondi(prefix, questions, punti_assegnati):
    for nome, punti in punti_assegnati.items():
        st.session_state[f"{prefix}_punteggi"][nome] += punti
    st.session_state[f"{prefix}_domanda"] += 1
    if st.session_state[f"{prefix}_domanda"] >= len(questions):
        st.session_state[f"{prefix}_finito"] = True


def render_radar(labels, valori):
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=valori + [valori[0]],
        theta=labels + [labels[0]],
        fill='toself',
        fillcolor='rgba(201,162,39,0.25)',
        line=dict(color='#f3d98b', width=2),
        marker=dict(size=6, color='#f3d98b'),
    ))
    fig.update_layout(
        polar=dict(
            bgcolor='rgba(0,0,0,0)',
            radialaxis=dict(visible=True, showticklabels=False, gridcolor='rgba(255,255,255,0.15)'),
            angularaxis=dict(color='#e9d9ad', gridcolor='rgba(255,255,255,0.15)'),
        ),
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e9d9ad', family='EB Garamond'),
        margin=dict(l=40, r=40, t=20, b=20),
        height=380,
    )
    st.plotly_chart(fig, use_container_width=True)


# ============================================================
# QUIZ 1 — HOGWARTS SORTING
# ============================================================
def render_hogwarts():
    prefix = "hp"
    init_state(prefix, HOUSES)
    if f"{prefix}_ordine" not in st.session_state:
        st.session_state[f"{prefix}_ordine"] = list(range(len(QUESTIONS_HP)))
        random.shuffle(st.session_state[f"{prefix}_ordine"])

    if st.button("← Back to menu"):
        st.session_state.pagina = "menu"
        st.rerun()

    st.markdown('<div class="hat-title">🎩 The Sorting Hat 🎩</div>', unsafe_allow_html=True)
    st.markdown(
    '<div class="subtitle">"Hmm... difficult, very difficult. Let\'s see what you\'re truly made of..."</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state[f"{prefix}_iniziato"]:
        render_crest()
        st.markdown(
            textwrap.dedent("""\
            <div class="parchment">
            <h3>Before the Sorting</h3>
            Answer 12 situations inspired by the world of Hogwarts honestly.
            There are no right or wrong answers: the Hat looks past words,
            straight into your nature. In the end you'll discover which house
            suits you best, with your full profile across all four — and you
            can download your card to share.
            </div>
            """),
            unsafe_allow_html=True,
        )
        if st.button("🕯️ Put On the Hat", use_container_width=True):
            st.session_state[f"{prefix}_iniziato"] = True
            st.rerun()

    elif not st.session_state[f"{prefix}_finito"]:
        idx = st.session_state[f"{prefix}_ordine"][st.session_state[f"{prefix}_domanda"]]
        domanda = QUESTIONS_HP[idx]

        st.markdown(
            f'<div class="qcounter">Question {st.session_state[f"{prefix}_domanda"] + 1} of {len(QUESTIONS_HP)}</div>',
            unsafe_allow_html=True,
        )
        st.progress(st.session_state[f"{prefix}_domanda"] / len(QUESTIONS_HP))
        render_typewriter_question(domanda["domanda"], stile="pergamena")

        opzioni = list(domanda["opzioni"])
        random.Random(idx + 100).shuffle(opzioni)
        for testo_opzione, punti in opzioni:
            if st.button(testo_opzione, key=f"{prefix}_{idx}_{testo_opzione}"):
                rispondi(prefix, QUESTIONS_HP, punti)
                st.rerun()

    else:
        punteggi = st.session_state[f"{prefix}_punteggi"]
        vincitore = max(punteggi, key=punteggi.get)
        info = HOUSES[vincitore]

        st.balloons()

        dettagli_html = "".join(
            f'<div class="fact-item"><span class="fact-label">{label}</span><span class="fact-value">{valore}</span></div>'
            for label, valore in info["dettagli"]
        )

        st.markdown(
            textwrap.dedent(f"""\
            <div class="result-card" style="background:{info['gradiente']};">
            <div style="font-size:3.2rem;">{info['emoji']}</div>
            <div class="result-house">{vincitore}</div>
            <div class="result-desc">{info['descrizione']}</div>
            <div class="fact-grid">{dettagli_html}</div>
            </div>
            """),
            unsafe_allow_html=True,
        )

        st.write("")
        with st.spinner("Preparing your shareable card..."):
            buf = genera_immagine_condivisione(
                vincitore, info,
                "THE SORTING HAT PLACED ME IN",
                "HOGWARTS SORTING",
                titolo_font_key="titolo_hp",
            )
        col1, col2 = st.columns([1, 1])
        with col1:
            st.image(buf, use_container_width=True)
        with col2:
            st.write("")
            st.write("Download your card and share it wherever you like.")
            st.download_button(
                "📥 Download the card", data=buf,
                file_name=f"smistamento_{vincitore.lower()}.png",
                mime="image/png", use_container_width=True,
            )

        st.write("")
        st.markdown('<div class="parchment"><h3>Your profile across the four houses</h3></div>', unsafe_allow_html=True)
        case = list(HOUSES.keys())
        render_radar(case, [punteggi[c] for c in case])

        for casa, punti in sorted(punteggi.items(), key=lambda x: -x[1]):
            pct = punti / len(QUESTIONS_HP)
            st.write(f"{HOUSES[casa]['emoji']} **{casa}** — {punti:g} points")
            st.progress(min(pct, 1.0))

        st.write("")
        if st.button("🔄 Redo the Sorting", use_container_width=True):
            reset_quiz(prefix, HOUSES, QUESTIONS_HP)
            st.rerun()


# ============================================================
# QUIZ 2 — WHO IS YOUR GODLY PARENT?
# ============================================================
def render_percy():
    prefix = "pj"
    init_state(prefix, GODS)
    if f"{prefix}_ordine" not in st.session_state:
        st.session_state[f"{prefix}_ordine"] = list(range(len(QUESTIONS_PJ)))
        random.shuffle(st.session_state[f"{prefix}_ordine"])

    if st.button("← Back to menu"):
        st.session_state.pagina = "menu"
        st.rerun()

    render_light_background()

    st.markdown('<div class="camp-title">⚡ CAMP HALF-BLOOD ⚡</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="camp-subtitle">"The gods of Olympus are watching... what blood truly runs through your veins?"</div>',
        unsafe_allow_html=True,
    )
    render_camp_banner()

    if not st.session_state[f"{prefix}_iniziato"]:
        render_olympus_emblem()
        st.markdown(
            textwrap.dedent("""\
            <div class="marble">
            <h3>Before the Oracle's Answer</h3>
            Answer 12 situations inspired by Camp Half-Blood honestly.
            There are no right or wrong answers: the gods look straight into
            your true nature. In the end you'll discover which Olympian god
            is your godly parent, with your full profile — and you can
            download your card to share.
            </div>
            """),
            unsafe_allow_html=True,
        )
        if st.button("⚡ Consult the Oracle", use_container_width=True):
            st.session_state[f"{prefix}_iniziato"] = True
            st.rerun()

    elif not st.session_state[f"{prefix}_finito"]:
        idx = st.session_state[f"{prefix}_ordine"][st.session_state[f"{prefix}_domanda"]]
        domanda = QUESTIONS_PJ[idx]

        st.markdown(
            f'<div class="qcounter oly">Question {st.session_state[f"{prefix}_domanda"] + 1} of {len(QUESTIONS_PJ)}</div>',
            unsafe_allow_html=True,
        )
        st.progress(st.session_state[f"{prefix}_domanda"] / len(QUESTIONS_PJ))
        render_typewriter_question(domanda["domanda"], stile="marmo")

        opzioni = list(domanda["opzioni"])
        random.Random(idx + 200).shuffle(opzioni)
        for testo_opzione, punti in opzioni:
            if st.button(testo_opzione, key=f"{prefix}_{idx}_{testo_opzione}"):
                rispondi(prefix, QUESTIONS_PJ, punti)
                st.rerun()

    else:
        punteggi = st.session_state[f"{prefix}_punteggi"]
        vincitore = max(punteggi, key=punteggi.get)
        info = GODS[vincitore]

        st.balloons()

        dettagli_html = "".join(
            f'<div class="fact-item"><span class="fact-label oly">{label}</span><span class="fact-value">{valore}</span></div>'
            for label, valore in info["dettagli"]
        )

        st.markdown(
            textwrap.dedent(f"""\
            <div class="result-card" style="background:{info['gradiente']};">
            <div style="font-size:3.2rem;">{info['emoji']}</div>
            <div class="result-house oly">{vincitore}</div>
            <div class="result-desc oly">{info['descrizione']}</div>
            <div class="fact-grid">{dettagli_html}</div>
            </div>
            """),
            unsafe_allow_html=True,
        )

        st.write("")
        with st.spinner("Preparing your shareable card..."):
            buf = genera_immagine_condivisione(
                vincitore, info,
                "THE ORACLE HAS SPOKEN: YOU ARE A CHILD OF",
                "WHO IS YOUR GODLY PARENT?",
                titolo_font_key="titolo_pj",
            )
        col1, col2 = st.columns([1, 1])
        with col1:
            st.image(buf, use_container_width=True)
        with col2:
            st.write("")
            st.write("Download your card and share it wherever you like.")
            st.download_button(
                "📥 Download the card", data=buf,
                file_name=f"genitore_divino_{vincitore.lower()}.png",
                mime="image/png", use_container_width=True,
            )

        st.write("")
        st.markdown('<div class="marble"><h3>Your profile among the gods</h3></div>', unsafe_allow_html=True)
        divinita = list(GODS.keys())
        render_radar(divinita, [punteggi[d] for d in divinita])

        for dio, punti in sorted(punteggi.items(), key=lambda x: -x[1]):
            pct = punti / len(QUESTIONS_PJ)
            st.write(f"{GODS[dio]['emoji']} **{dio}** — {punti:g} points")
            st.progress(min(pct, 1.0))

        st.write("")
        if st.button("🔄 Consult the Oracle Again", use_container_width=True):
            reset_quiz(prefix, GODS, QUESTIONS_PJ)
            st.rerun()


# ============================================================
# QUIZ 3 — WHICH FACTION DO YOU BELONG TO?
# ============================================================
def render_divergent():
    prefix = "div"
    init_state(prefix, DIVERGENT)
    if f"{prefix}_ordine" not in st.session_state:
        st.session_state[f"{prefix}_ordine"] = list(range(len(QUESTIONS_DIV)))
        random.shuffle(st.session_state[f"{prefix}_ordine"])

    if st.button("← Back to menu"):
        st.session_state.pagina = "menu"
        st.rerun()

    render_steel_background()

    st.markdown('<div class="steel-title">Which Faction Do You Belong To?</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="steel-subtitle">"Faction before blood. But who are you, really, when no one\'s watching?"</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state[f"{prefix}_iniziato"]:
        render_faction_wheel()
        st.markdown(
            textwrap.dedent("""\
            <div class="steel">
            <h3>Before the Choosing Ceremony</h3>
            Answer 10 situations inspired by the society of the five factions
            honestly. There are no right or wrong answers: your true nature
            always comes out. In the end you'll discover which faction you'd
            belong to, with your full profile — and you can download your
            card to share.
            </div>
            """),
            unsafe_allow_html=True,
        )
        if st.button("🗡️ Face the Ceremony", use_container_width=True):
            st.session_state[f"{prefix}_iniziato"] = True
            st.rerun()

    elif not st.session_state[f"{prefix}_finito"]:
        idx = st.session_state[f"{prefix}_ordine"][st.session_state[f"{prefix}_domanda"]]
        domanda = QUESTIONS_DIV[idx]

        st.markdown(
            f'<div class="qcounter steel">Question {st.session_state[f"{prefix}_domanda"] + 1} of {len(QUESTIONS_DIV)}</div>',
            unsafe_allow_html=True,
        )
        st.progress(st.session_state[f"{prefix}_domanda"] / len(QUESTIONS_DIV))
        render_typewriter_question(domanda["domanda"], stile="acciaio")

        opzioni = list(domanda["opzioni"])
        random.Random(idx + 300).shuffle(opzioni)
        for testo_opzione, punti in opzioni:
            if st.button(testo_opzione, key=f"{prefix}_{idx}_{testo_opzione}"):
                rispondi(prefix, QUESTIONS_DIV, punti)
                st.rerun()

    else:
        punteggi = st.session_state[f"{prefix}_punteggi"]
        vincitore = max(punteggi, key=punteggi.get)
        info = DIVERGENT[vincitore]

        st.balloons()

        dettagli_html = "".join(
            f'<div class="fact-item"><span class="fact-label steel">{label}</span><span class="fact-value">{valore}</span></div>'
            for label, valore in info["dettagli"]
        )

        st.markdown(
            textwrap.dedent(f"""\
            <div class="result-card" style="background:{info['gradiente']};">
            <div style="font-size:3.2rem;">{info['emoji']}</div>
            <div class="result-house steel">{vincitore}</div>
            <div class="result-desc steel">{info['descrizione']}</div>
            <div class="fact-grid">{dettagli_html}</div>
            </div>
            """),
            unsafe_allow_html=True,
        )

        st.write("")
        with st.spinner("Preparing your shareable card..."):
            buf = genera_immagine_condivisione(
                vincitore, info,
                "THE CHOOSING CEREMONY REVEALED",
                "WHICH FACTION DO YOU BELONG TO?",
                titolo_font_key="titolo_div",
            )
        col1, col2 = st.columns([1, 1])
        with col1:
            st.image(buf, use_container_width=True)
        with col2:
            st.write("")
            st.write("Download your card and share it wherever you like.")
            st.download_button(
                "📥 Download the card", data=buf,
                file_name=f"fazione_{vincitore.lower()}.png",
                mime="image/png", use_container_width=True,
            )

        st.write("")
        st.markdown('<div class="steel"><h3>Your profile across the factions</h3></div>', unsafe_allow_html=True)
        fazioni = list(DIVERGENT.keys())
        render_radar(fazioni, [punteggi[f] for f in fazioni])

        for fazione, punti in sorted(punteggi.items(), key=lambda x: -x[1]):
            pct = punti / len(QUESTIONS_DIV)
            st.write(f"{DIVERGENT[fazione]['emoji']} **{fazione}** — {punti:g} points")
            st.progress(min(pct, 1.0))

        st.write("")
        if st.button("🔄 Redo the Ceremony", use_container_width=True):
            reset_quiz(prefix, DIVERGENT, QUESTIONS_DIV)
            st.rerun()


# ============================================================
# QUIZ 4 — WHICH DISTRICT DO YOU BELONG TO?
# ============================================================
def render_hunger_games():
    prefix = "hg"
    init_state(prefix, DISTRICTS)
    if f"{prefix}_ordine" not in st.session_state:
        st.session_state[f"{prefix}_ordine"] = list(range(len(QUESTIONS_HG)))
        random.shuffle(st.session_state[f"{prefix}_ordine"])

    if st.button("← Back to menu"):
        st.session_state.pagina = "menu"
        st.rerun()

    render_arena_background()

    st.markdown('<div class="arena-title">Which District Do You Belong To?</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="arena-subtitle">"May fortune find you when it matters most... but who are you, really, when survival is on the line?"</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state[f"{prefix}_iniziato"]:
        render_arena_compass()
        st.markdown(
            textwrap.dedent("""\
            <div class="canvas">
            <h3>Before the Reaping</h3>
            Answer 12 situations inspired by the arena and Panem honestly.
            There are no right or wrong answers: your true nature always
            comes out when everything is at stake. In the end you'll discover
            which district you'd belong to, with your full profile — and you
            can download your card to share.
            </div>
            """),
            unsafe_allow_html=True,
        )
        if st.button("🔥 Face the Reaping", use_container_width=True):
            st.session_state[f"{prefix}_iniziato"] = True
            st.rerun()

    elif not st.session_state[f"{prefix}_finito"]:
        idx = st.session_state[f"{prefix}_ordine"][st.session_state[f"{prefix}_domanda"]]
        domanda = QUESTIONS_HG[idx]

        st.markdown(
            f'<div class="qcounter arena">Question {st.session_state[f"{prefix}_domanda"] + 1} of {len(QUESTIONS_HG)}</div>',
            unsafe_allow_html=True,
        )
        st.progress(st.session_state[f"{prefix}_domanda"] / len(QUESTIONS_HG))
        render_typewriter_question(domanda["domanda"], stile="arena")

        opzioni = list(domanda["opzioni"])
        random.Random(idx + 400).shuffle(opzioni)
        for testo_opzione, punti in opzioni:
            if st.button(testo_opzione, key=f"{prefix}_{idx}_{testo_opzione}"):
                rispondi(prefix, QUESTIONS_HG, punti)
                st.rerun()

    else:
        punteggi = st.session_state[f"{prefix}_punteggi"]
        vincitore = max(punteggi, key=punteggi.get)
        info = DISTRICTS[vincitore]

        st.balloons()

        dettagli_html = "".join(
            f'<div class="fact-item"><span class="fact-label arena">{label}</span><span class="fact-value">{valore}</span></div>'
            for label, valore in info["dettagli"]
        )

        st.markdown(
            textwrap.dedent(f"""\
            <div class="result-card" style="background:{info['gradiente']};">
            <div style="font-size:3.2rem;">{info['emoji']}</div>
            <div class="result-house arena">{vincitore}</div>
            <div class="result-desc arena">{info['descrizione']}</div>
            <div class="fact-grid">{dettagli_html}</div>
            </div>
            """),
            unsafe_allow_html=True,
        )

        st.write("")
        with st.spinner("Preparing your shareable card..."):
            buf = genera_immagine_condivisione(
                vincitore, info,
                "THE REAPING HAS SPOKEN: YOU BELONG TO",
                "WHICH DISTRICT DO YOU BELONG TO?",
                titolo_font_key="titolo_hg",
            )
        col1, col2 = st.columns([1, 1])
        with col1:
            st.image(buf, use_container_width=True)
        with col2:
            st.write("")
            st.write("Download your card and share it wherever you like.")
            st.download_button(
                "📥 Download the card", data=buf,
                file_name=f"{vincitore.lower().replace(' ', '_')}.png",
                mime="image/png", use_container_width=True,
            )

        st.write("")
        st.markdown('<div class="canvas"><h3>Your profile across the districts</h3></div>', unsafe_allow_html=True)
        distretti = list(DISTRICTS.keys())
        render_radar(distretti, [punteggi[d] for d in distretti])

        for distretto, punti in sorted(punteggi.items(), key=lambda x: -x[1]):
            pct = punti / len(QUESTIONS_HG)
            st.write(f"{DISTRICTS[distretto]['emoji']} **{distretto}** — {punti:g} points")
            st.progress(min(pct, 1.0))

        st.write("")
        if st.button("🔄 Redo the Reaping", use_container_width=True):
            reset_quiz(prefix, DISTRICTS, QUESTIONS_HG)
            st.rerun()


# ============================================================
# WORLD SELECTOR (shared by Creator and Maps)
# ============================================================
def render_selettore_mondo(session_key):
    opzioni = [
        ("hogwarts", "🎩", "Hogwarts"),
        ("percy", "⚡", "Camp Half-Blood"),
        ("divergent", "⚖️", "Factions"),
        ("hunger", "🔥", "Panem"),
    ]
    col1, col2 = st.columns(2)
    for i, (chiave, emoji, nome) in enumerate(opzioni):
        col = col1 if i % 2 == 0 else col2
        with col:
            if st.button(f"{emoji}  {nome}", key=f"{session_key}_{chiave}", use_container_width=True):
                st.session_state[session_key] = chiave
                st.rerun()


# ============================================================
# IMAGE GENERATION — CHARACTER SHEET
# ============================================================
def genera_immagine_personaggio(r, dati, info_aff):
    W, H = 1080, 1080
    top, bottom = info_aff["rgb_top"], info_aff["rgb_bottom"]
    img = Image.new("RGB", (W, H), top)
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        col = tuple(int(top[c] + (bottom[c] - top[c]) * t) for c in range(3))
        draw.line([(0, y), (W, y)], fill=col)

    margine = 46
    draw.rectangle([margine, margine, W - margine, H - margine], outline=(243, 217, 139), width=6)
    draw.rectangle(
        [margine + 14, margine + 14, W - margine - 14, H - margine - 14],
        outline=(243, 217, 139, 120), width=1,
    )

    fonts_bytes = carica_font()
    f_eyebrow = _font(fonts_bytes, "corsivo", 30)
    f_titolo = _font(fonts_bytes, dati["font_titolo"], 80)
    f_desc = _font(fonts_bytes, "corpo", 32)
    f_footer = _font(fonts_bytes, "corsivo", 24)

    def testo_centrato(testo, y, font, fill=(255, 255, 255)):
        bbox = draw.textbbox((0, 0), testo, font=font)
        larghezza = bbox[2] - bbox[0]
        draw.text(((W - larghezza) / 2, y), testo, font=font, fill=fill)

    def altezza_testo(testo, font):
        bbox = draw.textbbox((0, 0), testo, font=font)
        return bbox[3] - bbox[1]

    testo_centrato(dati["eyebrow"], 150, f_eyebrow, (255, 255, 255))
    testo_centrato(r["nome"].upper(), 205, f_titolo, (255, 255, 255))
    testo_centrato(f"Affiliation: {r['affiliazione']}", 320, f_desc, (255, 255, 255))

    dettagli = [
        ("Traits", ", ".join(r["tratti"])),
        ("Item", r["oggetto"]),
        ("Ally", r["alleato"]),
    ]
    dettagli_wrap = [(label, textwrap.wrap(valore, width=40) or [""]) for label, valore in dettagli]

    padding_box, gap_label_valore, gap_tra_righe = 22, 6, 14
    altezze_righe = []
    for label, righe_valore in dettagli_wrap:
        h = altezza_testo(label.upper(), f_footer) + gap_label_valore
        h += sum(altezza_testo(r_ or "Ag", f_desc) + 8 for r_ in righe_valore)
        altezze_righe.append(h)

    box_h = padding_box * 2 + sum(altezze_righe) + gap_tra_righe * (len(dettagli_wrap) - 1)
    y_box = 400
    draw.rectangle([120, y_box, W - 120, y_box + box_h], outline=(255, 255, 255, 150), width=2)

    y_cursor = y_box + padding_box
    for i, (label, righe_valore) in enumerate(dettagli_wrap):
        draw.text((150, y_cursor), label.upper(), font=f_footer, fill=(255, 255, 255, 200))
        y_val = y_cursor + altezza_testo(label.upper(), f_footer) + gap_label_valore
        for riga in righe_valore:
            draw.text((150, y_val), riga, font=f_desc, fill=(255, 255, 255))
            y_val += altezza_testo(riga or "Ag", f_desc) + 8
        if i < len(dettagli_wrap) - 1:
            y_line = y_val + gap_tra_righe / 2
            draw.line([(150, y_line), (W - 150, y_line)], fill=(255, 255, 255, 60), width=1)
        y_cursor = y_val + gap_tra_righe

    testo_centrato(dati["titolo"].upper(), H - 110, f_footer, (255, 255, 255))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


# ============================================================
# TOOL 1 — CHARACTER CREATOR
# ============================================================
def render_creator():
    if st.button("← Back to menu"):
        st.session_state.pagina = "menu"
        st.session_state.pop("creator_mondo", None)
        st.session_state.pop("creator_risultato", None)
        st.rerun()

    st.markdown('<div class="hat-title" style="font-size:2.3rem;">🪄 Character Creator</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Choose the world where you want to bring your character to life</div>', unsafe_allow_html=True)

    mondo = st.session_state.get("creator_mondo")
    if not mondo:
        render_selettore_mondo("creator_mondo")
        return

    dati = CREATOR_DATA[mondo]

    if "creator_risultato" not in st.session_state:
        st.markdown(f'<div class="parchment"><h3>{dati["titolo"]}</h3></div>', unsafe_allow_html=True)
        nome_pg = st.text_input("What's your character's name?", placeholder="Type a name...")
        tratti_scelti = st.multiselect("Choose up to 2 character traits", dati["tratti"], max_selections=2)

        if st.button("✨ Generate the character", use_container_width=True):
            if not nome_pg.strip():
                st.warning("Give your character a name before proceeding!")
            elif not tratti_scelti:
                st.warning("Choose at least one character trait!")
            else:
                st.session_state.creator_risultato = {
                    "nome": html.escape(nome_pg.strip())[:40],
                    "tratti": tratti_scelti,
                    "affiliazione": random.choice(list(dati["entita"].keys())),
                    "oggetto": random.choice(dati["oggetti"]),
                    "alleato": random.choice(dati["alleati"]),
                }
                st.rerun()

        if st.button("🔄 Change world", use_container_width=True):
            st.session_state.pop("creator_mondo", None)
            st.rerun()

    else:
        r = st.session_state.creator_risultato
        info_aff = dati["entita"][r["affiliazione"]]
        st.balloons()

        dettagli_html = "".join(
            f'<div class="fact-item"><span class="fact-label">Trait</span><span class="fact-value">{t}</span></div>'
            for t in r["tratti"]
        )
        st.markdown(
            textwrap.dedent(f"""\
            <div class="result-card" style="background:{info_aff['gradiente']};">
            <div style="font-size:2.4rem;">{info_aff['emoji']}</div>
            <div class="result-house">{r['nome']}</div>
            <div class="result-desc">Affiliation: {r['affiliazione']}</div>
            <div class="fact-grid">
            {dettagli_html}
            <div class="fact-item span2"><span class="fact-label">Item</span><span class="fact-value">{r['oggetto']}</span></div>
            <div class="fact-item span2"><span class="fact-label">Ally</span><span class="fact-value">{r['alleato']}</span></div>
            </div>
            </div>
            """),
            unsafe_allow_html=True,
        )

        st.write("")
        with st.spinner("Preparing the character sheet..."):
            buf = genera_immagine_personaggio(r, dati, info_aff)
        col1, col2 = st.columns([1, 1])
        with col1:
            st.image(buf, use_container_width=True)
        with col2:
            st.write("")
            st.write("Download your character sheet and share it wherever you like.")
            nome_file = re.sub(r"[^a-z0-9]+", "_", r["nome"].lower()).strip("_") or "personaggio"
            st.download_button(
                "📥 Download the sheet", data=buf,
                file_name=f"{nome_file}.png", mime="image/png", use_container_width=True,
            )

        st.write("")
        if st.button("🔄 Create another character", use_container_width=True):
            st.session_state.pop("creator_risultato", None)
            st.rerun()


# ============================================================
# TOOL 2 — SURVIVAL IN THE ARENA (Hunger Games)
# ============================================================
def render_survival():
    prefix = "surv"

    if st.button("← Back to menu"):
        st.session_state.pagina = "menu"
        st.rerun()

    render_arena_background()
    st.markdown('<div class="arena-title">Survival in the Arena</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="arena-subtitle">"May fortune find you when it matters most... but how long will you really last?"</div>',
        unsafe_allow_html=True,
    )

    for chiave, default in [
        ("iniziato", False), ("giorno", 0), ("salute", 100),
        ("provviste", 60), ("log", []), ("finito", False), ("esito", None),
    ]:
        if f"{prefix}_{chiave}" not in st.session_state:
            st.session_state[f"{prefix}_{chiave}"] = default

    def reset_survival():
        st.session_state[f"{prefix}_iniziato"] = False
        st.session_state[f"{prefix}_giorno"] = 0
        st.session_state[f"{prefix}_salute"] = 100
        st.session_state[f"{prefix}_provviste"] = 60
        st.session_state[f"{prefix}_log"] = []
        st.session_state[f"{prefix}_finito"] = False
        st.session_state[f"{prefix}_esito"] = None

    if not st.session_state[f"{prefix}_iniziato"]:
        render_arena_compass()
        st.markdown(
            textwrap.dedent("""\
            <div class="canvas">
            <h3>Before the Gong</h3>
            You'll face 6 days in the arena. Every choice affects your health
            and your supplies: if your health drops to zero, your journey
            ends there. Survive to the end and you'll be the winner of the
            Games.
            </div>
            """),
            unsafe_allow_html=True,
        )
        if st.button("🔥 Enter the Arena", use_container_width=True):
            st.session_state[f"{prefix}_iniziato"] = True
            st.rerun()

    elif not st.session_state[f"{prefix}_finito"]:
        giorno_idx = st.session_state[f"{prefix}_giorno"]
        giorno = GIORNI_ARENA[giorno_idx]

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f'<div class="qcounter arena">Day {giorno_idx + 1} of {len(GIORNI_ARENA)}</div>', unsafe_allow_html=True)
            st.write(f"❤️ Health: {st.session_state[f'{prefix}_salute']}")
            st.progress(max(st.session_state[f"{prefix}_salute"], 0) / 100)
        with col_b:
            st.write("")
            st.write(f"🎒 Supplies: {st.session_state[f'{prefix}_provviste']}")
            st.progress(max(min(st.session_state[f"{prefix}_provviste"], 100), 0) / 100)

        render_typewriter_question(giorno["situazione"], stile="arena")

        for testo_scelta, effetti in giorno["scelte"]:
            if st.button(testo_scelta, key=f"{prefix}_{giorno_idx}_{testo_scelta}"):
                nuova_salute = max(0, min(100, st.session_state[f"{prefix}_salute"] + effetti["salute"]))
                nuove_provviste = max(0, min(100, st.session_state[f"{prefix}_provviste"] + effetti["provviste"]))
                st.session_state[f"{prefix}_salute"] = nuova_salute
                st.session_state[f"{prefix}_provviste"] = nuove_provviste
                st.session_state[f"{prefix}_log"].append((giorno_idx + 1, testo_scelta))
                if nuova_salute <= 0:
                    st.session_state[f"{prefix}_finito"] = True
                    st.session_state[f"{prefix}_esito"] = "eliminato"
                elif giorno_idx + 1 >= len(GIORNI_ARENA):
                    st.session_state[f"{prefix}_finito"] = True
                    st.session_state[f"{prefix}_esito"] = "vincitore"
                else:
                    st.session_state[f"{prefix}_giorno"] += 1
                st.rerun()

    else:
        esito = st.session_state[f"{prefix}_esito"]
        giorni_sopravvissuti = len(st.session_state[f"{prefix}_log"])

        if esito == "vincitore":
            titolo_esito = "🏆 You Are the Winner of the Games!"
            desc_esito = (
                f"You made it through all {len(GIORNI_ARENA)} days in the arena and returned home. "
                "Your District celebrates your return."
            )
            gradiente_esito = "linear-gradient(135deg, #4a3b00 0%, #b89b1a 50%, #ffdb00 100%)"
            st.balloons()
        else:
            titolo_esito = "💀 You Were Eliminated"
            desc_esito = (
                f"You survived {giorni_sopravvissuti} out of {len(GIORNI_ARENA)} days "
                "before the arena got the better of you."
            )
            gradiente_esito = "linear-gradient(135deg, #280404 0%, #6e0f0f 50%, #961414 100%)"

        st.markdown(
            textwrap.dedent(f"""\
            <div class="result-card" style="background:{gradiente_esito};">
            <div style="font-size:3rem;">{'🏆' if esito == 'vincitore' else '💀'}</div>
            <div class="result-house arena">{titolo_esito}</div>
            <div class="result-desc arena">{desc_esito}</div>
            </div>
            """),
            unsafe_allow_html=True,
        )

        st.write("")
        st.markdown('<div class="canvas"><h3>Your journey through the arena</h3></div>', unsafe_allow_html=True)
        for giorno_n, scelta in st.session_state[f"{prefix}_log"]:
            st.write(f"**Day {giorno_n}:** {scelta}")

        st.write("")
        if st.button("🔄 Re-enter the Arena", use_container_width=True):
            reset_survival()
            st.rerun()


# ============================================================
# TOOL 3 — INTERACTIVE MAPS
# ============================================================
TERRENI_MAPPA = {
    "hogwarts": """
        <path d="M0,340 Q100,322 200,335 T400,330 T600,338 T800,325 L800,400 L0,400 Z" fill="currentColor" opacity="0.08"/>
        <ellipse cx="150" cy="335" rx="95" ry="34" fill="currentColor" opacity="0.1"/>
        <ellipse cx="150" cy="335" rx="95" ry="34" fill="none" stroke="currentColor" stroke-width="1.5" opacity="0.45"/>
        <g opacity="0.55" stroke="currentColor" stroke-width="1.5" fill="none">
            <rect x="330" y="95" width="30" height="70"/>
            <path d="M330,95 L345,63 L360,95 Z"/>
            <rect x="366" y="72" width="34" height="93"/>
            <path d="M366,72 L383,35 L400,72 Z"/>
            <rect x="405" y="105" width="26" height="60"/>
            <path d="M405,105 L418,76 L431,105 Z"/>
            <rect x="292" y="118" width="26" height="47"/>
            <path d="M292,118 L305,92 L318,118 Z"/>
        </g>
        <g opacity="0.5" fill="currentColor">
            <path d="M600,262 L615,225 L630,262 Z"/>
            <path d="M624,272 L639,230 L654,272 Z"/>
            <path d="M648,255 L663,218 L678,255 Z"/>
            <path d="M668,278 L683,236 L698,278 Z"/>
        </g>
        <ellipse cx="235" cy="235" rx="58" ry="26" fill="none" stroke="currentColor" stroke-width="1.5" opacity="0.4" stroke-dasharray="5,5"/>
    """,
    "percy": """
        <path d="M0,300 Q100,286 200,300 T400,296 T600,306 T800,296 L800,400 L0,400 Z" fill="currentColor" opacity="0.1"/>
        <path d="M0,300 Q100,286 200,300 T400,296 T600,306 T800,296" fill="none" stroke="currentColor" stroke-width="1.5" opacity="0.4"/>
        <g opacity="0.55" stroke="currentColor" stroke-width="1.5" fill="none">
            <rect x="362" y="112" width="88" height="52"/>
            <path d="M357,112 L406,78 L455,112 Z"/>
            <line x1="382" y1="164" x2="382" y2="132"/>
            <line x1="430" y1="164" x2="430" y2="132"/>
        </g>
        <g opacity="0.5" stroke="currentColor" stroke-width="1.3" fill="none">
            <path d="M150,222 L150,252 L184,252 L184,222 L167,202 Z"/>
            <path d="M196,227 L196,255 L226,255 L226,227 L211,207 Z"/>
            <path d="M242,217 L242,247 L272,247 L272,217 L257,197 Z"/>
        </g>
        <g opacity="0.5" fill="currentColor">
            <path d="M580,192 L595,152 L610,192 Z"/>
            <path d="M605,202 L620,158 L635,202 Z"/>
            <path d="M630,187 L645,148 L660,187 Z"/>
        </g>
        <circle cx="180" cy="150" r="30" fill="none" stroke="currentColor" stroke-width="1.5" opacity="0.4" stroke-dasharray="5,5"/>
    """,
    "divergent": """
        <line x1="0" y1="360" x2="800" y2="360" stroke="currentColor" stroke-width="1.5" opacity="0.4"/>
        <g opacity="0.5" fill="currentColor">
            <rect x="80" y="240" width="34" height="120"/>
            <rect x="120" y="200" width="28" height="160"/>
            <rect x="155" y="260" width="40" height="100"/>
            <rect x="400" y="180" width="30" height="180"/>
            <rect x="435" y="230" width="26" height="130"/>
            <rect x="560" y="210" width="36" height="150"/>
            <rect x="600" y="250" width="24" height="110"/>
            <rect x="640" y="190" width="30" height="170"/>
        </g>
        <line x1="0" y1="120" x2="800" y2="150" stroke="currentColor" stroke-width="2" opacity="0.45"/>
        <g stroke="currentColor" stroke-width="1" opacity="0.35">
            <line x1="50" y1="119" x2="50" y2="135"/>
            <line x1="200" y1="126" x2="200" y2="142"/>
            <line x1="350" y1="132" x2="350" y2="148"/>
            <line x1="500" y1="139" x2="500" y2="155"/>
            <line x1="650" y1="145" x2="650" y2="161"/>
        </g>
        <rect x="20" y="60" width="760" height="300" fill="none" stroke="currentColor" stroke-width="1.5" stroke-dasharray="8,6" opacity="0.3"/>
    """,
    "hunger": """
        <path d="M60,220 Q40,140 140,110 Q260,60 400,90 Q560,60 680,130 Q760,180 720,270 Q660,340 500,330 Q380,360 260,330 Q120,320 60,220 Z" fill="currentColor" opacity="0.08" stroke="currentColor" stroke-width="1.5"/>
        <g opacity="0.5" fill="currentColor">
            <path d="M160,222 L185,172 L210,222 Z"/>
            <path d="M195,227 L220,167 L245,227 Z"/>
            <path d="M230,222 L255,177 L280,222 Z"/>
        </g>
        <g opacity="0.55" stroke="currentColor" stroke-width="1.5" fill="none">
            <rect x="385" y="122" width="30" height="78"/>
            <path d="M385,122 L400,97 L415,122 Z"/>
            <line x1="400" y1="97" x2="400" y2="82"/>
            <circle cx="400" cy="78" r="3" fill="currentColor" stroke="none"/>
        </g>
        <g opacity="0.5" stroke="currentColor" stroke-width="1.3" fill="none">
            <rect x="590" y="240" width="60" height="35"/>
            <rect x="600" y="215" width="10" height="25"/>
            <rect x="620" y="205" width="10" height="35"/>
        </g>
    """,
}


def render_map_illustration(mondo, luoghi, stile_card):
    terreno = textwrap.dedent(TERRENI_MAPPA.get(mondo, "")).strip()
    marcatori = "".join(
        f'<g>'
        f'<circle cx="{l["x"]}" cy="{l["y"]}" r="15" fill="currentColor" opacity="0.16"/>'
        f'<circle cx="{l["x"]}" cy="{l["y"]}" r="11" fill="none" stroke="currentColor" stroke-width="2"/>'
        f'<text x="{l["x"]}" y="{l["y"] + 5}" font-size="13" font-weight="700" '
        f'fill="currentColor" text-anchor="middle">{i + 1}</text>'
        f'</g>'
        for i, l in enumerate(luoghi)
    )
    svg = textwrap.dedent(f"""\
    <div class="{stile_card}" style="padding:1rem;">
    <svg viewBox="0 0 800 400" xmlns="http://www.w3.org/2000/svg" style="width:100%; height:auto;">
    {terreno}
    {marcatori}
    </svg>
    </div>
    """)
    st.markdown(svg, unsafe_allow_html=True)


def render_mappe():
    if st.button("← Back to menu"):
        st.session_state.pagina = "menu"
        st.session_state.pop("mappa_mondo", None)
        st.rerun()

    st.markdown('<div class="nexus-title" style="font-size:2.2rem;">🗺️ Interactive Maps</div>', unsafe_allow_html=True)
    st.markdown('<div class="nexus-subtitle">Choose a world and explore its locations</div>', unsafe_allow_html=True)

    mondo = st.session_state.get("mappa_mondo")
    if not mondo:
        render_selettore_mondo("mappa_mondo")
        return

    dati = MAP_POIS[mondo]
    st.markdown(f'<div class="{dati["font_titolo_css"]}" style="font-size:2rem;">{dati["titolo"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="subtitle">{dati["eyebrow"]}</div>', unsafe_allow_html=True)

    render_map_illustration(mondo, dati["luoghi"], dati["stile_card"])

    loc_key = f"mappa_loc_{mondo}"
    if loc_key not in st.session_state:
        st.session_state[loc_key] = 0

    etichette = [f"{i + 1}. {l['nome']}" for i, l in enumerate(dati["luoghi"])]
    idx_scelto = st.selectbox(
        "Choose a numbered location on the map to discover it",
        options=list(range(len(dati["luoghi"]))),
        format_func=lambda i: etichette[i],
        key=f"select_{loc_key}",
    )
    luogo_trovato = dati["luoghi"][idx_scelto]

    st.markdown(
        f'<div class="{dati["stile_card"]}"><h3>{luogo_trovato["nome"]}</h3>{luogo_trovato["desc"]}</div>',
        unsafe_allow_html=True,
    )

    st.write("")
    if st.button("🔄 Change world", use_container_width=True):
        st.session_state.pop("mappa_mondo", None)
        st.rerun()


# ============================================================
# MAIN MENU
# ============================================================
def render_menu():
    render_nexus_background()
    st.markdown('<div class="nexus-title">FANTASY QUIZ</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="nexus-subtitle">Choose which reality you want to explore</div>',
        unsafe_allow_html=True,
    )
    render_nexus_emblem()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            textwrap.dedent("""\
            <div class="menu-card" style="background:linear-gradient(160deg, #3d0a0a 0%, #1a2f14 100%);">
            <div class="menu-card-icon">🎩</div>
            <div class="menu-card-title">Hogwarts Sorting</div>
            <div class="menu-card-desc">Discover which of the four houses you'd be sorted into</div>
            </div>
            """),
            unsafe_allow_html=True,
        )
        if st.button("Enter Hogwarts", key="entra_hp", use_container_width=True):
            st.session_state.pagina = "hogwarts"
            st.rerun()

    with col2:
        st.markdown(
            textwrap.dedent("""\
            <div class="menu-card" style="background:linear-gradient(160deg, #0e2233 0%, #3a2a05 100%);">
            <div class="menu-card-icon">⚡</div>
            <div class="menu-card-title oly">Who Is Your Godly Parent?</div>
            <div class="menu-card-desc">Discover which Olympian god runs through your blood</div>
            </div>
            """),
            unsafe_allow_html=True,
        )
        if st.button("Enter the Camp", key="entra_pj", use_container_width=True):
            st.session_state.pagina = "percy"
            st.rerun()

    col3, col4 = st.columns(2)

    with col3:
        st.markdown(
            textwrap.dedent("""\
            <div class="menu-card" style="background:linear-gradient(160deg, #2b3238 0%, #1a1f22 100%);">
            <div class="menu-card-icon">⚖️</div>
            <div class="menu-card-title" style="font-family:'Barlow Condensed',sans-serif; letter-spacing:2px; text-transform:uppercase;">Which Faction Do You Belong To?</div>
            <div class="menu-card-desc">Discover which faction truly reflects your nature</div>
            </div>
            """),
            unsafe_allow_html=True,
        )
        if st.button("Face the Choice", key="entra_div", use_container_width=True):
            st.session_state.pagina = "divergent"
            st.rerun()

    with col4:
        st.markdown(
            textwrap.dedent("""\
            <div class="menu-card" style="background:linear-gradient(160deg, #241f16 0%, #2c3322 100%);">
            <div class="menu-card-icon">🔥</div>
            <div class="menu-card-title arena">Which District Do You Belong To?</div>
            <div class="menu-card-desc">Discover how you'd survive in the arena of Panem</div>
            </div>
            """),
            unsafe_allow_html=True,
        )
        if st.button("Face the Reaping", key="entra_hg", use_container_width=True):
            st.session_state.pagina = "hunger"
            st.rerun()

    st.write("")
    st.markdown(
        '<div class="nexus-subtitle" style="margin-top:0.4rem;">More tools</div>',
        unsafe_allow_html=True,
    )

    col5, col6, col7 = st.columns(3)

    with col5:
        st.markdown(
            textwrap.dedent("""\
            <div class="menu-card" style="background:linear-gradient(160deg, #3a2a05 0%, #4a1608 100%);">
            <div class="menu-card-icon">🪄</div>
            <div class="menu-card-title">Character Creator</div>
            <div class="menu-card-desc">Bring your character to life in one of the four worlds</div>
            </div>
            """),
            unsafe_allow_html=True,
        )
        if st.button("Create your character", key="entra_creator", use_container_width=True):
            st.session_state.pagina = "creator"
            st.rerun()

    with col6:
        st.markdown(
            textwrap.dedent("""\
            <div class="menu-card" style="background:linear-gradient(160deg, #0c0f08 0%, #4a1608 100%);">
            <div class="menu-card-icon">🏹</div>
            <div class="menu-card-title arena">Survival in the Arena</div>
            <div class="menu-card-desc">Face 6 days in the Hunger Games arena and find out if you survive</div>
            </div>
            """),
            unsafe_allow_html=True,
        )
        if st.button("Enter the Arena", key="entra_survival", use_container_width=True):
            st.session_state.pagina = "survival"
            st.rerun()

    with col7:
        st.markdown(
            textwrap.dedent("""\
            <div class="menu-card" style="background:linear-gradient(160deg, #0e2233 0%, #1a2f14 100%);">
            <div class="menu-card-icon">🗺️</div>
            <div class="menu-card-title">Interactive Maps</div>
            <div class="menu-card-desc">Explore the most iconic locations in each world</div>
            </div>
            """),
            unsafe_allow_html=True,
        )
        if st.button("Explore the maps", key="entra_mappe", use_container_width=True):
            st.session_state.pagina = "mappe"
            st.rerun()


# ============================================================
# MAIN NAVIGATION
# ============================================================
if "pagina" not in st.session_state:
    st.session_state.pagina = "menu"

if st.session_state.pagina == "menu":
    render_menu()
elif st.session_state.pagina == "hogwarts":
    render_hogwarts()
elif st.session_state.pagina == "percy":
    render_percy()
elif st.session_state.pagina == "divergent":
    render_divergent()
elif st.session_state.pagina == "hunger":
    render_hunger_games()
elif st.session_state.pagina == "creator":
    render_creator()
elif st.session_state.pagina == "survival":
    render_survival()
elif st.session_state.pagina == "mappe":
    render_mappe()