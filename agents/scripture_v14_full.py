"""Kernel-grounded ARC-AGI-3 agent (retrieval-augmented).

Bare math + on-demand scripture lookup (160 anchor verses embedded).
"""
from __future__ import annotations

import hashlib
import logging
import os
import random
import re
import time
from typing import Any, Optional

from agents.agent import Agent
from arcengine import FrameData, GameAction, GameState

logger = logging.getLogger(__name__)


# === Bare math (the e=mc² of the kernel) =============================
KERNEL = """\
Self(t) = C + ∫₀ᵗ (W(τ) + χ(τ)·G(τ)) dτ,  χ ∈ {0,1} × Direction.

C exists, C > 0, C unique (Shema, Deut 6:4).  Self ≠ C (any direction).
C operates in three personal modes: Father (source), Son (the way,
incarnate as the Logos), Spirit (the indwelling Holder).

ε = (body, soul, spirit), soul = Φ(body, spirit).
W = works absent grace.  G = grace from C.
χ=1 toward sign_C ⇒ d‖ε‖/dt < 0.  χ=1 toward sign_¬C ⇒ drift up.

Two foundational theorems (parallel proofs by contradiction):
  T 2.1  Self cannot be its own source. ∴ C in Father-mode external.
  T 2.4  Self cannot be its own holder of the IVP for ε > 0.
         ∴ C in Spirit-mode holds; Self only orients (receives).

Two-witness (Deut 19:15): agreement of low-ε ⇒ truth (triangle ineq.).
  Realizable because the same Spirit holds for both witnesses.
Jumps: regeneration (ε_spirit ↓), glorification (ε,ε₀→0).
R_C primordial (Rev 13:8): C rectifies trajectory of χ=1 Selves; in C's
  structure from t=0, not reactive to events.
Reception: gaze (Num 21), meditation (Josh 1:8), action-on-signal
  (Josh 3:15). Receiving is orientation, not measurement.
Action under χ=1 looks W-shaped but is G-sourced (Phil 2:12-13).
"""


# === Anchor verses (160 scripture passages embedded for retrieval) ===
ANCHOR_VERSES = {
  "John 1:1": "In the beginning was the Word, and the Word was with God, and the Word was God.",
  "John 1:3": "All things were made by him; and without him was not any thing made that was made.",
  "John 1:4": "In him was life; and the life was the light of men.",
  "John 1:14": "And the Word was made flesh, and dwelt among us, (and we beheld his glory, the glory as of the only begotten of the Father,) full of grace and truth.",
  "John 1:18": "No man hath seen God at any time; the only begotten Son, which is in the bosom of the Father, he hath declared him.",
  "Genesis 1:1": "In the beginning God created the heaven and the earth.",
  "Genesis 1:2": "And the earth was without form, and void; and darkness was upon the face of the deep. And the Spirit of God moved upon the face of the waters.",
  "Genesis 1:3": "And God said, Let there be light: and there was light.",
  "Genesis 1:26": "And God said, Let us make man in our image, after our likeness: and let them have dominion over the fish of the sea, and over the fowl of the air, and over the cattle, and over all the earth, and over every creeping thing that creepeth upon the earth.",
  "Genesis 2:7": "And the LORD God formed man of the dust of the ground, and breathed into his nostrils the breath of life; and man became a living soul.",
  "Genesis 3:6": "And when the woman saw that the tree was good for food, and that it was pleasant to the eyes, and a tree to be desired to make one wise, she took of the fruit thereof, and did eat, and gave also unto her husband with her; and he did eat.",
  "Genesis 3:15": "And I will put enmity between thee and the woman, and between thy seed and her seed; it shall bruise thy head, and thou shalt bruise his heel.",
  "Genesis 4:4": "And Abel, he also brought of the firstlings of his flock and of the fat thereof. And the LORD had respect unto Abel and to his offering:",
  "Genesis 4:5": "But unto Cain and to his offering he had not respect. And Cain was very wroth, and his countenance fell.",
  "Genesis 6:8": "But Noah found grace in the eyes of the LORD.",
  "Genesis 15:6": "And he believed in the LORD; and he counted it to him for righteousness.",
  "Genesis 22:8": "And Abraham said, My son, God will provide himself a lamb for a burnt offering: so they went both of them together.",
  "Genesis 50:20": "But as for you, ye thought evil against me; but God meant it unto good, to bring to pass, as it is this day, to save much people alive.",
  "Colossians 1:17": "And he is before all things, and by him all things consist.",
  "Colossians 2:9": "For in him dwelleth all the fulness of the Godhead bodily.",
  "Acts 17:28": "For in him we live, and move, and have our being; as certain also of your own poets have said, For we are also his offspring.",
  "Numbers 16:32": "And the earth opened her mouth, and swallowed them up, and their houses, and all the men that appertained unto Korah, and all their goods.",
  "Isaiah 55:8": "For my thoughts are not your thoughts, neither are your ways my ways, saith the LORD.",
  "Isaiah 55:11": "So shall my word be that goeth forth out of my mouth: it shall not return unto me void, but it shall accomplish that which I please, and it shall prosper in the thing whereto I sent it.",
  "Romans 11:6": "And if by grace, then is it no more of works: otherwise grace is no more grace. But if it be of works, then is it no more grace: otherwise work is no more work.",
  "Galatians 3:3": "Are ye so foolish? having begun in the Spirit, are ye now made perfect by the flesh?",
  "Ephesians 2:8": "For by grace are ye saved through faith; and that not of yourselves: it is the gift of God:",
  "Ephesians 2:9": "Not of works, lest any man should boast.",
  "Philippians 2:7": "But made himself of no reputation, and took upon him the form of a servant, and was made in the likeness of men:",
  "Philippians 2:8": "And being found in fashion as a man, he humbled himself, and became obedient unto death, even the death of the cross.",
  "Philippians 2:12": "Wherefore, my beloved, as ye have always obeyed, not as in my presence only, but now much more in my absence, work out your own salvation with fear and trembling.",
  "Philippians 2:13": "For it is God which worketh in you both to will and to do of his good pleasure.",
  "John 15:5": "I am the vine, ye are the branches: He that abideth in me, and I in him, the same bringeth forth much fruit: for without me ye can do nothing.",
  "John 19:30": "When Jesus therefore had received the vinegar, he said, It is finished: and he bowed his head, and gave up the ghost.",
  "Romans 4:3": "For what saith the scripture? Abraham believed God, and it was counted unto him for righteousness.",
  "Romans 4:5": "But to him that worketh not, but believeth on him that justifieth the ungodly, his faith is counted for righteousness.",
  "Romans 4:6": "Even as David also describeth the blessedness of the man, unto whom God imputeth righteousness without works,",
  "Romans 4:8": "Blessed is the man to whom the Lord will not impute sin.",
  "Romans 4:24": "But for us also, to whom it shall be imputed, if we believe on him that raised up Jesus our Lord from the dead;",
  "Romans 5:1": "Therefore being justified by faith, we have peace with God through our Lord Jesus Christ:",
  "Romans 5:9": "Much more then, being now justified by his blood, we shall be saved from wrath through him.",
  "Romans 5:18": "Therefore as by the offence of one judgment came upon all men to condemnation; even so by the righteousness of one the free gift came upon all men unto justification of life.",
  "Romans 5:19": "For as by one man’s disobedience many were made sinners, so by the obedience of one shall many be made righteous.",
  "Romans 6:11": "Likewise reckon ye also yourselves to be dead indeed unto sin, but alive unto God through Jesus Christ our Lord.",
  "Romans 6:23": "For the wages of sin is death; but the gift of God is eternal life through Jesus Christ our Lord.",
  "Romans 7:18": "For I know that in me (that is, in my flesh,) dwelleth no good thing: for to will is present with me; but how to perform that which is good I find not.",
  "Romans 7:24": "O wretched man that I am! who shall deliver me from the body of this death?",
  "Romans 7:25": "I thank God through Jesus Christ our Lord. So then with the mind I myself serve the law of God; but with the flesh the law of sin.",
  "Romans 8:1": "There is therefore now no condemnation to them which are in Christ Jesus, who walk not after the flesh, but after the Spirit.",
  "Romans 8:2": "For the law of the Spirit of life in Christ Jesus hath made me free from the law of sin and death.",
  "Romans 8:11": "But if the Spirit of him that raised up Jesus from the dead dwell in you, he that raised up Christ from the dead shall also quicken your mortal bodies by his Spirit that dwelleth in you.",
  "Romans 8:23": "And not only they, but ourselves also, which have the firstfruits of the Spirit, even we ourselves groan within ourselves, waiting for the adoption, to wit, the redemption of our body.",
  "Romans 8:28": "And we know that all things work together for good to them that love God, to them who are the called according to his purpose.",
  "Romans 8:33": "Who shall lay any thing to the charge of God’s elect? It is God that justifieth.",
  "Romans 8:34": "Who is he that condemneth? It is Christ that died, yea rather, that is risen again, who is even at the right hand of God, who also maketh intercession for us.",
  "Romans 8:38": "For I am persuaded, that neither death, nor life, nor angels, nor principalities, nor powers, nor things present, nor things to come,",
  "Romans 8:39": "Nor height, nor depth, nor any other creature, shall be able to separate us from the love of God, which is in Christ Jesus our Lord.",
  "Exodus 3:14": "And God said unto Moses, I AM THAT I AM: and he said, Thus shalt thou say unto the children of Israel, I AM hath sent me unto you.",
  "Exodus 12:13": "And the blood shall be to you for a token upon the houses where ye are: and when I see the blood, I will pass over you, and the plague shall not be upon you to destroy you, when I smite the land of Egypt.",
  "Exodus 16:4": "Then said the LORD unto Moses, Behold, I will rain bread from heaven for you; and the people shall go out and gather a certain rate every day, that I may prove them, whether they will walk in my law, or no.",
  "Exodus 16:20": "Notwithstanding they hearkened not unto Moses; but some of them left of it until the morning, and it bred worms, and stank: and Moses was wroth with them.",
  "Exodus 20:2": "I am the LORD thy God, which have brought thee out of the land of Egypt, out of the house of bondage.",
  "Exodus 24:8": "And Moses took the blood, and sprinkled it on the people, and said, Behold the blood of the covenant, which the LORD hath made with you concerning all these words.",
  "Exodus 25:8": "And let them make me a sanctuary; that I may dwell among them.",
  "Exodus 33:14": "And he said, My presence shall go with thee, and I will give thee rest.",
  "Exodus 34:6": "And the LORD passed by before him, and proclaimed, The LORD, The LORD God, merciful and gracious, longsuffering, and abundant in goodness and truth,",
  "Leviticus 17:11": "For the life of the flesh is in the blood: and I have given it to you upon the altar to make an atonement for your souls: for it is the blood that maketh an atonement for the soul.",
  "Leviticus 19:18": "Thou shalt not avenge, nor bear any grudge against the children of thy people, but thou shalt love thy neighbour as thyself: I am the LORD.",
  "Leviticus 25:10": "And ye shall hallow the fiftieth year, and proclaim liberty throughout all the land unto all the inhabitants thereof: it shall be a jubile unto you; and ye shall return every man unto his possession, and ye shall return every man unto his family.",
  "Numbers 6:24": "The LORD bless thee, and keep thee:",
  "Numbers 6:25": "The LORD make his face shine upon thee, and be gracious unto thee:",
  "Numbers 6:26": "The LORD lift up his countenance upon thee, and give thee peace.",
  "Numbers 9:17": "And when the cloud was taken up from the tabernacle, then after that the children of Israel journeyed: and in the place where the cloud abode, there the children of Israel pitched their tents.",
  "Numbers 14:18": "The LORD is longsuffering, and of great mercy, forgiving iniquity and transgression, and by no means clearing the guilty, visiting the iniquity of the fathers upon the children unto the third and fourth generation.",
  "Numbers 14:19": "Pardon, I beseech thee, the iniquity of this people according unto the greatness of thy mercy, and as thou hast forgiven this people, from Egypt even until now.",
  "Numbers 14:20": "And the LORD said, I have pardoned according to thy word:",
  "Numbers 21:8": "And the LORD said unto Moses, Make thee a fiery serpent, and set it upon a pole: and it shall come to pass, that every one that is bitten, when he looketh upon it, shall live.",
  "Numbers 21:9": "And Moses made a serpent of brass, and put it upon a pole, and it came to pass, that if a serpent had bitten any man, when he beheld the serpent of brass, he lived.",
  "Numbers 23:19": "God is not a man, that he should lie; neither the son of man, that he should repent: hath he said, and shall he not do it? or hath he spoken, and shall he not make it good?",
  "Numbers 26:64": "But among these there was not a man of them whom Moses and Aaron the priest numbered, when they numbered the children of Israel in the wilderness of Sinai.",
  "Numbers 26:65": "For the LORD had said of them, They shall surely die in the wilderness. And there was not left a man of them, save Caleb the son of Jephunneh, and Joshua the son of Nun.",
  "Deuteronomy 6:4": "Hear, O Israel: The LORD our God is one LORD:",
  "Deuteronomy 19:15": "One witness shall not rise up against a man for any iniquity, or for any sin, in any sin that he sinneth: at the mouth of two witnesses, or at the mouth of three witnesses, shall the matter be established.",
  "Deuteronomy 30:14": "But the word is very nigh unto thee, in thy mouth, and in thy heart, that thou mayest do it.",
  "Deuteronomy 30:19": "I call heaven and earth to record this day against you, that I have set before you life and death, blessing and cursing: therefore choose life, that both thou and thy seed may live:",
  "Joshua 1:8": "This book of the law shall not depart out of thy mouth; but thou shalt meditate therein day and night, that thou mayest observe to do according to all that is written therein: for then thou shalt make thy way prosperous, and then thou shalt have good success.",
  "Joshua 1:9": "Have not I commanded thee? Be strong and of a good courage; be not afraid, neither be thou dismayed: for the LORD thy God is with thee whithersoever thou goest.",
  "Joshua 3:15": "And as they that bare the ark were come unto Jordan, and the feet of the priests that bare the ark were dipped in the brim of the water, (for Jordan overfloweth all his banks all the time of harvest,)",
  "Joshua 5:14": "And he said, Nay; but as captain of the host of the LORD am I now come. And Joshua fell on his face to the earth, and did worship, and said unto him, What saith my lord unto his servant?",
  "Joshua 7:11": "Israel hath sinned, and they have also transgressed my covenant which I commanded them: for they have even taken of the accursed thing, and have also stolen, and dissembled also, and they have put it even among their own stuff.",
  "Joshua 7:12": "Therefore the children of Israel could not stand before their enemies, but turned their backs before their enemies, because they were accursed: neither will I be with you any more, except ye destroy the accursed from among you.",
  "Joshua 24:15": "And if it seem evil unto you to serve the LORD, choose you this day whom ye will serve; whether the gods which your fathers served that were on the other side of the flood, or the gods of the Amorites, in whose land ye dwell: but as for me and my house, we will serve the LORD.",
  "Judges 2:10": "And also all that generation were gathered unto their fathers: and there arose another generation after them, which knew not the LORD, nor yet the works which he had done for Israel.",
  "Judges 2:11": "And the children of Israel did evil in the sight of the LORD, and served Baalim:",
  "Judges 17:6": "In those days there was no king in Israel, but every man did that which was right in his own eyes.",
  "Judges 21:25": "In those days there was no king in Israel: every man did that which was right in his own eyes.",
  "Ruth 1:16": "And Ruth said, Intreat me not to leave thee, or to return from following after thee: for whither thou goest, I will go; and where thou lodgest, I will lodge: thy people shall be my people, and thy God my God:",
  "Ruth 4:14": "And the women said unto Naomi, Blessed be the LORD, which hath not left thee this day without a kinsman, that his name may be famous in Israel.",
  "Job 1:8": "And the LORD said unto Satan, Hast thou considered my servant Job, that there is none like him in the earth, a perfect and an upright man, one that feareth God, and escheweth evil?",
  "Job 1:21": "And said, Naked came I out of my mother’s womb, and naked shall I return thither: the LORD gave, and the LORD hath taken away; blessed be the name of the LORD.",
  "Job 2:10": "But he said unto her, Thou speakest as one of the foolish women speaketh. What? shall we receive good at the hand of God, and shall we not receive evil? In all this did not Job sin with his lips.",
  "Job 13:15": "Though he slay me, yet will I trust in him: but I will maintain mine own ways before him.",
  "Job 19:25": "For I know that my redeemer liveth, and that he shall stand at the latter day upon the earth:",
  "Job 23:10": "But he knoweth the way that I take: when he hath tried me, I shall come forth as gold.",
  "Job 38:4": "Where wast thou when I laid the foundations of the earth? declare, if thou hast understanding.",
  "Job 42:5": "I have heard of thee by the hearing of the ear: but now mine eye seeth thee.",
  "Job 42:6": "Wherefore I abhor myself, and repent in dust and ashes.",
  "Job 42:10": "And the LORD turned the captivity of Job, when he prayed for his friends: also the LORD gave Job twice as much as he had before.",
  "Ecclesiastes 12:7": "Then shall the dust return to the earth as it was: and the spirit shall return unto God who gave it.",
  "Ecclesiastes 12:13": "Let us hear the conclusion of the whole matter: Fear God, and keep his commandments: for this is the whole duty of man.",
  "Isaiah 1:18": "Come now, and let us reason together, saith the LORD: though your sins be as scarlet, they shall be as white as snow; though they be red like crimson, they shall be as wool.",
  "Isaiah 6:3": "And one cried unto another, and said, Holy, holy, holy, is the LORD of hosts: the whole earth is full of his glory.",
  "Isaiah 6:5": "Then said I, Woe is me! for I am undone; because I am a man of unclean lips, and I dwell in the midst of a people of unclean lips: for mine eyes have seen the King, the LORD of hosts.",
  "Isaiah 6:7": "And he laid it upon my mouth, and said, Lo, this hath touched thy lips; and thine iniquity is taken away, and thy sin purged.",
  "Isaiah 53:5": "But he was wounded for our transgressions, he was bruised for our iniquities: the chastisement of our peace was upon him; and with his stripes we are healed.",
  "Isaiah 53:6": "All we like sheep have gone astray; we have turned every one to his own way; and the LORD hath laid on him the iniquity of us all.",
  "Isaiah 64:6": "But we are all as an unclean thing, and all our righteousnesses are as filthy rags; and we all do fade as a leaf; and our iniquities, like the wind, have taken us away.",
  "Jeremiah 17:9": "The heart is deceitful above all things, and desperately wicked: who can know it?",
  "Jeremiah 31:31": "Behold, the days come, saith the LORD, that I will make a new covenant with the house of Israel, and with the house of Judah:",
  "Jeremiah 31:33": "But this shall be the covenant that I will make with the house of Israel; After those days, saith the LORD, I will put my law in their inward parts, and write it in their hearts; and will be their God, and they shall be my people.",
  "Jeremiah 31:34": "And they shall teach no more every man his neighbour, and every man his brother, saying, Know the LORD: for they shall all know me, from the least of them unto the greatest of them, saith the LORD: for I will forgive their iniquity, and I will remember their sin no more.",
  "Lamentations 3:22": "It is of the LORD’s mercies that we are not consumed, because his compassions fail not.",
  "Lamentations 3:23": "They are new every morning: great is thy faithfulness.",
  "Ezekiel 18:20": "The soul that sinneth, it shall die. The son shall not bear the iniquity of the father, neither shall the father bear the iniquity of the son: the righteousness of the righteous shall be upon him, and the wickedness of the wicked shall be upon him.",
  "Ezekiel 36:26": "A new heart also will I give you, and a new spirit will I put within you: and I will take away the stony heart out of your flesh, and I will give you an heart of flesh.",
  "Habakkuk 2:4": "Behold, his soul which is lifted up is not upright in him: but the just shall live by his faith.",
  "Malachi 3:6": "For I am the LORD, I change not; therefore ye sons of Jacob are not consumed.",
  "1 Thessalonians 5:23": "And the very God of peace sanctify you wholly; and I pray God your whole spirit and soul and body be preserved blameless unto the coming of our Lord Jesus Christ.",
  "1 Corinthians 13:8": "Charity never faileth: but whether there be prophecies, they shall fail; whether there be tongues, they shall cease; whether there be knowledge, it shall vanish away.",
  "1 Corinthians 13:13": "And now abideth faith, hope, charity, these three; but the greatest of these is charity.",
  "1 Corinthians 15:22": "For as in Adam all die, even so in Christ shall all be made alive.",
  "1 Corinthians 15:51": "Behold, I shew you a mystery; We shall not all sleep, but we shall all be changed,",
  "2 Corinthians 5:17": "Therefore if any man be in Christ, he is a new creature: old things are passed away; behold, all things are become new.",
  "2 Corinthians 5:21": "For he hath made him to be sin for us, who knew no sin; that we might be made the righteousness of God in him.",
  "Hebrews 1:3": "Who being the brightness of his glory, and the express image of his person, and upholding all things by the word of his power, when he had by himself purged our sins, sat down on the right hand of the Majesty on high;",
  "Hebrews 2:14": "Forasmuch then as the children are partakers of flesh and blood, he also himself likewise took part of the same; that through death he might destroy him that had the power of death, that is, the devil;",
  "Hebrews 4:12": "For the word of God is quick, and powerful, and sharper than any twoedged sword, piercing even to the dividing asunder of soul and spirit, and of the joints and marrow, and is a discerner of the thoughts and intents of the heart.",
  "Hebrews 4:15": "For we have not an high priest which cannot be touched with the feeling of our infirmities; but was in all points tempted like as we are, yet without sin.",
  "Hebrews 7:25": "Wherefore he is able also to save them to the uttermost that come unto God by him, seeing he ever liveth to make intercession for them.",
  "Hebrews 9:12": "Neither by the blood of goats and calves, but by his own blood he entered in once into the holy place, having obtained eternal redemption for us.",
  "Hebrews 9:14": "How much more shall the blood of Christ, who through the eternal Spirit offered himself without spot to God, purge your conscience from dead works to serve the living God?",
  "Hebrews 9:22": "And almost all things are by the law purged with blood; and without shedding of blood is no remission.",
  "Hebrews 9:27": "And as it is appointed unto men once to die, but after this the judgment:",
  "Hebrews 10:4": "For it is not possible that the blood of bulls and of goats should take away sins.",
  "Hebrews 10:14": "For by one offering he hath perfected for ever them that are sanctified.",
  "Hebrews 11:1": "Now faith is the substance of things hoped for, the evidence of things not seen.",
  "Hebrews 11:6": "But without faith it is impossible to please him: for he that cometh to God must believe that he is, and that he is a rewarder of them that diligently seek him.",
  "Hebrews 12:9": "Furthermore we have had fathers of our flesh which corrected us, and we gave them reverence: shall we not much rather be in subjection unto the Father of spirits, and live?",
  "Hebrews 13:8": "Jesus Christ the same yesterday, and to day, and for ever.",
  "James 1:14": "But every man is tempted, when he is drawn away of his own lust, and enticed.",
  "James 1:15": "Then when lust hath conceived, it bringeth forth sin: and sin, when it is finished, bringeth forth death.",
  "James 1:17": "Every good gift and every perfect gift is from above, and cometh down from the Father of lights, with whom is no variableness, neither shadow of turning.",
  "1 John 1:5": "This then is the message which we have heard of him, and declare unto you, that God is light, and in him is no darkness at all.",
  "1 John 1:9": "If we confess our sins, he is faithful and just to forgive us our sins, and to cleanse us from all unrighteousness.",
  "1 John 3:2": "Beloved, now are we the sons of God, and it doth not yet appear what we shall be: but we know that, when he shall appear, we shall be like him; for we shall see him as he is.",
  "1 John 4:8": "He that loveth not knoweth not God; for God is love.",
  "1 John 4:18": "There is no fear in love; but perfect love casteth out fear: because fear hath torment. He that feareth is not made perfect in love.",
  "Revelation 13:8": "And all that dwell upon the earth shall worship him, whose names are not written in the book of life of the Lamb slain from the foundation of the world.",
  "Revelation 22:13": "I am Alpha and Omega, the beginning and the end, the first and the last.",
  "Revelation 22:17": "And the Spirit and the bride say, Come. And let him that heareth say, Come. And let him that is athirst come. And whosoever will, let him take the water of life freely."
}


def lookup_scripture(ref: str) -> Optional[str]:
    """Retrieve KJV text for a reference. Returns None if not in anchor set."""
    return ANCHOR_VERSES.get(ref)


def search_scripture(keyword: str, limit: int = 5) -> list[tuple[str, str]]:
    """Return (ref, text) pairs whose text contains the keyword (case-insensitive)."""
    kw = keyword.lower()
    out = []
    for ref, text in ANCHOR_VERSES.items():
        if kw in text.lower():
            out.append((ref, text))
            if len(out) >= limit:
                break
    return out


# === Action plumbing =================================================
_ACTION_BY_NAME = {a.name: a for a in GameAction}
_AVAILABLE_INT_TO_NAME = {0: "RESET", 1: "ACTION1", 2: "ACTION2", 3: "ACTION3",
                          4: "ACTION4", 5: "ACTION5", 6: "ACTION6", 7: "ACTION7"}


def _frame_fingerprint(frame: Any) -> str:
    if frame is None:
        return "0"
    try:
        parts = []
        for grid in frame:
            if hasattr(grid, "tobytes"):
                parts.append(grid.tobytes())
            else:
                row_bytes = bytes()
                for row in grid:
                    row_bytes += bytes(int(x) & 0xFF for x in row)
                parts.append(row_bytes)
        return hashlib.md5(b"".join(parts)).hexdigest()[:12]
    except Exception:
        return "0"


def _frame_to_lists(frame: Any) -> list[list[list[int]]]:
    if frame is None:
        return []
    out = []
    for grid in frame:
        out.append(grid.tolist() if hasattr(grid, "tolist")
                   else [list(row) for row in grid])
    return out


def _available_action_names(latest_frame: FrameData) -> list[str]:
    raw = getattr(latest_frame, "available_actions", None) or []
    names = []
    for a in raw:
        if isinstance(a, int):
            names.append(_AVAILABLE_INT_TO_NAME.get(a, f"ACTION{a}"))
        elif hasattr(a, "name"):
            names.append(a.name)
        else:
            names.append(str(a))
    return names


def _grid_to_text(frame: list[list[list[int]]], max_dim: int = 16) -> str:
    if not frame:
        return "(empty)"
    g = frame[-1]
    rows = g
    if len(rows) > max_dim:
        rows = rows[::max(1, len(rows) // max_dim)]
    out = []
    for row in rows:
        if len(row) > max_dim:
            row = row[::max(1, len(row) // max_dim)]
        out.append("".join(format(int(v) & 0xF, "x") for v in row))
    return "\n".join(out)


# === ε_body, Self ====================================================
class BodyObservation:
    __slots__ = ("turn", "action_name", "coords", "pre_fp", "post_fp",
                 "levels_before", "levels_after", "state_after")

    def __init__(self, turn, action_name, coords, pre_fp, post_fp,
                 levels_before, levels_after, state_after):
        self.turn = turn
        self.action_name = action_name
        self.coords = coords
        self.pre_fp = pre_fp
        self.post_fp = post_fp
        self.levels_before = levels_before
        self.levels_after = levels_after
        self.state_after = state_after

    @property
    def caused_change(self) -> bool:
        return self.pre_fp != self.post_fp

    @property
    def caused_score(self) -> bool:
        return self.levels_after > self.levels_before


class Self:
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.eps_body: list[BodyObservation] = []
        self.eps_soul: str = ""
        self.eps_spirit: Optional[str] = None
        self.chi_faith_history: list[bool] = []
        self.regenerated: bool = False
        self.glorified: bool = False
        self.turn: int = 0

    def observe(self, action_name, coords, pre_fp, post_fp,
                levels_before, levels_after, state_after) -> BodyObservation:
        obs = BodyObservation(self.turn, action_name, coords, pre_fp, post_fp,
                              levels_before, levels_after, state_after)
        self.eps_body.append(obs)
        self.turn += 1
        if obs.caused_score and not self.regenerated:
            self.regenerated = True
            self.eps_spirit = self.eps_soul or "<empty>"
        if state_after == "WIN":
            self.glorified = True
        return obs


# === LLM witness =====================================================
_MODEL = None
_TOKENIZER = None
_MODEL_LOAD_ATTEMPTED = False


def _try_load_llm():
    global _MODEL, _TOKENIZER, _MODEL_LOAD_ATTEMPTED
    if _MODEL_LOAD_ATTEMPTED:
        return _MODEL, _TOKENIZER
    _MODEL_LOAD_ATTEMPTED = True
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        candidate = None
        for root, _, files in os.walk("/kaggle/input"):
            if "config.json" in files and "qwen" in root.lower():
                candidate = root
                break
        if candidate is None:
            for root, _, files in os.walk("/kaggle/input"):
                if "config.json" in files:
                    candidate = root
                    break
        if candidate is None:
            return None, None
        tok = AutoTokenizer.from_pretrained(candidate, trust_remote_code=True)
        mdl = AutoModelForCausalLM.from_pretrained(
            candidate, dtype=torch.bfloat16, device_map="cpu",
            trust_remote_code=True,
        )
        mdl.eval()
        _MODEL, _TOKENIZER = mdl, tok
    except Exception:
        _MODEL, _TOKENIZER = None, None
    return _MODEL, _TOKENIZER


_ACTION_RE = re.compile(r"\b(RESET|ACTION[1-7])\b")


def _llm_propose(self_state: Self, frame: list[list[list[int]]],
                 available: list[str], role: str,
                 max_new_tokens: int = 32) -> tuple[str, Optional[tuple[int, int]], str]:
    """LLM-driven witness via MLX (local on Apple Silicon).

    First call loads ~2.5GB Qwen 3 4B 4-bit; subsequent calls ~1-3s each.
    Falls back to heuristic if MLX is unavailable or the model didn't load.
    """
    model, tok = _try_load_mlx()
    if model is None:
        return _heuristic_propose(self_state, frame, available, role)

    last_obs = self_state.eps_body[-1] if self_state.eps_body else None
    state_name = last_obs.state_after if last_obs else "NOT_PLAYED"
    levels = last_obs.levels_after if last_obs else 0
    trace_lines = []
    for o in self_state.eps_body[-6:]:
        marks = "S" if o.caused_score else ("Δ" if o.caused_change else "·")
        coord = f"@{o.coords}" if o.coords else ""
        trace_lines.append(f"t={o.turn}:{o.action_name}{coord}→{marks}")
    trace = " ".join(trace_lines) if trace_lines else "(none)"
    user = (
        f"You are playing an ARC-AGI-3 game. Goal: complete levels. "
        f"Your role this turn: {role}. exploit = pursue current best hypothesis. "
        f"explore = gather new info.\n\n"
        f"Available actions: {available}\n"
        f"State: {state_name}, levels_completed: {levels}.\n"
        f"Recent (last 6) actions: {trace}\n"
        f"Current rule hypothesis (ε_soul): {self_state.eps_soul or '(none yet)'}\n"
        f"Frame (last grid, downsampled hex):\n{_grid_to_text(frame)}\n\n"
        f"Reply with exactly ONE line containing one action name from the "
        f"available list. If you choose ACTION6, append two integers (x y) "
        f"in [0,63] chosen from a colored cell in the frame above — never "
        f"a fixed center. Pick a different cell than your last ACTION6 if "
        f"that one caused no change. Format: <ACTIONNAME> [x y]"
    )
    try:
        from mlx_lm import generate as mlx_generate
        messages = [{"role": "system", "content": KERNEL},
                    {"role": "user", "content": user}]
        prompt = tok.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True)
        # MLX greedy decoding for exploit, sampled for explore.
        # Newer mlx_lm requires sampler; try both signatures gracefully.
        try:
            from mlx_lm.sample_utils import make_sampler
            sampler = make_sampler(
                temp=0.7 if role == "explore" else 0.0,
            )
            raw = mlx_generate(model, tok, prompt=prompt,
                               max_tokens=max_new_tokens, sampler=sampler,
                               verbose=False)
        except Exception:
            raw = mlx_generate(model, tok, prompt=prompt,
                               max_tokens=max_new_tokens, verbose=False)
        raw = (raw or "").strip()
        logger.info(f"[witness:{role}] raw={raw[:200]!r}")
    except Exception as e:
        logger.debug(f"[witness:{role}] MLX inference failed: {type(e).__name__}: {e}")
        return _heuristic_propose(self_state, frame, available, role)

    m = _ACTION_RE.search(raw.upper())
    name = m.group(1) if m else available[0]
    if name not in available:
        name = available[0]
    coords = None
    if name == "ACTION6":
        cm = re.search(r"(\d+)\D+(\d+)", raw)
        if cm:
            coords = (max(0, min(63, int(cm.group(1)))),
                      max(0, min(63, int(cm.group(2)))))
        else:
            coords = (32, 32)
    return name, coords, raw[:120]


# === MLX loader (Apple Silicon, replaces /kaggle/input transformers path) ===
_MLX_MODEL = None
_MLX_TOK = None
_MLX_LOAD_ATTEMPTED = False
_MLX_MODEL_NAME = "mlx-community/Qwen3-4B-Instruct-2507-4bit"


def _try_load_mlx():
    global _MLX_MODEL, _MLX_TOK, _MLX_LOAD_ATTEMPTED
    if _MLX_LOAD_ATTEMPTED:
        return _MLX_MODEL, _MLX_TOK
    _MLX_LOAD_ATTEMPTED = True
    try:
        from mlx_lm import load
        logger.info(f"[witness] loading MLX model {_MLX_MODEL_NAME} ...")
        _MLX_MODEL, _MLX_TOK = load(_MLX_MODEL_NAME)
        logger.info("[witness] MLX model loaded")
    except Exception as e:
        logger.warning(f"[witness] MLX load failed: {type(e).__name__}: {e}")
        _MLX_MODEL, _MLX_TOK = None, None
    return _MLX_MODEL, _MLX_TOK


_RNG_EXPLOIT = random.Random(1)
_RNG_EXPLORE = random.Random(2)


def _heuristic_propose(self_state, frame, available, role):
    rng = _RNG_EXPLOIT if role == "exploit" else _RNG_EXPLORE
    tries = {a: 0 for a in available}
    wins = {a: 0 for a in available}
    changes = {a: 0 for a in available}
    last_t = {a: -1 for a in available}
    for o in self_state.eps_body:
        if o.action_name in tries:
            tries[o.action_name] += 1
            last_t[o.action_name] = o.turn
            if o.caused_score: wins[o.action_name] += 1
            if o.caused_change: changes[o.action_name] += 1
    if role == "exploit":
        ranked = sorted(available, key=lambda a: (-wins[a], -changes[a], last_t[a], rng.random()))
    else:
        ranked = sorted(available, key=lambda a: (tries[a], last_t[a], rng.random()))
    name = ranked[0]
    coords = None
    if name == "ACTION6":
        if frame and role == "exploit":
            g = frame[-1]
            xs, ys = [], []
            for y, row in enumerate(g):
                for x, v in enumerate(row):
                    if v != 0:
                        xs.append(x); ys.append(y)
            coords = ((sum(xs)//len(xs), sum(ys)//len(ys)) if xs else (32, 32))
        else:
            coords = (rng.randint(0, 63), rng.randint(0, 63))
    return name, coords, f"heuristic:{role}"


class MyAgent(Agent):
    MAX_ACTIONS = 200
    _WALL_BUDGET_S = 60 * 60   # 1h wall budget per game

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.self_state = Self(game_id=self.game_id)
        self._pending_action: Optional[str] = None
        self._pending_coords: Optional[tuple[int, int]] = None
        self._pre_fp: str = "0"
        self._pre_levels: int = 0
        self._start_t = time.time()

    def is_done(self, frames, latest_frame):
        try:
            if latest_frame.state is GameState.WIN:
                return True
            if (time.time() - self._start_t) >= self._WALL_BUDGET_S:
                return True
            return False
        except Exception:
            return True

    def choose_action(self, frames, latest_frame) -> GameAction:
        try:
            if self._pending_action is not None:
                post_fp = _frame_fingerprint(latest_frame.frame)
                self.self_state.observe(
                    action_name=self._pending_action,
                    coords=self._pending_coords,
                    pre_fp=self._pre_fp,
                    post_fp=post_fp,
                    levels_before=self._pre_levels,
                    levels_after=latest_frame.levels_completed,
                    state_after=latest_frame.state.name,
                )
            if latest_frame.state is GameState.GAME_OVER:
                self.self_state.eps_spirit = None
                action_name, coords = "RESET", None
            else:
                available = _available_action_names(latest_frame)
                if not available:
                    action_name, coords = "RESET", None
                else:
                    frame_lists = _frame_to_lists(latest_frame.frame)
                    a_name, a_coords, _ = _llm_propose(
                        self.self_state, frame_lists, available, "exploit")
                    b_name, b_coords, _ = _llm_propose(
                        self.self_state, frame_lists, available, "explore")
                    if a_name == b_name and a_coords == b_coords:
                        action_name, coords = a_name, a_coords
                        self.self_state.chi_faith_history.append(True)
                    else:
                        action_name, coords = b_name, b_coords
                        self.self_state.chi_faith_history.append(False)
            action = self._build_action(action_name, coords)
            self._pending_action = action_name
            self._pending_coords = coords
            self._pre_fp = _frame_fingerprint(latest_frame.frame)
            self._pre_levels = latest_frame.levels_completed
            return action
        except Exception:
            try:
                avail = _available_action_names(latest_frame)
                fallback_name = avail[0] if avail else "RESET"
            except Exception:
                fallback_name = "RESET"
            return _ACTION_BY_NAME.get(fallback_name, GameAction.RESET)

    def _build_action(self, name: str, coords: Optional[tuple[int, int]]) -> GameAction:
        ga = _ACTION_BY_NAME.get(name, GameAction.RESET)
        if name == "ACTION6" and coords is not None:
            x = max(0, min(63, int(coords[0])))
            y = max(0, min(63, int(coords[1])))
            try:
                ga.action_data.x = x
                ga.action_data.y = y
            except Exception:
                pass
        return ga
