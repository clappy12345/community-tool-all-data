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
        "The skating feels so much smoother this year, huge improvement over last year",
        "Why is Be A Pro still so bare bones? They promised changes",
        "EASHL is the best mode in the game hands down, love playing with my squad",
        "Franchise mode scouting update is exactly what we needed",
        "Cross-play is amazing, finally can play with my Xbox friends on PS5",
        "Goalies are still broken, they let in the same weak goals every game",
        "HUT is pay to win as always, nothing new there",
        "The new deking system takes time to learn but it's so rewarding",
        "Best NHL game in years, the Frostbite engine makes everything look incredible",
        "Can we please get more celebration options? The current ones are stale",
        "Board play physics are insane, you actually feel the hits now",
        "Why does my BAP player feel so slow even at 95 speed?",
        "The crowd noise and atmosphere is unreal, feels like a real broadcast",
        "Penalty system is much better, no more phantom tripping calls",
        "Still waiting for that GM Connected mode, come on EA",
        "World of Chel customization this year is top tier",
        "Servers have been laggy all week, please fix this EA",
        "Just pulled a 99 McDavid in HUT, best day ever!",
        "Franchise mode trade logic is still terrible, AI offers garbage deals",
        "The passing in this game is so crisp, love the new mechanics",
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

    pp = _generate_post_performance(rng, date_range, posts)
    prof = _generate_profile_performance(rng, date_range)
    aff = _generate_affogata(rng, date_range, community)
    inbox = _generate_inbox(rng, date_range, inbox_msgs)
    looker = _generate_looker_sentiment(rng, date_range)

    return {
        "post_performance": pp,
        "profile_performance": prof,
        "affogata": aff,
        "inbox": inbox,
        "looker_sentiment": looker,
    }


def generate_sample_comparison_data(title_key="NHL"):
    """Generate sample data for an earlier period (for Compare Periods)."""
    rng = np.random.default_rng(99)
    start = pd.Timestamp("2025-07-24")
    end = pd.Timestamp("2025-08-20")
    date_range = pd.date_range(start, end)

    posts = TITLE_POSTS.get(title_key, TITLE_POSTS["NHL"])
    community = TITLE_COMMUNITY.get(title_key, TITLE_COMMUNITY["NHL"])
    inbox_msgs = TITLE_INBOX.get(title_key, TITLE_INBOX["NHL"])

    pp = _generate_post_performance(rng, date_range, posts)
    prof = _generate_profile_performance(rng, date_range)
    aff = _generate_affogata(rng, date_range, community)
    inbox = _generate_inbox(rng, date_range, inbox_msgs)
    looker = _generate_looker_sentiment(rng, date_range)

    return {
        "post_performance": pp,
        "profile_performance": prof,
        "affogata": aff,
        "inbox": inbox,
        "looker_sentiment": looker,
    }


def _generate_post_performance(rng, date_range, posts):
    rows = []
    for date in date_range:
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
        n_msgs = rng.integers(30, 80)
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
        n_msgs = rng.integers(10, 35)
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
