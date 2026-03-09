import pandas as pd
import numpy as np

NETWORKS = ["X", "Facebook", "Instagram", "TikTok", "YouTube"]
CONTENT_TYPES = ["Photo", "Video", "Carousel", "Text", "Reel"]
POST_TYPES = ["Post", "Post", "Post", "Post", "Story", "Reel"]
SENTIMENTS = ["positive", "negative", "neutral"]
AFF_NETWORKS = ["Reddit", "X", "YouTube", "TikTok", "Instagram", "Facebook"]

# ── Per-title sample text ──────────────────────────────────────────

TITLE_POSTS = {
    "NHL": [
        "NHL 26 is officially HERE. Lace up and hit the ice. Who's ready? #NHL26",
        "The new skating engine in NHL 26 feels incredible. Every stride matters.",
        "Check out the top 10 goals of the week in #NHL26! Which is your favorite?",
        "EASHL is back and better than ever. Squad up tonight.",
        "Behind the scenes: how we built the new Frostbite arenas in NHL 26.",
        "New World of Chel drip just dropped. Show us your best fits.",
        "Patch notes are live! Improved AI defense and goalie reactions. Details below.",
        "The crowd atmosphere in NHL 26 is unmatched. Listen to that roar.",
        "HUT Team of the Week is here! Who made your squad?",
        "Be A Pro mode finally feels like a real career journey.",
        "Connor McDavid's speed in NHL 26 is INSANE. Real Player Motion at its best.",
        "Show us your nastiest dekes with the new skill stick controls.",
        "First look at the Winter Classic outdoor arena. Absolutely beautiful.",
        "Franchise mode deep dive: new scouting overhaul and draft day trades.",
        "This community is incredible. 1M games played in the first 48 hours!",
        "New celebration animations are hilarious. The celly game is strong.",
        "Goalie mode improvements: butterfly slides and desperation saves feel so real.",
        "Tips & tricks: how to master the new passing system in NHL 26.",
        "Community tournament this weekend! Sign up link in bio.",
        "The soundtrack this year is absolute fire. Perfect vibes for game day.",
        "Rivalry games hit different in NHL 26. The intensity is turned up.",
        "Thank you for 500K followers! Giveaway time — RT for a chance to win.",
        "Updated rosters are live. All the latest trades and callups reflected.",
        "Cross-play is finally here! Play with friends on any platform.",
        "The physics on board play are next level this year.",
        "Pro-Am mode lets you team up with NHL legends. Who's your pick?",
        "New penalty system makes the game feel way more realistic.",
    ],
    "UFC": [
        "UFC 6 is HERE. Step into the Octagon. Who's fighting first? #UFC6",
        "The new grappling system in UFC 6 is a game changer. Ground game evolved.",
        "Top 10 KOs of the week in #UFC6! Which one had you jumping off the couch?",
        "Online World Championships are live. Prove you're the best pound-for-pound.",
        "Behind the scenes: motion capture with real UFC fighters for UFC 6.",
        "New fighter customization just dropped. Create your ultimate fighter.",
        "Patch notes are live! Improved submission system and clinch transitions.",
        "The walkout presentation in UFC 6 is unmatched. Feel the energy.",
        "Ultimate Team Fighter of the Week! Who made your squad?",
        "Career mode finally feels like a real journey to the belt.",
        "Alex Pereira's power in UFC 6 is TERRIFYING. Every punch feels lethal.",
        "Show us your best knockouts with the new striking mechanics.",
        "First look at the new Fight Island arena. Incredible atmosphere.",
        "Career mode deep dive: new training camps and rivalry storylines.",
        "This community is incredible. 2M fights in the first 48 hours!",
        "New celebration animations after KOs are absolutely savage.",
        "Clinch and takedown defense improvements feel so much more realistic.",
        "Tips & tricks: how to master the new submission mini-game in UFC 6.",
        "Community tournament this weekend! Sign up link in bio.",
        "The soundtrack this year hits different. Perfect walkout vibes.",
        "Rivalry fights hit different in UFC 6. The bad blood is real.",
        "Thank you for 500K followers! Giveaway time — RT for a chance to win.",
        "Updated rosters are live. All the latest signings and rankings reflected.",
        "Cross-play is finally here! Fight friends on any platform.",
        "The physics on ground-and-pound are next level this year.",
        "Legends mode lets you play as UFC Hall of Famers. Who's your pick?",
        "New referee system makes stoppages feel way more realistic.",
    ],
    "F1": [
        "F1 26 is HERE. Lights out and away we go! Who's racing first? #F126",
        "The new tire model in F1 26 feels incredible. Every compound matters.",
        "Top 10 overtakes of the week in #F126! Which one is your favorite?",
        "Online Championships are live. Prove you're the fastest on the grid.",
        "Behind the scenes: laser-scanned circuits bring every track to life in F1 26.",
        "New livery editor just dropped. Show us your best team designs.",
        "Patch notes are live! Improved AI racecraft and wet weather physics.",
        "The race day atmosphere in F1 26 is unmatched. Hear those engines roar.",
        "My Team driver market update! Who did you sign for Season 2?",
        "Career mode finally feels like a real journey to the championship.",
        "Max Verstappen's pace in F1 26 is UNREAL. Simulated perfection.",
        "Show us your best lap times at Spa with the new handling model.",
        "First look at the new Las Vegas night race. Absolutely stunning.",
        "My Team deep dive: new sponsor system and facility upgrades.",
        "This community is incredible. 5M laps completed in the first 48 hours!",
        "New podium celebrations and team radio lines are fantastic.",
        "Wet weather racing improvements — aquaplaning and spray effects are so real.",
        "Tips & tricks: how to master the new ERS deployment strategy in F1 26.",
        "Community time trial this weekend! Fastest lap wins. Link in bio.",
        "The soundtrack this year is absolute fire. Perfect pre-race vibes.",
        "Rivalry battles hit different in F1 26. Wheel-to-wheel intensity.",
        "Thank you for 500K followers! Giveaway time — RT for a chance to win.",
        "Updated driver lineups are live. All the latest transfers reflected.",
        "Cross-play is finally here! Race friends on any platform.",
        "The physics on curb riding are next level this year.",
        "Legends mode lets you drive iconic F1 cars. Which era is your pick?",
        "New penalty system and stewards make racing feel way more realistic.",
    ],
}

TITLE_COMMUNITY = {
    "NHL": [
        # Skating / Movement
        "The skating feels so much smoother this year, huge improvement over last year",
        "Edge work and pivots feel incredible, the skating engine is a game changer",
        "Player acceleration is way better, you can actually feel the speed difference between 85 and 95",
        "The stride animations are gorgeous, every skate push looks realistic now",
        "Momentum matters so much more this year, no more instant direction changes",
        "Agility feels so much more responsive, the skating is finally where it needs to be",
        # Goalies
        "Goalies are still broken, they let in the same weak goals every game",
        "The butterfly saves look incredible this year, goaltending is so much better",
        "Goalie movement side to side feels way more realistic, blocker saves are crisp",
        "My goaltender keeps letting in five hole goals, is this a known glove issue?",
        "Finally the saves feel realistic, goalies actually track the puck properly now",
        "Goalie desperation saves are insane, butterfly slides across the crease are chef's kiss",
        # Pokechecks / Stick Play
        "The poke check is way too OP, every game is just spam pokecheck city",
        "Stick lift timing is perfect now, stick play actually requires skill",
        "Poke checking feels balanced, not like the tripping fest it was in 25",
        "Stick check spam is still an issue, half my penalties are from slash calls",
        "Love the new poke check risk/reward, stick play matters more than ever",
        "The stick lift mechanic finally feels fair, no more phantom tripping calls",
        # Hitting / Physicality
        "Body checks along the boards are BRUTAL this year, the hitting feels so satisfying",
        "The hip check animation is hilarious, big hit physics are insane",
        "Fighting is actually fun again, the new fight engine is great",
        "Board play and body checking feel way more impactful, hitting is finally rewarding",
        "The boarding penalties are too strict, every hit near the boards is a call now",
        "Love how physical this game feels, every bodycheck has real weight behind it",
        # HUT / Ultimate Team
        "HUT is pay to win as always, nothing new there",
        "Just pulled a 99 McDavid in HUT, best day ever!",
        "Pack odds in Ultimate Team are terrible, spent 200k coins and got nothing",
        "HUT Rivals rewards are much better this year, rivals is actually worth grinding",
        "Squad Battles difficulty is all over the place, one game easy next game impossible",
        "The HUT auction house prices are insane right now, MSP cards going for millions",
        "Champions in HUT is way too sweaty, rush mode is more fun for casual players",
        "New HUT lineup building is addicting, love the team chemistry system",
        # EASHL / Online Modes
        "EASHL is the best mode in the game hands down, love playing with my squad",
        "World of Chel customization this year is top tier",
        "Club games in EASHL are so much fun, the matchmaking is actually decent now",
        "Drop-in games are toxic as always, need a better ranked system for Chel",
        "EASHL needs more unlockables, World of Chel gets stale after a few weeks",
        "The online versus mode is finally stable, matchmaking finds games fast",
        # Be A Pro / Franchise
        "Why is Be A Pro still so bare bones? They promised changes",
        "Franchise mode scouting update is exactly what we needed",
        "Why does my BAP player feel so slow even at 95 speed?",
        "Franchise mode trade logic is still terrible, AI offers garbage deals",
        "Be A Pro story mode is too short, needs way more content and draft scenarios",
        "The scouting overhaul in franchise mode is amazing, draft day feels realistic",
        "BAP interviews and media stuff is cool but gets repetitive by season 2",
        "Franchise simulation engine is so much better, trades actually make sense now",
        # Servers / Performance
        "Servers have been laggy all week, please fix this EA",
        "The input delay online is awful, every game feels like I'm on a half-second lag",
        "Game crashed three times today during HUT Champs, lost all my progress",
        "Server disconnects mid-game should not count as a loss, this is ridiculous",
        "FPS drops on PS5 during big scrums in front of the net, frame rate tanks",
        "Latency in online games makes the game unplayable some nights, fix your servers",
        "Desync issues are ruining ranked games, both players see different things",
        # Graphics / Presentation
        "The crowd noise and atmosphere is unreal, feels like a real broadcast",
        "Best NHL game in years, the Frostbite engine makes everything look incredible",
        "The arena atmospheres are so detailed, every NHL arena feels unique",
        "Commentary is much improved but still repetitive by week two",
        "Jersey physics and ice reflections look stunning, the visuals are next level",
        "The replay angles and cutscenes between periods are a nice touch",
        "Graphics on the ice surface deterioration throughout the game are beautiful",
        "Presentation package feels like a real NBC/ESPN broadcast now",
        # AI / CPU Behavior
        "CPU teammate AI is absolutely braindead, they just stand around in the D-zone",
        "Superstar difficulty is cheating, the AI makes perfect plays every time",
        "AI on All-Star is too easy now, but Superstar is too hard, need something between",
        "The computer players never backcheck, teammate AI needs a serious fix",
        "CPU difficulty sliders help but shouldn't be needed to make the AI fair",
        "AI defenders finally pinch at the right times, the CPU behavior is way smarter",
        # General / Cross-topic
        "Cross-play is amazing, finally can play with my Xbox friends on PS5",
        "The new deking system takes time to learn but it's so rewarding",
        "Can we please get more celebration options? The current ones are stale",
        "Still waiting for that GM Connected mode, come on EA",
        "The passing in this game is so crisp, love the new mechanics",
        "This is the best hockey game in a decade, everything just clicks",
        "The soundtrack is fire, love the playlist they picked for this year",
        "Cross-gen version should not exist, it's holding the game back",
        "Why do my settings keep resetting every time I boot the game?",
        "Loving the new faceoff system, feels way more strategic and skill-based",
    ],
    "UFC": [
        "The striking feels so much more fluid this year, huge improvement",
        "Why is Career mode still so short? They promised a deeper experience",
        "Online Championships are the best mode, love competing against real fighters",
        "Ground game overhaul is exactly what we needed for realistic grappling",
        "Cross-play is amazing, finally can fight my Xbox friends on PS5",
        "Submissions are still broken, they need to rework the mini-game",
        "Ultimate Team is pay to win as always, nothing new there",
        "The new clinch system takes time to learn but it's so rewarding",
        "Best UFC game in years, the fighter models look incredibly realistic",
        "Can we please get more taunts and celebrations after KOs?",
        "Ground-and-pound physics are insane, you actually feel the impact",
        "Why does my CAF feel so underpowered even at max stats?",
        "The crowd noise and commentary is unreal, feels like a real PPV event",
        "Referee stoppages are much better, no more early stoppages on standing fighters",
        "Still waiting for a proper tournament mode, come on EA",
        "Fighter customization this year is top tier, love the new gear options",
        "Servers have been laggy all week, please fix this EA",
        "Just got a 5-star fighter in Ultimate Team, best pull ever!",
        "Career mode matchmaking is still terrible, fighting top 5 guys as a rookie",
        "The striking combos in this game are so crisp, love the new flow",
    ],
    "F1": [
        "The handling feels so much more realistic this year, huge improvement",
        "Why is My Team still missing features? They promised deeper management",
        "Online Championships are the best mode, love racing clean against real drivers",
        "Tire model overhaul is exactly what we needed for realistic strategy",
        "Cross-play is amazing, finally can race my Xbox friends on PS5",
        "AI racecraft is still broken, they dive-bomb into every corner",
        "My Team economy is unbalanced, sponsors pay too little early on",
        "The new ERS system takes time to learn but it's so rewarding when you nail it",
        "Best F1 game in years, the Frostbite engine makes the tracks look incredible",
        "Can we please get more team radio options and engineer interactions?",
        "Curb physics are insane, you actually feel every bump on the kerbs",
        "Why does my car feel so slow even with max upgrades in My Team?",
        "The race day atmosphere is unreal, feels like a real broadcast",
        "Penalty system is much better, no more 5-second penalties for racing incidents",
        "Still waiting for a proper classic cars expansion, come on EA",
        "Livery editor this year is top tier, the designs people are making are wild",
        "Servers have been laggy all week, please fix this EA",
        "Just won the championship in My Team season 3, best feeling ever!",
        "AI difficulty scaling is still inconsistent, some tracks are way harder than others",
        "The braking points and turn-in feel so realistic, love the new physics",
    ],
}

TITLE_INBOX = {
    "NHL": [
        "Love the new game! Been playing non-stop since launch",
        "When are you fixing the goalie issues? They're ruining online play",
        "Can you add more customization to World of Chel?",
        "Best NHL game ever made, the skating is incredible",
        "My game keeps crashing on PS5, any fix coming?",
        "Please bring back GM Connected, we've been asking for years",
        "The Be A Pro story mode is too short, needs more content",
        "Loving the cross-play feature, great addition this year",
        "HUT rewards are too stingy, need better pack odds",
        "The EASHL matchmaking is broken, always getting matched against stacked teams",
        "Incredible game, the Frostbite engine really shines",
        "Franchise mode is finally worth playing again with the new scouting",
        "The soundtrack is fire this year, great song choices",
        "Servers need improvement, too much lag in competitive modes",
        "Great job on the arena atmospheres, they feel so alive",
        "The poke check spam online is unbearable, every game is just stick check after stick check",
        "Goaltending AI is terrible, my goalie just watches five hole shots go in",
        "Body checking feels amazing this year, the hitting is so satisfying",
        "Butterfly saves and blocker reactions are actually realistic now, goalies feel right",
        "The CPU AI is so dumb on defense, teammate AI never covers the passing lanes",
        "Pack pulls in HUT are rigged, opened 50 packs and best was an 84 overall",
        "EASHL drop-in is a mess, randoms just chase the puck and never pass",
        "Franchise mode trade deadline is exciting with the new scouting system",
        "Input delay and latency make online games unplayable, fix the servers",
        "The commentary and crowd atmosphere during playoff games is incredible",
        "Speed and acceleration feel much more realistic, skating engine is elite",
        "Superstar difficulty is broken, the AI makes impossible plays every shift",
        "FPS drops during fights and scrums need to be patched ASAP",
        "The ice surface graphics and arena details are absolutely gorgeous",
        "Can you nerf the poke check already? Tripping penalties mean nothing when you spam it",
        "HUT Squad Battles rewards need a serious buff, not worth the grind",
        "The edge work in tight spaces is so smooth, pivot skating feels natural",
        "Franchise mode draft class quality is way better this year",
        "World of Chel ranked matchmaking should factor in club skill, not just record",
        "Please fix the desync issues in online versus, happens every other game",
    ],
    "UFC": [
        "Love the new game! Been fighting non-stop since launch",
        "When are you fixing the submission system? It's way too hard to escape",
        "Can you add more fighter customization options?",
        "Best UFC game ever made, the striking is incredible",
        "My game keeps crashing on PS5, any fix coming?",
        "Please add a tournament bracket mode, we've been asking for years",
        "Career mode story is too short, needs more content and rivalries",
        "Loving the cross-play feature, great addition this year",
        "Ultimate Team rewards are too stingy, need better pack odds",
        "Online matchmaking is broken, always getting matched against maxed-out fighters",
        "Incredible game, the fighter models look so real",
        "Ground game is finally worth learning with the new grappling overhaul",
        "The soundtrack is fire this year, great walkout music options",
        "Servers need improvement, too much lag in ranked fights",
        "Great job on the Octagon atmosphere, feels like a real UFC event",
    ],
    "F1": [
        "Love the new game! Been racing non-stop since launch",
        "When are you fixing the AI dive-bombs? They ruin every first corner",
        "Can you add more livery customization layers?",
        "Best F1 game ever made, the handling is incredible",
        "My game keeps crashing on PS5, any fix coming?",
        "Please add classic seasons mode, we've been asking for years",
        "My Team story is too short, needs more drama and rivalries",
        "Loving the cross-play feature, great addition this year",
        "Pitcoin prices are too high for what you get, needs adjustment",
        "Online lobbies are broken, always getting punted off at turn 1",
        "Incredible game, the Frostbite engine makes every track stunning",
        "Tire strategy finally matters with the new degradation model",
        "The soundtrack is fire this year, perfect pre-race vibes",
        "Servers need improvement, too much lag in league races",
        "Great job on the race atmospheres, night races are breathtaking",
    ],
}


def generate_sample_data(title_key="NHL"):
    rng = np.random.default_rng(42)
    start = pd.Timestamp("2025-08-21")
    end = pd.Timestamp("2025-09-17")
    date_range = pd.date_range(start, end)

    posts = TITLE_POSTS.get(title_key, TITLE_POSTS["NHL"])
    community = TITLE_COMMUNITY.get(title_key, TITLE_COMMUNITY["NHL"])
    inbox_msgs = TITLE_INBOX.get(title_key, TITLE_INBOX["NHL"])

    pp = _generate_post_performance(rng, date_range, posts, title_key=title_key)
    prof = _generate_profile_performance(rng, date_range)
    aff = _generate_affogata(rng, date_range, community)
    inbox = _generate_inbox(rng, date_range, inbox_msgs)
    looker = _generate_looker_sentiment(rng, date_range)

    title_events = _SAMPLE_CAMPAIGN_EVENTS.get(title_key, _SAMPLE_CAMPAIGN_EVENTS["NHL"])
    import streamlit as st
    st.session_state["campaign_events_draft"] = list(title_events.get("current", []))

    return {
        "post_performance": pp,
        "profile_performance": prof,
        "affogata": aff,
        "inbox": inbox,
        "looker_sentiment": looker,
    }


_SAMPLE_CAMPAIGN_EVENTS = {
    "NHL": {
        "full_season": [
            {"name": "Cover Reveal", "date": "2024-06-10", "color": "#FF6B6B"},
            {"name": "Gameplay Trailer", "date": "2024-08-05", "color": "#4ECDC4"},
            {"name": "Beta Start", "date": "2024-09-12", "color": "#FFE66D"},
            {"name": "Early Access", "date": "2024-10-01", "color": "#95E1D3"},
            {"name": "Launch Day", "date": "2024-10-04", "color": "#F38181"},
            {"name": "First Patch", "date": "2024-10-18", "color": "#AA96DA"},
        ],
        "cover_reveal": [
            {"name": "Cover Reveal", "date": "2024-06-10", "color": "#FF6B6B"},
            {"name": "Trailer Drop", "date": "2024-06-12", "color": "#4ECDC4"},
        ],
        "launch_week": [
            {"name": "Early Access", "date": "2024-10-01", "color": "#95E1D3"},
            {"name": "Launch Day", "date": "2024-10-04", "color": "#F38181"},
            {"name": "Day 1 Patch", "date": "2024-10-05", "color": "#AA96DA"},
        ],
        "current": [
            {"name": "Cover Reveal", "date": "2025-08-21", "color": "#FF6B6B"},
            {"name": "Gameplay Deep Dive", "date": "2025-08-28", "color": "#4ECDC4"},
            {"name": "Beta Announcement", "date": "2025-09-04", "color": "#FFE66D"},
        ],
    },
    "UFC": {
        "full_season": [
            {"name": "Reveal Trailer", "date": "2024-06-10", "color": "#FF6B6B"},
            {"name": "Gameplay Trailer", "date": "2024-08-05", "color": "#4ECDC4"},
            {"name": "Early Access", "date": "2024-10-01", "color": "#95E1D3"},
            {"name": "Launch Day", "date": "2024-10-04", "color": "#F38181"},
        ],
        "cover_reveal": [
            {"name": "Reveal Trailer", "date": "2024-06-10", "color": "#FF6B6B"},
        ],
        "launch_week": [
            {"name": "Launch Day", "date": "2024-10-04", "color": "#F38181"},
        ],
        "current": [
            {"name": "Reveal Trailer", "date": "2025-08-21", "color": "#FF6B6B"},
        ],
    },
    "F1": {
        "full_season": [
            {"name": "Reveal Trailer", "date": "2024-06-10", "color": "#FF6B6B"},
            {"name": "Gameplay Trailer", "date": "2024-08-05", "color": "#4ECDC4"},
            {"name": "Early Access", "date": "2024-10-01", "color": "#95E1D3"},
            {"name": "Launch Day", "date": "2024-10-04", "color": "#F38181"},
        ],
        "cover_reveal": [
            {"name": "Reveal Trailer", "date": "2024-06-10", "color": "#FF6B6B"},
        ],
        "launch_week": [
            {"name": "Launch Day", "date": "2024-10-04", "color": "#F38181"},
        ],
        "current": [
            {"name": "Reveal Trailer", "date": "2025-08-21", "color": "#FF6B6B"},
        ],
    },
}


def generate_sample_saved_campaigns(title_key="NHL"):
    """Create saved campaign datasets for the given title to enable campaign comparison."""
    from utils.data_store import _dataset_dir
    import json

    title_events = _SAMPLE_CAMPAIGN_EVENTS.get(title_key, _SAMPLE_CAMPAIGN_EVENTS["NHL"])

    campaigns = [
        {
            "label": f"{title_key} 25 Full Season",
            "seed": 55,
            "start": pd.Timestamp("2024-08-16"),
            "end": pd.Timestamp("2025-08-16"),
            "campaign_start": "2024-10-04",
            "game_version": f"{title_key} 25",
            "campaign_type": "Full Season",
            "campaign_events": title_events["full_season"],
        },
        {
            "label": f"{title_key} 25 Cover Reveal",
            "seed": 77,
            "start": pd.Timestamp("2024-06-10"),
            "end": pd.Timestamp("2024-06-24"),
            "campaign_start": "2024-06-10",
            "game_version": f"{title_key} 25",
            "campaign_type": "Cover Reveal",
            "campaign_events": title_events["cover_reveal"],
        },
        {
            "label": f"{title_key} 25 Launch Week",
            "seed": 88,
            "start": pd.Timestamp("2024-10-04"),
            "end": pd.Timestamp("2024-10-18"),
            "campaign_start": "2024-10-04",
            "game_version": f"{title_key} 25",
            "campaign_type": "Launch Week",
            "campaign_events": title_events["launch_week"],
        },
    ]

    posts = TITLE_POSTS.get(title_key, TITLE_POSTS["NHL"])
    community = TITLE_COMMUNITY.get(title_key, TITLE_COMMUNITY["NHL"])
    inbox_msgs = TITLE_INBOX.get(title_key, TITLE_INBOX["NHL"])

    for camp in campaigns:
        rng = np.random.default_rng(camp["seed"])
        dr = pd.date_range(camp["start"], camp["end"])
        data = {
            "post_performance": _generate_post_performance(rng, dr, posts, title_key=title_key),
            "profile_performance": _generate_profile_performance(rng, dr),
            "affogata": _generate_affogata(rng, dr, community),
            "inbox": _generate_inbox(rng, dr, inbox_msgs),
            "looker_sentiment": _generate_looker_sentiment(rng, dr),
        }

        dest = _dataset_dir(title_key, camp["label"])
        dest.mkdir(parents=True, exist_ok=True)
        row_counts = {}
        for key, df in data.items():
            if df is not None and len(df) > 0:
                df.to_parquet(dest / f"{key}.parquet", index=False)
                row_counts[key] = len(df)

        manifest = {
            "title": title_key,
            "label": camp["label"],
            "date_range": [camp["start"].strftime("%Y-%m-%d"), camp["end"].strftime("%Y-%m-%d")],
            "campaign_start": camp["campaign_start"],
            "campaign_events": camp.get("campaign_events", []),
            "game_version": camp.get("game_version"),
            "campaign_type": camp.get("campaign_type"),
            "saved_at": pd.Timestamp.now().isoformat(),
            "row_counts": row_counts,
        }
        with open(dest / "manifest.json", "w") as f:
            json.dump(manifest, f, indent=2)


def generate_sample_comparison_data(title_key="NHL"):
    """Generate sample data for an earlier period (for Compare Periods).

    Also sets ``compare_campaign_events`` in session state so event markers
    appear on comparison charts.
    """
    import streamlit as st

    rng = np.random.default_rng(99)
    start = pd.Timestamp("2025-07-24")
    end = pd.Timestamp("2025-08-20")
    date_range = pd.date_range(start, end)

    posts = TITLE_POSTS.get(title_key, TITLE_POSTS["NHL"])
    community = TITLE_COMMUNITY.get(title_key, TITLE_COMMUNITY["NHL"])
    inbox_msgs = TITLE_INBOX.get(title_key, TITLE_INBOX["NHL"])

    pp = _generate_post_performance(rng, date_range, posts, title_key=title_key)
    prof = _generate_profile_performance(rng, date_range)
    aff = _generate_affogata(rng, date_range, community)
    inbox = _generate_inbox(rng, date_range, inbox_msgs)
    looker = _generate_looker_sentiment(rng, date_range)

    title_events = _SAMPLE_CAMPAIGN_EVENTS.get(title_key, _SAMPLE_CAMPAIGN_EVENTS["NHL"])
    comparison_events = [
        {"name": "Reveal Trailer", "date": "2025-07-24", "color": "#FF6B6B"},
        {"name": "Gameplay Deep Dive", "date": "2025-08-01", "color": "#4ECDC4"},
        {"name": "Beta Announcement", "date": "2025-08-10", "color": "#FFE66D"},
    ]
    st.session_state["compare_campaign_events"] = comparison_events

    return {
        "post_performance": pp,
        "profile_performance": prof,
        "affogata": aff,
        "inbox": inbox,
        "looker_sentiment": looker,
    }


_CROSS_CHANNEL_POSTS = {
    "NHL": [
        (0, ["X", "YouTube", "Instagram", "TikTok"], "NHL 26 is officially HERE. Lace up and hit the ice. Who's ready? #NHL26"),
        (3, ["X", "Instagram", "Facebook"], "The new skating engine in NHL 26 feels incredible. Every stride matters."),
        (5, ["YouTube", "TikTok", "Instagram"], "Check out the top 10 goals of the week in #NHL26! Which is your favorite?"),
        (8, ["X", "Facebook", "Instagram", "YouTube"], "Behind the scenes: how we built the new Frostbite arenas in NHL 26."),
        (10, ["X", "TikTok", "YouTube"], "Connor McDavid's speed in NHL 26 is INSANE. Real Player Motion at its best."),
        (14, ["X", "YouTube", "Instagram"], "Cross-play is finally here! Play with friends on any platform."),
        (18, ["Instagram", "TikTok", "Facebook"], "Show us your nastiest dekes with the new skill stick controls."),
        (22, ["X", "YouTube", "Facebook", "Instagram", "TikTok"], "This community is incredible. 1M games played in the first 48 hours!"),
    ],
    "UFC": [
        (0, ["X", "YouTube", "Instagram", "TikTok"], "UFC 6 is HERE. Step into the Octagon. Who's fighting first? #UFC6"),
        (3, ["X", "Instagram", "Facebook"], "The new grappling system in UFC 6 is a game changer. Ground game evolved."),
        (5, ["YouTube", "TikTok", "Instagram"], "Top 10 KOs of the week in #UFC6! Which one had you jumping off the couch?"),
        (8, ["X", "Facebook", "Instagram", "YouTube"], "Behind the scenes: motion capture with real UFC fighters for UFC 6."),
        (10, ["X", "TikTok", "YouTube"], "Alex Pereira's power in UFC 6 is TERRIFYING. Every punch feels lethal."),
        (14, ["X", "YouTube", "Instagram"], "Cross-play is finally here! Fight friends on any platform."),
        (18, ["Instagram", "TikTok", "Facebook"], "Show us your best knockouts with the new striking mechanics."),
        (22, ["X", "YouTube", "Facebook", "Instagram", "TikTok"], "This community is incredible. 2M fights in the first 48 hours!"),
    ],
    "F1": [
        (0, ["X", "YouTube", "Instagram", "TikTok"], "F1 26 is HERE. Lights out and away we go! Who's racing first? #F126"),
        (3, ["X", "Instagram", "Facebook"], "The new tire model in F1 26 feels incredible. Every compound matters."),
        (5, ["YouTube", "TikTok", "Instagram"], "Top 10 overtakes of the week in #F126! Which one is your favorite?"),
        (8, ["X", "Facebook", "Instagram", "YouTube"], "Behind the scenes: laser-scanned circuits bring every track to life in F1 26."),
        (10, ["X", "TikTok", "YouTube"], "Max Verstappen's pace in F1 26 is UNREAL. Simulated perfection."),
        (14, ["X", "YouTube", "Instagram"], "Cross-play is finally here! Race friends on any platform."),
        (18, ["Instagram", "TikTok", "Facebook"], "Show us your best lap times at Spa with the new handling model."),
        (22, ["X", "YouTube", "Facebook", "Instagram", "TikTok"], "This community is incredible. 5M laps completed in the first 48 hours!"),
    ],
}


def _generate_post_performance(rng, date_range, posts, title_key=None):
    rows = []
    start_date = date_range[0]

    cross_channel = _CROSS_CHANNEL_POSTS.get(title_key, []) if title_key else []
    cross_dates = {}
    for day_offset, networks, text in cross_channel:
        if day_offset < len(date_range):
            cross_dates.setdefault(day_offset, []).append((networks, text))

    for i, date in enumerate(date_range):
        n_posts = rng.integers(2, 7)
        for _ in range(n_posts):
            network = rng.choice(NETWORKS)
            impressions = int(rng.integers(5_000, 500_000))
            eng_base = impressions * rng.uniform(0.01, 0.08)
            engagements = int(eng_base)
            reactions = int(engagements * rng.uniform(0.4, 0.7))
            comments = int(engagements * rng.uniform(0.05, 0.2))
            shares = int(engagements * rng.uniform(0.05, 0.15))
            saves = int(engagements * rng.uniform(0.01, 0.05))
            clicks = int(engagements * rng.uniform(0.05, 0.1))
            video_views = int(impressions * rng.uniform(0.2, 0.6)) if rng.random() > 0.3 else 0

            rows.append({
                "Date": date,
                "Network": network,
                "Content Type": rng.choice(CONTENT_TYPES),
                "Post Type": rng.choice(POST_TYPES),
                "Post": rng.choice(posts),
                "Link": f"https://example.com/post/{rng.integers(10000, 99999)}",
                "Impressions": float(impressions),
                "Reach": float(int(impressions * rng.uniform(0.7, 0.95))),
                "Potential Reach": float(int(impressions * rng.uniform(1.2, 3.0))),
                "Engagements": float(engagements),
                "Reactions": float(reactions),
                "Comments": float(comments),
                "Shares": float(shares),
                "Saves": float(saves),
                "Post Link Clicks": float(clicks),
                "Video Views": float(video_views),
                "Engagement Rate (per Impression)": round(engagements / impressions * 100, 4),
            })

        if i in cross_dates:
            for networks, text in cross_dates[i]:
                for network in networks:
                    impressions = int(rng.integers(80_000, 500_000))
                    eng_base = impressions * rng.uniform(0.02, 0.08)
                    engagements = int(eng_base)
                    reactions = int(engagements * rng.uniform(0.4, 0.7))
                    comments = int(engagements * rng.uniform(0.05, 0.2))
                    shares = int(engagements * rng.uniform(0.05, 0.15))
                    saves = int(engagements * rng.uniform(0.01, 0.05))
                    clicks = int(engagements * rng.uniform(0.05, 0.1))
                    video_views = int(impressions * rng.uniform(0.2, 0.6)) if rng.random() > 0.3 else 0

                    rows.append({
                        "Date": date,
                        "Network": network,
                        "Content Type": rng.choice(CONTENT_TYPES),
                        "Post Type": "Post",
                        "Post": text,
                        "Link": f"https://example.com/post/{rng.integers(10000, 99999)}",
                        "Impressions": float(impressions),
                        "Reach": float(int(impressions * rng.uniform(0.7, 0.95))),
                        "Potential Reach": float(int(impressions * rng.uniform(1.2, 3.0))),
                        "Engagements": float(engagements),
                        "Reactions": float(reactions),
                        "Comments": float(comments),
                        "Shares": float(shares),
                        "Saves": float(saves),
                        "Post Link Clicks": float(clicks),
                        "Video Views": float(video_views),
                        "Engagement Rate (per Impression)": round(engagements / impressions * 100, 4),
                    })

    return pd.DataFrame(rows)


def _generate_profile_performance(rng, date_range):
    base_audiences = {"X": 820_000, "Facebook": 1_450_000, "Instagram": 2_100_000, "TikTok": 950_000, "YouTube": 1_700_000}
    rows = []
    cumulative_growth = {n: 0 for n in NETWORKS}

    for date in date_range:
        for network in NETWORKS:
            daily_growth = int(rng.integers(50, 600))
            cumulative_growth[network] += daily_growth
            audience = base_audiences[network] + cumulative_growth[network]
            impressions = int(rng.integers(100_000, 2_000_000))
            engagements = int(impressions * rng.uniform(0.01, 0.05))

            rows.append({
                "Date": date,
                "Network": network,
                "Audience": float(audience),
                "Net Audience Growth": float(daily_growth),
                "Audience Gained": float(int(daily_growth * rng.uniform(1.1, 1.4))),
                "Impressions": float(impressions),
                "Engagements": float(engagements),
                "Video Views": float(int(impressions * rng.uniform(0.1, 0.3))),
                "Reactions": float(int(engagements * rng.uniform(0.4, 0.6))),
                "Comments": float(int(engagements * rng.uniform(0.05, 0.15))),
                "Shares": float(int(engagements * rng.uniform(0.05, 0.12))),
                "Post Link Clicks": float(int(engagements * rng.uniform(0.02, 0.08))),
                "Saves": float(int(engagements * rng.uniform(0.01, 0.04))),
                "Engagement Rate (per Impression)": round(engagements / impressions * 100, 4),
            })

    return pd.DataFrame(rows)


def _generate_affogata(rng, date_range, community_messages):
    rows = []
    weights = [0.35, 0.20, 0.45]

    for date in date_range:
        n_msgs = rng.integers(60, 150)
        for _ in range(n_msgs):
            hour = rng.integers(0, 24)
            minute = rng.integers(0, 60)
            ts = date + pd.Timedelta(hours=int(hour), minutes=int(minute))
            sentiment = rng.choice(SENTIMENTS, p=weights)
            network = rng.choice(AFF_NETWORKS)
            likes = int(rng.integers(0, 200))
            shares_val = int(rng.integers(0, 50))
            comments_val = int(rng.integers(0, 30))
            views = int(rng.integers(50, 5000))

            rows.append({
                "Created At": ts,
                "Network Name": network,
                "Interaction Type": rng.choice(["reply", "reply", "reply", "quote", "quote", "post", "private"], p=[0.3, 0.15, 0.12, 0.15, 0.13, 0.1, 0.05]),
                "Text": rng.choice(community_messages),
                "Sentiment": sentiment,
                "Likes": float(likes),
                "Shares": float(shares_val),
                "Comments": float(comments_val),
                "Views": float(views),
                "Total Engagements": float(likes + shares_val + comments_val),
                "Reach": float(int(views * rng.uniform(1.5, 4.0))),
                "URL": f"https://example.com/community/{rng.integers(10000, 99999)}",
            })

    return pd.DataFrame(rows)


def _generate_looker_sentiment(rng, date_range):
    scores = 5.0 + rng.normal(0, 0.5, size=len(date_range))
    scores = scores.clip(3.0, 6.5).round(1)
    return pd.DataFrame({"Date": date_range, "Impact Score": scores})


def _generate_inbox(rng, date_range, inbox_messages):
    rows = []
    weights = [0.30, 0.25, 0.45]

    for date in date_range:
        n_msgs = rng.integers(25, 65)
        for _ in range(n_msgs):
            hour = rng.integers(0, 24)
            minute = rng.integers(0, 60)
            ts = date + pd.Timedelta(hours=int(hour), minutes=int(minute))

            rows.append({
                "Timestamp": ts,
                "Network": rng.choice(NETWORKS),
                "Message Type": rng.choice(["Comment", "Direct Message", "Mention", "Reply"]),
                "Message": rng.choice(inbox_messages),
                "Sentiment": rng.choice(SENTIMENTS, p=weights),
                "Message Intent": rng.choice(
                    ["unclassified", "unclassified", "unclassified", "unclassified",
                     "customer love", "customer support request", "high brand risk"],
                    p=[0.40, 0.25, 0.15, 0.07, 0.06, 0.04, 0.03],
                ),
                "Language": "English",
            })

    return pd.DataFrame(rows)
